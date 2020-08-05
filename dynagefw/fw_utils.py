import os
from pathlib import Path
import pandas as pd
import flywheel
from flywheel_bids import upload_bids

from .utils import get_info_dict, flatten_dict, compare_info_dicts, nest_dict, \
    prepare_info_dict, clean_nan, \
    load_tabular_file
from .fw_bids_utils import handle_project, get_subject_session
import logging

logger = logging.getLogger("dynagefw")


# TODO write tests

def get_flat_info(fw, project_id, subject_name, session_name, level):
    """
    creates a session if it does not exist
    """
    session = upload_bids.handle_session(fw, project_id, session_name,
                                         subject_name)
    info_nested = get_info_dict(level, fw.get_session(session["id"]))
    info_flat = flatten_dict(info_nested)
    return info_flat


def upload_info(fw, project_id, subject_name, session_name, level, info_flat,
                update_values=False):
    """
    uploads info_flat (e.g., {"age": 33, "c.a1": "x",  "c.a2": "y"}) into db
    level: upload to "subject" or "session"
    update_vals: if False, will not overwrite values that are already in db with new values
    """

    # check that already existing db values are not overwritten
    current_info_flat = get_flat_info(fw, project_id, subject_name,
                                      session_name, level)
    diff, new = compare_info_dicts(current_info_flat, clean_nan(info_flat))
    if diff and not update_values:
        raise Exception(
            "update_values is False but you want to upload changed values {} {} {} {}" \
                .format(subject_name, session_name, level, diff))

    # only upload new values
    if new or diff:
        upload_keys = new + diff
        info_flat_upload = {k: info_flat[k] for k in upload_keys}

        logger.info("New or changed values found for {} {}. "
                    "Uploading. {}".format(subject_name, session_name,
                                           info_flat_upload))
        logger.debug("{}".format(info_flat_upload))

        info_flat_upload = clean_nan(
            info_flat_upload)  # replace np.nan with "", otherwise the db won't take them
        info_nested = nest_dict(info_flat_upload)
        info = prepare_info_dict(level, info_nested)
        session = upload_bids.handle_session(fw, project_id, session_name,
                                             subject_name)
        fw.modify_session(session["id"], info)
    else:
        logger.info("No new or changed values found. Do nothing. {} {}".format(
            subject_name, session_name))


def upload_tabular_file(fw, filename, project_id, update_values=False, create_emtpy_entry=False,
                        subject_col="subject_id", session_col="session_id"):
    df = load_tabular_file(filename, subject_col, session_col)

    for i, row in df.iterrows():
        subject_name = row[subject_col]
        session_name = row[session_col]
        if not create_emtpy_entry:
            row = row.dropna()
        info = row.drop([subject_col, session_col]).to_dict()

        # preprend sub- and ses- prefix if not there
        if not subject_name.startswith("sub-"):
            subject_name = "sub-" + subject_name
        if not session_name.startswith("ses-"):
            session_name = "ses-" + session_name

        if session_name == "ses-":
            session = get_subject_session(fw, project_id, subject_name)
            if not session:
                raise Exception(
                    "Cannot find session for subject {}. Before uploading to the subject tab, "
                    "create at least one session for this subject.".format(
                        subject_name))
            session_name = session["label"]
            level = "subject"
        else:
            level = "session"

        logger.info(
            "Preparing {} {} for {} level".format(subject_name, session_name,
                                                  level))
        logger.debug("Uploading {}".format(info))

        upload_info(fw, project_id, subject_name, session_name, level, info,
                    update_values)


def get_fw_api(api_key=None):
    if not api_key:
        api_key = os.environ["FWAPI"]
    if not api_key:
        raise Exception(
            "No flywheel api key provided. Either pass explicitly, or set an env var FWAPI")
    return api_key


def fix_timestamps(project_label, group_id, api_key=None):
    from datetime import datetime, timezone

    api_key = get_fw_api(api_key)
    fw = flywheel.Client(api_key)
    project = fw.lookup(f"{group_id}/{project_label}")

    print(f"Fixing timestamps for {group_id} {project_label}.")

    for subject in project.subjects():
        for session in subject.sessions():
            print(f"{subject.label} {session.label}")
            session_num = int(session.label.replace("ses-tp", ""))
            if not session_num:
                raise RuntimeError(f"Session cannot be determined: {session.label}")
            session.update({"timestamp": datetime(1900, 1, session_num, 0, 0, tzinfo=timezone.utc)})
    print("Done")


def create_views(project_label, group_id, api_key=None):
    """
    Creates predefined views on site level
    """
    api_key = get_fw_api(api_key)
    fw = flywheel.Client(api_key)
    project = fw.lookup(f"{group_id}/{project_label}")

    views = {
        "cognition": ["subject.sex", "session.age_years", "session.info.cognition"],
        "health": ["subject.sex", "session.age_years", "session.info.health"],
        "demographics": ["subject.sex", "session.age_years", "session.info.demographics"],
        "motorskills": ["subject.sex", "session.age_years", "session.info.motorskills"],
        "questionnaires": ["subject.sex", "session.age_years", "session.info.questionnaires"],
        "all": ["subject.sex", "session.age_years", "session.info.cognition", "session.info.health",
                "session.info.demographics", "session.info.motorskills", "session.info.questionnaires"],

    }

    for v_name, v_cols in views.items():
        view = fw.View(label=v_name, columns=v_cols)
        view_id = fw.add_view(project.id, view)

    print("Done")


def upload_tabular_file_wrapper(filename, project_label, group_id, api_key=None, create=False, raise_on=None,
                                update_values=False, create_emtpy_entry=False, subject_col="subject_id",
                                session_col="session_id"):
    api_key = get_fw_api(api_key)
    fw = flywheel.Client(api_key)

    project = handle_project(fw, project_label, group_id, create, raise_on)
    project_id = project["id"]

    upload_tabular_file(fw, filename, project_id, update_values, create_emtpy_entry, subject_col, session_col)


def download_tabular_file_wrapper(filename, project_label, group_id, api_key):
    api_key = get_fw_api(api_key)
    fw = flywheel.Flywheel(api_key)

    project = handle_project(fw, project_label, group_id, create=False,
                             raise_on="missing")
    project_id = project["id"]

    df = get_info_for_all(fw, project_id)
    df.drop(columns=["BIDS.Label", "BIDS.Subject"], inplace=True)

    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filename, index=False, sep="\t")


def get_info_for_all(fw, project_id, add_age_sex=True):
    """
    """
    df = pd.DataFrame([])

    # Get all sessions
    existing_sessions = fw.get_project_sessions(project_id)

    for es in existing_sessions:
        session = fw.get_session(es.id)
        session_name = session['label']
        subject_name = session['subject']['code']

        info_nested_session = get_info_dict("session", session)
        info_flat_session = flatten_dict(info_nested_session)
        # remove "subject_raw.sex"
        _ = info_flat_session.pop("subject_raw.sex", "")

        df_ = pd.DataFrame(info_flat_session, index=[subject_name])

        # add session, age and sex
        df_["session"] = session_name
        if add_age_sex:
            df_["age"] = session.age_years
            df_["sex"] = session.subject.sex
        df = df.append(df_, sort=True)

    df.index.name = "subject"
    df = df.sort_index().reset_index()

    # bring important stuff to front
    c = df.columns.tolist()
    first_vars = ["subject", "session"]
    if add_age_sex:
        first_vars += ["sex", "age"]
    for f in first_vars:
        c.remove(f)
    c = first_vars + c
    df = df[c]

    return df

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

    std_cols = [("subject.label", "subject_id"), ("session.label", "session_id"), ("subject.sex", "sex"),
                ("session.age_years", "age")]
    std_cols_subject = [("subject.label", "subject_id")]
    views = {
        "all": ["session.info.cognition", "session.info.health", "session.info.demographics",
                "session.info.motorskills", "session.info.questionnaires"],
        "cognition": ["session.info.cognition"],
        "health": ["session.info.health"],
        "demographics": ["session.info.demographics"],
        "motorskills": ["session.info.motorskills"],
        "questionnaires": ["session.info.questionnaires"],
        "missing_info": ["subject.info.missing_info"],

    }

    for v_name, v_cols in views.items():
        # remove views with the same name
        existing_views = fw.get_views(project.id)
        for e_view in existing_views:
            if e_view.label == v_name:
                fw.delete_view(e_view.id)
                print(f"Old data view removed: {v_name}")

        # initial view with hierarchical columns (e.g., only one col for all cognition subdomains)
        initial_view = fw.View(label="init" + v_name, columns=std_cols + v_cols, include_labels=False)

        df = fw.read_view_dataframe(initial_view, project.id)[v_cols]

        unique_cols = set()
        for _, row in df.iterrows():
            d = row.dropna().to_dict()
            from flatten_dict import flatten
            flat_d = flatten(d, reducer='dot')
            unique_cols = unique_cols | set(flat_d.keys())

        # get an explicit list of hierarchical cols and clean aliases
        unique_cols = list(unique_cols)
        unique_cols.sort()
        unique_cols_clean = [c.replace("session.info.", "") for c in unique_cols]
        unique_cols_clean = [c.replace("subject.info.", "") for c in unique_cols_clean]
        unique_cols_clean = [c.replace(".", "__") for c in unique_cols_clean]
        cols = list(zip(unique_cols, unique_cols_clean))

        # get final view.
        if v_name == "missing_info":
            columns = std_cols_subject + cols
        else:
            columns = std_cols + cols
        view = fw.View(label=v_name, columns=columns, include_labels=False)
        view_id = fw.add_view(project.id, view)
        print(f"Data view added: {v_name}")

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


def delete_lhab_info(group_id, project_label, api_key=None, delete_subject_info_keys=["missing_info"],
                     delete_session_info_keys=['cognition', 'health', 'demographics', 'motorskills',
                                               'questionnaires']):
    """
    Removes keys from the info dict on subject and session levels
    Needs to be run in case variables are discontinued
    """
    api_key = get_fw_api(api_key)
    fw = flywheel.Client(api_key)
    project = fw.lookup(f"{group_id}/{project_label}")

    print(f"Deleting LHAB-related values (phenotype) in info dict for {group_id} {project_label}.")

    for subject in project.subjects():

        for k in delete_subject_info_keys:
            print(f"{subject.label} {k}")
            subject.delete_info(k)

        for session in subject.sessions():
            for k in delete_session_info_keys:
                print(f"{subject.label} {session.label} {k}")
                session.delete_info(k)
    print("DONE")

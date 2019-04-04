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


def upload_tabular_file(fw, filename, project_id, update_values=False,
                        subject_col="subject_id", session_col="session_id"):
    df = load_tabular_file(filename, subject_col, session_col)

    for i, row in df.iterrows():
        subject_name = row[subject_col]
        session_name = row[session_col]
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


def upload_tabular_file_wrapper(filename, project_label, group_id,
                                api_key=None, create=False, raise_on=None,
                                update_values=False, subject_col=None,
                                session_col=None):
    api_key = get_fw_api(api_key)
    fw = flywheel.Flywheel(api_key)

    project = handle_project(fw, project_label, group_id, create, raise_on)
    project_id = project["id"]

    upload_tabular_file(fw, filename, project_id, update_values, subject_col,
                        session_col)


def download_tabular_file_wrapper(filename, project_label, group_id, api_key):
    api_key = get_fw_api(api_key)
    fw = flywheel.Flywheel(api_key)

    project = handle_project(fw, project_label, group_id, create=False,
                             raise_on="missing")
    project_id = project["id"]

    df_subject, df_session = get_info_for_all(fw, project_id)
    df_subject.drop(columns=["session_id"], inplace=True)
    df_session.drop(columns=["BIDS.Label", "BIDS.Subject"], inplace=True)

    df = pd.merge(df_subject, df_session, how="outer", on="subject")
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filename, index=False, sep="\t")


def get_info_for_all(fw, project_id):
    """
    """
    df_subject = pd.DataFrame([])
    df_session = pd.DataFrame([])

    # Get all sessions
    existing_sessions = fw.get_project_sessions(project_id)

    for es in existing_sessions:
        session = fw.get_session(es.id)
        session_name = session['label']
        subject_name = session['subject']['code']

        info_nested_subject = get_info_dict("subject", session)
        info_flat_subject = flatten_dict(info_nested_subject)
        df_subject_ = pd.DataFrame(info_flat_subject, index=[subject_name])
        df_subject = df_subject.append(df_subject_, sort=True)

        info_nested_session = get_info_dict("session", session)
        info_flat_session = flatten_dict(info_nested_session)
        # add session age
        # fixme age floating point issue
        info_flat_session["age"] = session.age_years

        df_session_ = pd.DataFrame(info_flat_session, index=[subject_name])


        df_session_["session"] = session_name
        df_session = df_session.append(df_session_, sort=True)

    df_subject.index.name = "subject"
    df_session.index.name = "subject"

    df_subject = df_subject.sort_index().reset_index()
    df_session = df_session.sort_index().reset_index()

    c = df_subject.columns.tolist()
    c.remove("subject")
    c = ["subject"] + c
    df_subject = df_subject[c]
    df_subject = df_subject.drop_duplicates().reset_index(drop=True)

    c = df_session.columns.tolist()
    c.remove("subject")
    c.remove("session")
    c = ["subject", "session"] + c
    df_session = df_session[c]

    return df_subject, df_session

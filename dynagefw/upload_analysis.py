import flywheel
from .fw_utils import get_fw_api
from pprint import pprint
from datetime import datetime
from pathlib import Path
import pickle
import os
from zipfile import ZipFile
import shutil
from warnings import warn
import time
from datetime import datetime
import sys
from zipfile import ZipFile
from tempfile import TemporaryDirectory
import backoff
from OpenSSL.SSL import WantWriteError


def get_subject_containers(project, subjects):
    containers = []
    for subject in project.subjects():
        if subjects:
            if subject.label in subjects:
                use_subject = True
            else:
                use_subject = False
        else:
            use_subject = True
        if use_subject:
            containers.append(subject)
    return containers


def cont():
    c = input("\nContinue (y): ")
    if c != "y":
        print("Stopping...")
        sys.exit()


def fetch_analysis(fw, container, analysis_label):
    """Checks container for analysis with label.
    In none exists, creates one. If 1 exists returns id.
    """
    analyses = fw.get_container_analyses(container.id, filter=f'label="{analysis_label}"')
    if len(analyses) > 1:
        raise Exception(f"Max 1 analysis expected. Found {len(analyses)}")

    if analyses:
        analysis = analyses[0]
        analysis_already_existed = True
    else:
        analysis = container.add_analysis(label=analysis_label)
        analysis_already_existed = False
    return analysis, analysis_already_existed


def list_files(root_dir, search_strings):
    files = []
    os.chdir(root_dir)
    for s in search_strings:
        files_and_folders = Path(".").glob(s)
        for ff in files_and_folders:
            if ff.is_file():
                files.append(ff)
            else:
                files.extend([f for f in ff.rglob("*") if f.is_file()])
    files = list(set(files))
    if not files:
        warn(f"No files found {root_dir} {search_strings}")
    return files


def zip_files(files, zip_file_name, tmp_dir):
    zip_file = Path(str(Path(tmp_dir) / zip_file_name) + ".zip")
    with ZipFile(zip_file, 'w') as z:
        for file in files:
            z.write(file)
    return zip_file


def zip_and_upload_data(fw, container, root_dir, analysis_label, search_strings, note=""):
    assert isinstance(search_strings, list), "search_strings should be a list"
    files = list_files(root_dir, search_strings)

    if files:
        analysis, analysis_already_existed = fetch_analysis(fw, container, analysis_label)

        if analysis_already_existed:
            print(f"    analysis found for {container.label}. Assuming that it has all the data and skipping upload")

        else:  # upload data
            if note:
                analysis.add_note(note)
            with TemporaryDirectory() as tmp_dir:
                print(f"    zip and upload {len(files)} files")
                zip_file_name = f"{analysis_label}_{container.label}"
                zip_file = zip_files(files, zip_file_name, tmp_dir)

                @backoff.on_exception(backoff.expo, WantWriteError, max_time=600)
                def upload_(analysis, zip_file):
                    analysis.upload_output(zip_file)
                try:
                    upload_(analysis, zip_file)
                except Exception:
                    fw.delete_container_analysis(container.id, analysis.id)
                    raise RuntimeError(f"Upload for {container.label} failed. Removed analysis and stopping")
    return files


def upload_analysis(group_id, project_label, root_dir, api_key=None, level="subject", subjects=[],
                    search_strings_template=["{subject}*"], note="", check_ignored_files=True):
    """
    :param group_id:
    :param project_label:
    :param root_dir:
    :param api_key:
    :param level:
    :param subjects:
    :return:
    """
    assert level in ["subject", "project"], f'level needs to be "subject" or "project", not {level}'

    api_key = get_fw_api(api_key)
    fw = flywheel.Client(api_key)
    project = fw.lookup(f"{group_id}/{project_label}")

    root_dir = Path(root_dir)
    os.chdir(root_dir)
    analysis_label = root_dir.name

    files_uploaded = []
    if level == "subject":
        containers = get_subject_containers(project, subjects)
        print(f"Uploading {root_dir} into {project_label} for {len(containers)} subject.")
        cont()

        for container in containers:
            subject = container.label
            print(subject)
            search_strings = [s.format(subject=subject) for s in search_strings_template]
            files_uploaded += zip_and_upload_data(fw, container, root_dir, analysis_label,
                                                  search_strings=search_strings, note=note)
    elif level == "project":
        container = project
        search_strings = search_strings_template
        print(f"Uploading {root_dir} into {project_label} for group data.")
        cont()

        files_uploaded += zip_and_upload_data(fw, container, root_dir, analysis_label,
                                              search_strings=search_strings, note=note)

    print("Upload done")

    # check for files that have not been uploaded
    if check_ignored_files:
        all_files = set(list_files(root_dir, ["*"]))
        files_not_uploaded = all_files - set(files_uploaded)
        if files_not_uploaded:
            files_not_uploaded_ = [str(f) for f in files_not_uploaded]
            warn(f"\n\n\n{len(files_not_uploaded)} files not uploaded {files_not_uploaded_}")

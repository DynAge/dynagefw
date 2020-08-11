import flywheel
from .fw_utils import get_fw_api
from pprint import pprint
from datetime import datetime
from pathlib import Path
import pickle
import os
from zipfile import ZipFile
import shutil


def run_gear_on_subjects(group_id, project_label, gear, save_dir="~/fw_jobs", config=None, gear_version=None,
                         analysis_label_suffix="default", api_key=None):
    api_key = get_fw_api(api_key)
    fw = flywheel.Client(api_key)
    project = fw.lookup(f"{group_id}/{project_label}")

    if gear_version:
        v_str = f"/{gear_version}"
    else:
        v_str = ""
    gear = fw.lookup(f"gears/{gear}{v_str}")
    gear_config = gear.get_default_config()

    if config:
        for k, v in config.items():
            if k in gear_config.keys():
                gear_config[k] = v
            else:
                raise RuntimeError(f"Key {k} not part of config.\n\n{gear.get_default_config()}")

    subjects = []
    for subject in project.subjects():
        subjects.append(fw.get_subject(subject.id))

    if analysis_label_suffix:
        analysis_label_suffix = "__" + analysis_label_suffix
    analysis_label = f'{gear.gear.name}__{gear.gear.version}{analysis_label_suffix}'

    print(f"project: {project_label}")
    print(f"{gear.gear.name}:{gear.gear.version}")
    print(f"analysis label: {analysis_label}")

    print(f"On {len(subjects)} subjects")
    print(f"\n\nConfig:\n")
    pprint(gear_config)

    c = input("\n\nContinue (y): ")
    if c == "y":
        analysis_ids = []
        for subject in subjects:
            analysis_id = gear.run(analysis_label=analysis_label, config=gear_config, inputs={}, destination=subject)
            analysis_ids.append(analysis_id)

        save_dir = Path(save_dir).expanduser()
        out_file = Path(save_dir) / f'{datetime.now().strftime("%Y-%m-%d_%H%M%S")}__{analysis_label}.pkl'
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        print(f"Saving ids to {out_file}")
        pickle.dump(analysis_ids, open(out_file, "wb"))


    else:
        print("OK. Doing nothing.")


def check_jobs(analysis_id_file, api_key=None):
    api_key = get_fw_api(api_key)
    fw = flywheel.Client(api_key)

    analysis_ids = pickle.load(open(analysis_id_file, "rb"))

    info = {'cancelled': [], 'complete': [], 'failed': [], 'running': [], 'pending': []}

    for analysis_id in analysis_ids:
        analysis = fw.get_analysis(analysis_id)
        job_id = analysis.job.id
        job = fw.get_job(job_id)
        info[job.state].append(job_id)

    print("JOB INFO\n")
    for k, v in info.items():
        print(f"{k}:\t{len(v)}")


def cancle_jobs(pending=True, running=True, api_key=None):
    api_key = get_fw_api(api_key)
    fw = flywheel.Client(api_key)

    searches = []
    if pending:
        searches.append('state=pending')
    if running:
        searches.append('state=running')

    for search_str in searches:
        jobs = fw.jobs.find(search_str)
        print(f"Cancelling {len(jobs)} jobs")

        for job in jobs:
            job.change_state('cancelled')


def delete_canceled_analysis(group_id, project_label, api_key=None):
    api_key = get_fw_api(api_key)
    fw = flywheel.Client(api_key)
    project = fw.lookup(f"{group_id}/{project_label}")

    for subject in project.subjects():
        print(subject.label)
        ana_list = fw.get_container_analyses(subject.id)
        for analysis in ana_list:
            job = fw.get_job(analysis.job)
            if job.state == "cancelled":
                fw.delete_container_analysis(subject.id, analysis.id)


def download_analysis(group_id, project_label, analysis_label, file_starts_with, save_dir, api_key=None):
    api_key = get_fw_api(api_key)
    fw = flywheel.Client(api_key)
    project = fw.lookup(f"{group_id}/{project_label}")

    orig_dir = Path.cwd()
    out_dir = Path(save_dir) / analysis_label
    zip_out_dir = out_dir / "00_zip"
    extract_out_dir = out_dir / "00_extract"
    zip_out_dir.mkdir(parents=True, exist_ok=True)
    extract_out_dir.mkdir(parents=True, exist_ok=True)

    os.chdir(zip_out_dir)

    print("DOWNLOAD")
    for subject in project.subjects():
        print(subject.label)
        analysis = fw.get_container_analyses(subject.id, filter=f'label="{analysis_label}"')
        assert len(analysis) <= 1, "More than one analysis found"
        if analysis:
            if analysis[0].files:
                files = [file_obj.name for file_obj in analysis[0].files]
            else:
                files = []

            # filter files
            download_files = []
            if file_starts_with:
                for f in files:
                    if f.startswith(file_starts_with):
                        download_files.append(f)
            else:
                download_files = files

            for file in download_files:
                print(file)
                analysis[0].download_file(file, file)

    print("UNZIP")
    zipfiles = list(zip_out_dir.glob("*.zip"))
    for file in zipfiles:
        with ZipFile(file, "r") as zip_ref:
            zip_ref.extractall(extract_out_dir)

    print("MOVE AND CLEAN UP")
    os.chdir(extract_out_dir)
    os.system(f"mv */* {out_dir}")
    shutil.rmtree(extract_out_dir)
    shutil.rmtree(zip_out_dir)

    print("DONE")
    os.chdir(orig_dir)

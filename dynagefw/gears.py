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


def run_gear(group_id, project_label, gear, save_dir="~/fw_jobs", config=None, gear_version=None,
             analysis_label_suffix="default", api_key=None, level="subject", subjects=[]):
    assert level in ["subject", "session"], f'level needs to be "subject" or "session", not {level}'

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
            if level == "session":
                for session in subject.sessions():
                    containers.append(session)
            else:
                containers.append(subject)

    if analysis_label_suffix:
        analysis_label_suffix = "__" + analysis_label_suffix
    analysis_label = f'{gear.gear.name}__{gear.gear.version}{analysis_label_suffix}'

    print(f"project: {project_label}")
    print(f"{gear.gear.name}:{gear.gear.version}")
    print(f"analysis label: {analysis_label}")
    print(f"level {level}")

    print(f"On {len(containers)} {level}s")
    print(f"\n\nConfig:\n")
    pprint(gear_config)

    c = input("\n\nContinue (y): ")
    if c == "y":
        analysis_ids = []
        for n, container in enumerate(containers):
            try:
                analysis_id = gear.run(analysis_label=analysis_label, config=gear_config, inputs={},
                                       destination=container)
                print(n, container.label)
            except:
                try:
                    t = 10
                    print(f"Could not submit analysis {n} {container.id}. Wait {t} seconds and retry {datetime.now()}")
                    time.sleep(t)
                    analysis_id = gear.run(analysis_label=analysis_label, config=gear_config, inputs={},
                                           destination=container)
                    print(n, container.label)
                except:
                    try:
                        t = 20
                        print(f"Could not submit analysis {n} {container.id}. \
                            Wait {t} seconds and retry {datetime.now()}")
                        time.sleep(t)
                        analysis_id = gear.run(analysis_label=analysis_label, config=gear_config, inputs={},
                                               destination=container)
                        print(n, container.label)
                    except:
                        t = 60
                        print(
                            f"Could not submit analysis {n} {container.id}. Wait {t} seconds and retry. \
                            last try! {datetime.now()}")
                        time.sleep(t)
                        analysis_id = gear.run(analysis_label=analysis_label, config=gear_config, inputs={},
                                               destination=container)
                        print(n, container.label)

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
    if info["failed"]:
        print("FAILED JOBS:")
        print(info["failed"])


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
            print(job.id)
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
                print(analysis.id)
                fw.delete_container_analysis(subject.id, analysis.id)


def download_analysis(group_id, project_label, analysis_label, file_starts_with, save_dir, api_key=None):
    """
    Looks for analysis matching the {analysis_label}
    if they cannot be found on the subject levle, the sessions are queried
    inside the analysis containers, looks for files that have names that start with {file_starts_with} [if None
    downloads all]
    downloads to save_dir, extracts and cleans up tree
    """
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
        analyses = fw.get_container_analyses(subject.id, filter=f'label="{analysis_label}"')
        assert len(analyses) <= 1, "More than one analysis found"

        # if no analyses on subject level, look into sessions
        if not analyses:
            analyses = []
            for session in subject.sessions():
                analyses_session = fw.get_container_analyses(session.id, filter=f'label="{analysis_label}"')
                assert len(analyses_session) <= 1, "More than one analysis found"
                analyses += analyses_session

        if analyses:
            for analysis in analyses:
                if analysis.files:
                    files = [file_obj.name for file_obj in analysis.files]
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
                    analysis.download_file(file, file)

    print("UNZIP")
    zipfiles = list(zip_out_dir.glob("*.zip"))
    for file in zipfiles:
        with ZipFile(file, "r") as zip_ref:
            zip_ref.extractall(extract_out_dir)

    print("MOVE AND CLEAN UP")
    # remove id hierarchy and move to out_dir
    # e.g., '5f34/sub-x/ses-y/func/*bold.json'
    #       'sub-x/ses-y/func/*bold.json'
    os.chdir(extract_out_dir)
    file_tree = [f for f in Path(".").rglob("*") if f.is_file()]
    file_overwritten = []
    for in_file in file_tree:
        out_file = out_dir / Path(*in_file.parts[1:])
        out_file.parent.mkdir(parents=True, exist_ok=True)
        print(in_file, out_file)
        if out_file.is_file():
            file_overwritten.append(out_file)
        in_file.rename(out_file)

    if file_overwritten:
        file_overwritten_str = '\n'.join([str(f) for f in set(file_overwritten)])
        warn(f"{len(set(file_overwritten))} have been overwritten, because of multiple files with the same name in "
             f"different analyses.\n{file_overwritten_str}")
    shutil.rmtree(extract_out_dir)
    shutil.rmtree(zip_out_dir)

    print("DONE")
    os.chdir(orig_dir)

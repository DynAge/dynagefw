import flywheel
from .fw_utils import get_fw_api
from pprint import pprint
from datetime import datetime
from pathlib import Path
import pickle


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

from dynagefw.gears import run_gear_on_subjects
import os

group_id = "lhab"
project_label = "lhab_mini"
gear = "bids-fmriprep"

config = {}
config["gear-FREESURFER_LICENSE"] = os.environ["gear_FREESURFER_LICENSE"]
config["n_cpus"] = 8
config["fs-no-reconall"] = True
config["longitudinal"] = True

run_gear_on_subjects(group_id, project_label, gear, config=config)

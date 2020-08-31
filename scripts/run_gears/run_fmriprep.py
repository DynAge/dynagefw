from dynagefw.gears import run_gear
import os

group_id = "lhab"
project_label = "lhab_mini"
gear = "bids-fmriprep"

config = {}
config["gear-FREESURFER_LICENSE"] = os.environ["gear_FREESURFER_LICENSE"]
config["n_cpus"] = 4
config["fs-no-reconall"] = True
config["longitudinal"] = True

subjects = ["sub-lhabX0001"]
run_gear(group_id, project_label, gear, config=config, level="subject", subjects=["sub-lhabX0001"])

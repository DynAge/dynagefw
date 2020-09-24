from dynagefw.gears import run_gear
import os

group_id = "lhab"
project_label = "LHAB"
gear = "bids-fmriprep"

config = {}
config["gear-FREESURFER_LICENSE"] = os.environ["gear_FREESURFER_LICENSE"]
config["fs-no-reconall"] = True
config["longitudinal"] = True


run_gear(group_id, project_label, gear, config=config, level="subject")

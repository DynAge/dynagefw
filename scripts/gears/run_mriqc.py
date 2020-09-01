from dynagefw.gears import run_gear
import os

group_id = "lhab"
project_label = "LHAB"
gear = "bids-mriqc"

config = {}

run_gear(group_id, project_label, gear, config=config, analysis_label_suffix="default", level="subject")

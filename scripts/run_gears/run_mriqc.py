from dynagefw.gears import run_gear_on_subjects
import os

group_id = "lhab"
project_label = "lhab_mini"
gear = "bids-mriqc"

config = {}

run_gear_on_subjects(group_id, project_label, gear, config=config)

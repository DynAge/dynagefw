from dynagefw.upload_analysis import upload_analysis
import os

group_id = "lhab"
project_label = "lhab_mini"

root_dir = "/Volumes/lhab_data/LHAB/LHAB_v2.0.0/derivates/freesurfer_v6.0.1-5"

note = """
freesurfer bids-app v6.0.1-5 (https://github.com/bids-apps/freesurfer)
run on the science cloud with bidswrapps
"""

search_strings = ["00_group*"]
upload_analysis(group_id, project_label, root_dir, level="project", note=note, search_strings_template=search_strings,
                check_ignored_files=False)

search_strings = ["{subject}*"]
upload_analysis(group_id, project_label, root_dir, level="subject", note=note,
                search_strings=search_strings, check_ignored_files=True)

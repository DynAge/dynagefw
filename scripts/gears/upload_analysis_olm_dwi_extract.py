from dynagefw.upload_analysis import upload_analysis
import os

group_id = "olm"
project_label = "OLM"

root_dir = "/mnt/olm/derivates/extract_fa_v4"

note = """
http://github.com/fliem/extract_FA v4 
run on the science cloud with bidswrapps
"""

search_strings = ["00_group"]
upload_analysis(group_id, project_label, root_dir, level="project", note=note, search_strings_template=search_strings,
                check_ignored_files=False)

search_strings = ["*/{subject}*"]
upload_analysis(group_id, project_label, root_dir, level="subject", note=note, search_strings_template=search_strings,
                check_ignored_files=True)

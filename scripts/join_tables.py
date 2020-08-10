"""join all wide tables
"""
from pathlib import Path
from dynagefw.utils import join_wide_files

# phenotype_in_dir = Path("/Volumes/lhab_data/LHAB/LHAB_v2.0.0/phenotype")
# out_file = Path("/Users/franzliem/Desktop/fw_upload/joined_tables.tsv")
in_dir = Path("/Users/franzliem/Desktop/fw_sandbox/phenotype_sandbox")
out_file = Path("/Users/franzliem/Desktop/fw_sandbox/fw_upload/joined_tables.tsv")
missings_out_file = Path("/Users/franzliem/Desktop/fw_sandbox/fw_upload/joined_tables_missings.tsv")

input_files = in_dir.glob("**/*_wide.tsv")
missing_input_files = in_dir.glob("**/*_missing_info.tsv")

join_wide_files(input_files, missing_input_files, out_file, missings_out_file)

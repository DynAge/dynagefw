"""join all wide tables
"""
from pathlib import Path
from dynagefw.utils import join_wide_files

# phenotype_in_dir = Path("/Volumes/lhab_data/LHAB/LHAB_v2.0.0/phenotype")
# out_file = Path("/Users/franzliem/Desktop/fw_upload/joined_tables.tsv")
in_dir = Path("/Users/franzliem/Desktop/fw_sandbox/phenotype_sandbox")
out_file = Path("/Users/franzliem/Desktop/fw_sandbox/fw_upload/joined_tables.tsv")

input_files = in_dir.glob("**/*_wide.tsv")


join_wide_files(input_files, out_file)
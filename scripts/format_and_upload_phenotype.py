"""join all wide tables
"""
import argparse
from pathlib import Path
from dynagefw.utils import join_wide_files
from dynagefw.fw_utils import upload_tabular_file_wrapper
from tempfile import TemporaryDirectory

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Upload phenotype data')

    parser.add_argument('group_id', help='Group ID on Flywheel instance.')
    parser.add_argument('project_label', action='store', help='Project Label on Flywheel instance')
    parser.add_argument('phenotype_in_dir', action='store', help='LHAB-style phenotype input directory')
    parser.add_argument('--api-key', dest='api_key', action='store', required=False,
                        help='API key. If not passed, looks for env var "FWAPI"')
    args = parser.parse_args()


    tmp_dir = TemporaryDirectory()
    print(f"saving intermed files to {tmp_dir.name}")
    out_file = Path(tmp_dir.name) / "joined_tables.tsv"

    project_label = "lhab_mini7"
    group_id = "lhab"

    input_files = Path(args.phenotype_in_dir).glob("**/*_wide.tsv")

    join_wide_files(input_files, out_file)
    upload_tabular_file_wrapper(out_file, project_label=args.project_label, group_id=args.group_id)

    tmp_dir.cleanup()
    print(f"{tmp_dir.name} removed")
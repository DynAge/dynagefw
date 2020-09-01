from dynagefw.fw_utils import delete_lhab_info
import argparse
from dynagefw.gears import download_analysis

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='removes all lhab-related data from \
    subject and session containers')

    parser.add_argument('group_id', help='Group ID on Flywheel instance.')
    parser.add_argument('project_label', action='store', help='Project Label on Flywheel instance')
    parser.add_argument('--api-key', dest='api_key', action='store', required=False,
                        help='API key. If not passed, looks for env var "FWAPI"')
    args = parser.parse_args()

    delete_lhab_info(args.group_id, args.project_label, api_key=args.api_key)

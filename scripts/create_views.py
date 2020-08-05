"""
the fw gui lists sessions according to timestamps. to make this consistent, we create fake timestamps for the sessions
"""
import argparse
from dynagefw.fw_utils import create_views

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fix timestamps in lhab-style projects')

    parser.add_argument('group_id', help='Group ID on Flywheel instance.')
    parser.add_argument('project_label', action='store', help='Project Label on Flywheel instance')
    parser.add_argument('--api-key', dest='api_key', action='store', required=False,
                        help='API key. If not passed, looks for env var "FWAPI"')
    args = parser.parse_args()

    create_views(args.project_label, args.group_id, api_key=args.api_key)

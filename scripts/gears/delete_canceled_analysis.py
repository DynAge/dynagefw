import argparse
from dynagefw.gears import delete_canceled_analysis

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Removes analysis that have been canceled or have failed')

    parser.add_argument('group_id', help='Group ID on Flywheel instance.')
    parser.add_argument('project_label', action='store', help='Project Label on Flywheel instance')
    parser.add_argument('--api-key', dest='api_key', action='store', required=False,
                        help='API key. If not passed, looks for env var "FWAPI"')
    args = parser.parse_args()

    delete_canceled_analysis(args.group_id, args.project_label, api_key=args.api_key)

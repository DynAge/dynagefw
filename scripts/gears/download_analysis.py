import argparse
from dynagefw.gears import download_analysis

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download and unzip gear analysis outputs for an entire project')

    parser.add_argument('group_id', help='Group ID on Flywheel instance.')
    parser.add_argument('project_label', action='store', help='Project Label on Flywheel instance')
    parser.add_argument('analysis_label', action='store', help='Exact label of analysis')
    parser.add_argument('save_dir', action='store',
                        help='Directory to save outputs (will create folder with analysis label in this folder)')
    parser.add_argument('--file-starts-with', dest='file_starts_with', action='store', required=False,
                        help='string for filtering files in output. Only downloads files that startwith string.\
                             Download all files if empty')
    parser.add_argument('--api-key', dest='api_key', action='store', required=False,
                        help='API key. If not passed, looks for env var "FWAPI"')
    args = parser.parse_args()

    download_analysis(args.group_id, args.project_label, args.analysis_label, args.save_dir, args.file_starts_with,
                      api_key=args.api_key)

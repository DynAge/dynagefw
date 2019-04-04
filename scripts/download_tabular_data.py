import argparse

import logging
from dynagefw.fw_utils import download_tabular_file_wrapper

if __name__ == '__main__':
    logger = logging.getLogger("dynagefw")
    logger.setLevel(logging.INFO)

    ### Read in arguments
    parser = argparse.ArgumentParser(
        description='Upload tabular file with info')
    parser.add_argument('filename',
                        help='.tsv outputfile'
                             'If folder does not exist, it will be created')
    parser.add_argument('--api-key', dest='api_key', action='store',
                        required=False, help='API key')
    parser.add_argument('-p', dest='project_label', action='store',
                        required=False, default=None,
                        help='Project Label on Flywheel instance')
    parser.add_argument('-g', dest='group_id', action='store',
                        required=True, help='Group ID on Flywheel instance.')

    args = parser.parse_args()

    download_tabular_file_wrapper(args.filename, args.project_label,
                                  group_id=args.group_id,
                                  api_key=args.api_key
                                  )

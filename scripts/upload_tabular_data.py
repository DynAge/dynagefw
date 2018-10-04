import argparse

import logging
from dynagefw.fw_utils import upload_tabular_file_wrapper

if __name__ == '__main__':
    logger = logging.getLogger("dynagefw")
    logger.setLevel(logging.INFO)

    ### Read in arguments
    parser = argparse.ArgumentParser(description='Upload tabular file with info')
    parser.add_argument('filename',
                        help='file with tabular data (.csv/.tsv/.xlsx). '
                             'header needs "subject" field.'
                             'If a "session" column is present and not empty, data is uploaded to the session tab. '
                             'If a "session" column is not present or empty, data is uploaded to the subject tab. '
                             'Note that data can only be uploaded to the subject tab, after at least one session '
                             'for this subject was created.')
    parser.add_argument('--api-key', dest='api_key', action='store',
                        required=False, help='API key')
    parser.add_argument('-p', dest='project_label', action='store',
                        required=False, default=None, help='Project Label on Flywheel instance')
    parser.add_argument('-g', dest='group_id', action='store',
                        required=True, help='Group ID on Flywheel instance.')
    parser.add_argument('-c', dest='create', action='store_true',
                        required=False, help='Needed if you want to upload to project that '
                                             'has not been created yet. Default=False')
    parser.add_argument('-r', dest='raise_on', action='store', required=False,
                        choices=[None, 'missing', 'existing'], default=None,
                        help='Raise error if project is (not) existing. Default=None')
    parser.add_argument('-u', dest='update_values', action='store_true',
                        required=False, help='If you want to change values that are already in the db, set this.')

    args = parser.parse_args()

    upload_tabular_file_wrapper(args.filename, args.project_label,
                                group_id=args.group_id,
                                api_key=args.api_key,
                                create=args.create,
                                raise_on=args.raise_on,
                                update_values=args.update_values)

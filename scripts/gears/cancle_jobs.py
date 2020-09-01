from dynagefw.gears import cancle_jobs
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='cancel all jobs')

    parser.add_argument('--api-key', dest='api_key', action='store', required=False,
                        help='API key. If not passed, looks for env var "FWAPI"')
    args = parser.parse_args()

    cancle_jobs(api_key=args.api_keyl)

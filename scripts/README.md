# scripts

For scripts that require a connection to the database, an API key is required. The respective scripts and functions 
have an optional argument that can be used to pass the key. If no key is provided, it assumes that an env var 
"FWAPI" holds the key.

## `scripts/`
Holds scripts to wrangle and format phenotypical data and upload it to the database.

* format_and_upload_phenotype.py
    * takes lhab-formatted phenotype data, re-formats it to make it ready for the database, joins all available data
     and uploads it. combines the following scripts:
        * join_tables.py
        * upload_tabular_data.py

* create_views.py
    * after uploading the phenotype data, creates data views
* delete_lhab_info.py
    * removes all lhab-related data from subject and session containers

* create_sandbox_data.py
    * goes through phenotypical tables and only retains sandbox subjects

* fix_timestamps.py
    * the fw gui lists sessions according to timestamps. to make this consistent, we create fake timestamps for the 
    sessions


## `scripts/gears/`
Holds scripts related to gear job-submission and download of analysis data

Run analysis with
* run_fmriprep.py
* run_mriqc.py

When running jobs
* check_jobs.py
* cancle_jobs.py
* delete_canceled_analysis.py

When analysis is done
* download_analysis.py

# fixme? Use the long tables to avoid issues with missing values?
# check in fw


"""join all wide tables
"""
from pathlib import Path
import pandas as pd
from functools import reduce

in_dir = Path("/Users/franzliem/Desktop/fw_sandbox/phenotype_sandbox")
out_file = Path("/Users/franzliem/Desktop/fw_sandbox/phenotype_sandbox_upload"
                "/joined_tables.tsv")
out_file.parent.mkdir(parents=True, exist_ok=True)

g = in_dir.glob("**/*_wide.tsv")
df = pd.DataFrame([])
dfs = []

for f in g:
    # get domain and subdomain, e.g.,
    # domain = 'demographics'
    # subdomain = 'edu_isced' from
    # phenotype_sandbox/01_Demographics/data/01_Edu_ISCED_wide.tsv

    domain = f.parts[-3].split("_")[-1].lower()
    subdomain = "_".join(f.parts[-1].split("_")[1:-1]).lower()

    df_in = (pd.read_csv(f, sep="\t").
             drop(columns=["conversion_date"])
             )

    # rename columns to {domain}.{subdomain}.{colName}
    cols = df_in.drop(columns=["subject_id", "session_id"]).columns.values
    ren = {}
    for c in cols:
        ren[c] = f"{domain}.{subdomain}.{c}"
    df_in = df_in.rename(columns=ren)

    dfs.append(df_in)

df = reduce(lambda left, right: pd.merge(left, right,
                                         on=["subject_id", "session_id"],
                                         how="outer"
                                         ), dfs)

df.to_csv(out_file, sep="\t", index=False)
print("")

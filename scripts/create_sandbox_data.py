"""goes through phenotypical tables and only retains sandbox subjects.
"""

from pathlib import Path
import pandas as pd

keep_subjects = ["lhabX0001", "lhabX0003", "lhabX0007"]

in_dir = Path("/Volumes/lhab_data/LHAB/LHAB_v2.0.0/phenotype")
out_dir = Path("/Users/franzliem/Desktop/fw_sandbox/phenotype_sandbox")

g = list(in_dir.glob("**/*.tsv"))

for f in g:
    print(f)
    out_file = out_dir / f.relative_to(in_dir)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(f, sep="\t")
    df = df[df.subject_id.isin(keep_subjects)]
    df.to_csv(out_file, sep="\t", index=False)

print("done")

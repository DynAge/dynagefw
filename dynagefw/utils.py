from functools import reduce

import flatten_dict as fdict
from pathlib import Path
import pandas as pd
import numpy as np


def dot_reducer(k1, k2):
    if k1 is None:
        return k2
    else:
        return k1 + "." + k2


def dot_splitter(flat_key):
    return flat_key.split(".")


d = {"a": 1, "b": 2}
d1 = {"a": 1, "b": {"x": 1}}


def dict_is_hierarchical(d):
    """
    >>> dict_is_hierarchical({"a": 1, "b": 2})
    False

    >>> dict_is_hierarchical({"a": 1, "b": {"x": 2}})
    True
    """
    is_hierarchical = False
    for k, v in d.items():
        if isinstance(v, dict):
            is_hierarchical = True
    return is_hierarchical


def flatten_dict(nested_d):
    """
    >>> flatten_dict({"age": 11, "cog": {"ps": 1, "mem": 3}})
    {'age': 11, 'cog.ps': 1, 'cog.mem': 3}

    >>> flatten_dict({"age": 11, "ps": 1})
    {'age': 11, 'ps': 1}

    >>> flatten_dict(None)
    {}
    """
    if nested_d:
        # fdict.flatten fails if you try to flatten a flat dict
        if dict_is_hierarchical(nested_d):
            return fdict.flatten(nested_d, reducer=dot_reducer)
        else:
            return nested_d
    else:
        # helpful when db returns None because no data there
        return {}


def nest_dict(flat_d):
    """
    >>> nest_dict({"age": 11, "cog.ps": 1, "cog.mem": 3})
    {'age': 11, 'cog': {'ps': 1, 'mem': 3}}
    """
    return fdict.unflatten(flat_d, splitter=dot_splitter)


def get_info_dict(level, d):
    """
    >>> d = {"subject": {"info": {"age": 33}}, "info": {"var": 1}}
    >>> get_info_dict("subject", d)
    {'age': 33}

    >>> get_info_dict("session", d)
    {'var': 1}
    """
    if level == "session":
        return d["info"]
    if level == "subject":
        return d["subject"]["info"]
    else:
        raise Exception(level)


def prepare_info_dict(level, d):
    """
    >>> prepare_info_dict("session", {"var": 66})
    {'info': {'var': 66}}

    >>> prepare_info_dict("subject", {"age": 55})
    {'subject': {'info': {'age': 55}}}
    """
    if level == "session":
        return {"info": d}
    if level == "subject":
        return {"subject": {"info": d}}
    else:
        raise Exception(level)


def compare_info_dicts(current_info, new_info):
    """
    input are flattened dicts
    for each key in new_info, check if it's already in current info
     if it's there, check if the values are different
     if it's new, note as well
    Returns keys of (changes, new)

    >>> c = {"a": 1, "b": 2}
    >>> n = {"b": 3, "c": 5}
    >>> compare_info_dicts(c, n)
    (['b'], ['c'])

    >>> c = {"a": 1, "b": 2}
    >>> n = {"b": 2}
    >>> compare_info_dicts(c, n)
    ([], [])

    >>> c = {"a": 1, "b": 2}
    >>> n = {"c": 2}
    >>> compare_info_dicts(c, n)
    ([], ['c'])

    >>> c = {"a": 1, "b": np.nan}
    >>> n = {"c": 2, "b": np.nan}
    >>> compare_info_dicts(c, n)
    ([], ['c'])

    >>> c = {"a": 1, "b": "a"}
    >>> n = {"c": 2, "b": "a"}
    >>> compare_info_dicts(c, n)
    ([], ['c'])

    >>> c = {"a": 1, "b": ""}
    >>> n = {"c": 2, "b": ""}
    >>> compare_info_dicts(c, n)
    ([], ['c'])

    >>> c = {"a": 1, "b": "a"}
    >>> n = {"c": 2, "b": "x"}
    >>> compare_info_dicts(c, n)
    (['b'], ['c'])
    """
    changes = []
    new = []
    for k in new_info.keys():
        if k in current_info.keys():
            # key already available, check if values differ
            if isinstance(new_info[k], str):
                if new_info[k] != current_info[k]:  # np.isclose does not work with stings
                    changes.append(k)
            else:
                if not np.isclose(new_info[k], current_info[k], equal_nan=True, atol=0, rtol=0):  # deals with nan
                    changes.append(k)
        else:
            new.append(k)
    return changes, new


def load_tabular_file(filename, subject_col, session_col):
    f = Path(filename)
    ext = f.suffix

    if ext == ".xlsx":
        df = pd.read_excel(f)
    elif ext == ".csv":
        df = pd.read_csv(f)
    elif ext == ".tsv":
        df = pd.read_csv(f, sep="\t")
    else:
        raise Exception("Cannot infer filetype {}".format(f))

    if subject_col not in df.columns:
        raise Exception(
            "A '{subject_col}' column is required in the tabular data, but cannot be found in {}".format(f))

    if session_col not in df.columns:
        df[session_col] = ""
    return df


def clean_nan(d, clean_val=""):
    """
    finds np.nan in flat dict and replaces them with clean_val
    >>> clean_nan({"a": 1, "b": np.nan})
    {'a': 1, 'b': ''}
    """
    for k, v in d.items():
        if not isinstance(v, str) and np.isnan(v):
            d[k] = clean_val
    return d


def join_wide_files(input_files, missing_input_files, out_file, missings_out_file):
    """
    concatenates wide lhab tables and rename columns to {domain}.{subdomain}.{colName}
    and long missing infput tables (rename collumns to missing_info.{domain}.{subdomain}.{colName}
    """

    out_file = Path(out_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    dfs = []
    for f in input_files:
        # get domain and subdomain, e.g.,
        # domain = 'demographics'
        # subdomain = 'edu_isced' from
        # phenotype_sandbox/01_Demographics/data/01_Edu_ISCED_wide.tsv

        domain = f.parts[-3].split("_")[-1].lower()
        subdomain = "_".join(f.parts[-1].split("_")[1:-1]).lower()
        df_in = pd.read_csv(f, sep="\t")

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
    df = df.sort_values(by=["subject_id", "session_id"])
    df.to_csv(out_file, sep="\t", index=False)
    print(f"Saved to {out_file}")

    if missings_out_file:
        dfs = []
        for f in missing_input_files:
            domain = f.parts[-3].split("_")[-1].lower()
            subdomain = "_".join(f.parts[-1].split("_")[1:-2]).lower()
            df_in = pd.read_csv(f, sep="\t")
            df_in = df_in.loc[df_in.data_missing]
            df_in = df_in[['subject_id', 'session_id', 'info', 'test_name']].set_index(['subject_id'])

            # make wide and format multiindex cols
            df_in["test_name"] = df_in["test_name"] + "." + df_in["session_id"]
            df_in.drop(columns=["session_id"], inplace=True)
            df_in_wide = df_in.pivot(columns="test_name").reset_index()
            out_cols = []
            c = df_in_wide.columns.to_flat_index()
            for cc in c:
                out_cols.append("".join([cc[0].replace("info", ""), cc[1]]))
            df_in_wide.columns = out_cols

            # rename columns to missing_info.{domain}.{subdomain}.{colName}
            cols = df_in_wide.drop(columns=["subject_id"]).columns.values
            ren = {}
            for c in cols:
                ren[c] = f"missing_info.{domain}.{subdomain}.{c}"
            df_in_wide = df_in_wide.rename(columns=ren)
            dfs.append(df_in_wide)

        df = reduce(lambda left, right: pd.merge(left, right,
                                                 on=["subject_id"],
                                                 how="outer"
                                                 ), dfs)
        df = df.sort_values(by=["subject_id"])
        df.to_csv(missings_out_file, sep="\t", index=False)
        print(f"Saved to {missings_out_file}")

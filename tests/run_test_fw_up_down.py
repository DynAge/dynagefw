from dynagefw.fw_utils import upload_tabular_file, get_fw_api, get_info_for_all
from dynagefw.fw_bids_utils import handle_project
import flywheel
from datetime import datetime
import pandas as pd

TEARDOWN = True


def run_dynagefw_up_down_test():
    api_key = get_fw_api()
    fw = flywheel.Flywheel(api_key)

    timestamp = datetime.now().isoformat(timespec='minutes')
    project_label = "test_dynagefw_{}".format(timestamp)
    group_id = "test1"
    project = handle_project(fw, project_label=project_label, group_id=group_id, create=True, raise_on="existing")
    project_id = project["id"]

    print(project_id, project_label)

    filename1 = "test_data/session_data_1.csv"
    upload_tabular_file(fw, filename1, project_id)

    filename_subject = "test_data/subject_data.xlsx"
    upload_tabular_file(fw, filename_subject, project_id)

    df_session_in = pd.read_csv(filename1).sort_index(axis=1).fillna("")
    df_subject_in = pd.read_excel(filename_subject).sort_index(axis=1).fillna("")

    df_subject_out, df_session_out = get_info_for_all(fw, project_id)
    df_subject_out.sort_index(axis=1, inplace=True)
    df_session_out.sort_index(axis=1, inplace=True)

    pd.testing.assert_frame_equal(df_session_in, df_session_out)
    pd.testing.assert_frame_equal(df_subject_in, df_subject_out)

    # test additional columns
    filename2 = "test_data/session_data_2.csv"
    upload_tabular_file(fw, filename2, project_id)

    df_session_2_in = pd.read_csv(filename2).sort_index(axis=1).fillna("")
    df_session_in = pd.merge(df_session_in, df_session_2_in).sort_index(axis=1)

    df_subject_out, df_session_out = get_info_for_all(fw, project_id)
    df_subject_out.sort_index(axis=1, inplace=True)
    df_session_out.sort_index(axis=1, inplace=True)

    pd.testing.assert_frame_equal(df_session_in, df_session_out)
    pd.testing.assert_frame_equal(df_subject_in, df_subject_out)

    # test update vals
    filename3 = "test_data/session_data_3.csv"
    upload_tabular_file(fw, filename3, project_id, update_values=True)

    df_session_2_in = pd.read_csv(filename2).sort_index(axis=1).fillna("")
    df_session_3_in = pd.read_csv(filename3).sort_index(axis=1).fillna("")
    df_session_in = pd.merge(df_session_2_in, df_session_3_in).sort_index(axis=1)

    df_subject_out, df_session_out = get_info_for_all(fw, project_id)
    df_subject_out.sort_index(axis=1, inplace=True)
    df_session_out.sort_index(axis=1, inplace=True)
    pd.testing.assert_frame_equal(df_session_in, df_session_out)
    pd.testing.assert_frame_equal(df_subject_in, df_subject_out)

    print("Tests seem ok {} {}".format(project_label, project_id))

    if TEARDOWN:
        print("Deleting {} {}".format(project_label, project_id))
        fw.delete_project(project_id)


if __name__ == "__main__":
    run_dynagefw_up_down_test()

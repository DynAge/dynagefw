from dynagefw.fw_utils import get_fw_api
import flywheel
import pandas as pd

group_id = "lhab"
project_label = "lhab_mini"
api_key = None

api_key = get_fw_api(api_key)
fw = flywheel.Client(api_key)
project = fw.lookup(f"{group_id}/{project_label}")

analysis_label = "bids-mriqc__1.1.0_0.15.2__sess"
# analysis_label = "bids-mriqc__1.1.0_0.15.2__default"
container = "session"

mod = {
    # "t1w_run-1": "*_run-1_t1w.json",
    # "t1w_run-2": "*_run-2_t1w.json",
    # "t2w": "*_t21w.json",
    "bold": "*_bold.json",
}

for modality, search_str in mod.items():
    view_name = f"{analysis_label}__{modality}"
    view_name = view_name.replace(".", "_")
    builder = flywheel.ViewBuilder(label=view_name,
                                   columns=['subject.label', 'subject.id'],
                                   container=container,
                                   analysis_label=analysis_label,
                                   # analysis_gear_name='bids-mriqc',
                                   filename='mriqc_*.zip'
                                   )
    builder.zip_member_filter(search_str)
    builder.file_match('all')
    # builder.file_column('gcor', type='float')
    view = builder.build()

    existing_views = fw.get_views(project.id)
    for e_view in existing_views:
        if e_view.label == view_name:
            fw.delete_view(e_view.id)
            print(f"Old data view removed: {view_name}")

    df = fw.read_view_dataframe(view, project.id)
    print(df.columns)
    view_id = fw.add_view(project.id, view)
    print(f"Data view added: {view_name}")

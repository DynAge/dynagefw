"""
A very hacky way to check engine instances
copy ips from openstack gui
"""
ips = """
	mriqc1-50	fw_engine_20200828_anaGears_1job_clean_400s_retry_mriqc	
172.23.34.210
2cpu-8ram-hpcv3	mbp	Active	nova	None	Running	1 minute	Create Snapshot
mriqc1-49	fw_engine_20200828_anaGears_1job_clean_400s_retry_mriqc	
172.23.34.190


"""
ips = [i for i in ips.split("\n") if i.startswith("172")]
s = ""
for ip in ips:
    s += f"echo {ip};ssh -t -oStrictHostKeyChecking=no ubuntu@{ip} sudo systemctl status flywheel_startup.service;"
print(s)

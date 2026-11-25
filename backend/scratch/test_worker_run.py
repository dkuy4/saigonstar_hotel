import sys
sys.path.insert(0, r"D:\HQT-CSDL\saigonstar_hotel\backend")
from app.workers.scheduler import BackgroundJobManager

def test_jobs():
    mgr = BackgroundJobManager.get_instance()
    for job_id in ["JOB_HET_HAN_GIU_CHO", "JOB_TU_NO_SHOW", "JOB_DOI_SOAT_PHONG", "JOB_DONG_BO_TY_GIA"]:
        res = mgr.execute_job(job_id)
        print(f"Executed {job_id}:", res)
    
    print("\nAll jobs status:")
    for j in mgr.get_all_jobs():
        print(j["id"], "->", j["lastStatus"], ":", j["lastResult"])

if __name__ == "__main__":
    test_jobs()

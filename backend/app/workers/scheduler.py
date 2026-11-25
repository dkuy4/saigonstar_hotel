import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json
import oracledb

from app.config import settings
from app.db import get_pool, fetch_cursor_as_dicts
from app.context import set_db_context
from app.workers.ty_gia import ExchangeRateService
from app.workers.email import EmailWorker

logger = logging.getLogger(__name__)

@dataclass
class JobState:
    id: str
    name: str
    description: str
    interval_seconds: int
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_status: str = "IDLE"  # IDLE, RUNNING, SUCCESS, ERROR
    last_duration_ms: float = 0.0
    last_result: Optional[str] = None
    last_error: Optional[str] = None
    total_runs: int = 0
    total_success: int = 0
    total_errors: int = 0

class BackgroundJobManager:
    """
    Central background job manager for Saigon Star Hotel (F13, FR-20, FR-52, NFR-03).
    Executes automated routines when DBMS_SCHEDULER is not running or on-demand from Manager UI.
    """
    _instance: Optional["BackgroundJobManager"] = None

    def __init__(self):
        self._jobs: Dict[str, JobState] = {
            "JOB_HET_HAN_GIU_CHO": JobState(
                id="JOB_HET_HAN_GIU_CHO",
                name="Quét đơn giữ chỗ hết hạn (HOLD -> EXPIRED)",
                description="Tự động nhả phòng cho các đơn quá hạn thanh toán theo BR-18, gửi email thông báo hết hạn",
                interval_seconds=60,
                next_run=datetime.now() + timedelta(seconds=60)
            ),
            "JOB_TU_NO_SHOW": JobState(
                id="JOB_TU_NO_SHOW",
                name="Tự động đánh dấu vắng mặt (NO_SHOW)",
                description="Tự động hủy và đóng đơn không nhận phòng quá giờ quy định theo BR-27, BR-28",
                interval_seconds=300,
                next_run=datetime.now() + timedelta(seconds=300)
            ),
            "JOB_DOI_SOAT_PHONG": JobState(
                id="JOB_DOI_SOAT_PHONG",
                name="Đối soát trạng thái phòng và lịch đặt",
                description="Kiểm tra sai lệch giữa trạng thái thực tế của phòng và các đơn CHECKED_IN theo NFR-03",
                interval_seconds=86400,
                next_run=datetime.now() + timedelta(seconds=86400)
            ),
            "JOB_DONG_BO_TY_GIA": JobState(
                id="JOB_DONG_BO_TY_GIA",
                name="Đồng bộ tỷ giá ngoại tệ ngân hàng",
                description="Cập nhật tỷ giá hàng ngày cho USD, EUR, CNY, KRW, JPY phục vụ thanh toán quốc tế (FR-10, D-37)",
                interval_seconds=86400,
                next_run=datetime.now() + timedelta(seconds=86400)
            ),
            "JOB_GUI_EMAIL": JobState(
                id="JOB_GUI_EMAIL",
                name="Gửi email theo hàng đợi (HANG_DOI_EMAIL)",
                description="Lấy các email CHO_GUI bằng FOR UPDATE SKIP LOCKED, dựng nội dung từ mẫu và gửi qua SMTP (FR-53)",
                interval_seconds=15,
                next_run=datetime.now() + timedelta(seconds=15)
            )
        }
        self._running_task: Optional[asyncio.Task] = None
        self._is_stopping: bool = False

    @classmethod
    def get_instance(cls) -> "BackgroundJobManager":
        if cls._instance is None:
            cls._instance = BackgroundJobManager()
        return cls._instance

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Return runtime status of all registered background jobs."""
        res = []
        for job in self._jobs.values():
            res.append({
                "id": job.id,
                "name": job.name,
                "description": job.description,
                "intervalSeconds": job.interval_seconds,
                "enabled": job.enabled,
                "lastRun": job.last_run.isoformat() if job.last_run else None,
                "nextRun": job.next_run.isoformat() if job.next_run else None,
                "lastStatus": job.last_status,
                "lastDurationMs": round(job.last_duration_ms, 2),
                "lastResult": job.last_result,
                "lastError": job.last_error,
                "totalRuns": job.total_runs,
                "totalSuccess": job.total_success,
                "totalErrors": job.total_errors,
            })
        return res

    def get_discrepancies(self, conn: oracledb.Connection) -> List[Dict[str, Any]]:
        """Execute PKG_PHONG.DOI_SOAT_PHONG_LICH and return discrepancy items."""
        with conn.cursor() as cur:
            cur_out = cur.callfunc("PKG_PHONG.DOI_SOAT_PHONG_LICH", oracledb.DB_TYPE_CURSOR)
            rows = fetch_cursor_as_dicts(cur_out)
            return [
                {
                    "roomId": r.get("phong_id"),
                    "roomNumber": r.get("ma_phong"),
                    "currentStatus": r.get("trang_thai"),
                    "discrepancyType": r.get("lech"),
                    "description": (
                        "Phòng đang ở nhưng không có đơn nào ở trạng thái CHECKED_IN"
                        if r.get("lech") == "DANG_O_NHUNG_KHONG_CO_DON_CHECKED_IN"
                        else "Có đơn CHECKED_IN nhưng phòng không ở trạng thái DANG_O"
                    )
                }
                for r in rows
            ]

    def execute_job(self, job_id: str) -> Dict[str, Any]:
        """Synchronously execute a background job using a dedicated DB connection."""
        if job_id not in self._jobs:
            raise ValueError(f"Unknown job_id: {job_id}")

        job = self._jobs[job_id]
        job.last_status = "RUNNING"
        start_time = time.time()
        job.total_runs += 1

        pool = get_pool()
        try:
            with pool.acquire() as conn:
                with conn.cursor() as cur:
                    if settings.ORA_SCHEMA:
                        cur.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {settings.ORA_SCHEMA}")
                
                # Context as system job
                set_db_context(conn, nguoi_id=None, vai_tro="HE_THONG", kenh="HE_THONG", ly_do=f"Tác vụ nền {job_id}")

                result_msg = ""

                if job_id == "JOB_HET_HAN_GIU_CHO":
                    with conn.cursor() as cur:
                        p_count = cur.var(oracledb.NUMBER)
                        cur.callproc("PKG_DAT_PHONG.HET_HAN_GIU_CHO", [p_count])
                        conn.commit()
                        count = int(p_count.getvalue() or 0)
                        result_msg = f"Đã quét và nhả {count} đơn hết hạn giữ chỗ (HOLD -> EXPIRED)."

                elif job_id == "JOB_TU_NO_SHOW":
                    with conn.cursor() as cur:
                        p_count = cur.var(oracledb.NUMBER)
                        cur.callproc("PKG_DAT_PHONG.TU_NO_SHOW", [p_count])
                        conn.commit()
                        count = int(p_count.getvalue() or 0)
                        result_msg = f"Đã quét và tự động chuyển {count} đơn vắng mặt quá giờ (NO_SHOW)."

                elif job_id == "JOB_DOI_SOAT_PHONG":
                    discrepancies = self.get_discrepancies(conn)
                    # Ghi nhật ký kiểm toán cho từng phòng lệch theo NFR-03 qua PKG_NHAT_KY.GHI
                    if discrepancies:
                        with conn.cursor() as cur:
                            for d in discrepancies:
                                cu_json = json.dumps({"trang_thai": d["currentStatus"]}, ensure_ascii=False)
                                moi_json = json.dumps({"lech": d["discrepancyType"]}, ensure_ascii=False)
                                cur.callproc("PKG_NHAT_KY.GHI", [
                                    "PHONG",
                                    str(d["roomId"]),
                                    "LECH_TRANG_THAI",
                                    cu_json,
                                    moi_json
                                ])
                            conn.commit()
                    result_msg = f"Đối soát hoàn tất. Phát hiện {len(discrepancies)} phòng có sai lệch trạng thái lịch."

                elif job_id == "JOB_DONG_BO_TY_GIA":
                    res = ExchangeRateService.sync_exchange_rates(conn)
                    rates_str = ", ".join([f"{k}: {v:,.0f} đ" for k, v in res.get("synced_rates", {}).items()])
                    result_msg = f"Đồng bộ tỷ giá thành công: {rates_str}."

                elif job_id == "JOB_GUI_EMAIL":
                    res = EmailWorker.process_queue(conn)
                    result_msg = (
                        f"Đã xử lý {res['processed']} email "
                        f"(Thành công: {res['sent']}, Chờ thử lại: {res['retrying']}, Lỗi: {res['failed']})."
                    )

                duration_ms = (time.time() - start_time) * 1000
                job.last_status = "SUCCESS"
                job.last_duration_ms = duration_ms
                job.last_run = datetime.now()
                job.next_run = datetime.now() + timedelta(seconds=job.interval_seconds)
                job.last_result = result_msg
                job.last_error = None
                job.total_success += 1

                logger.info(f"Background Job [{job_id}] executed successfully in {duration_ms:.1f}ms: {result_msg}")
                return {
                    "jobId": job_id,
                    "status": "SUCCESS",
                    "durationMs": duration_ms,
                    "result": result_msg,
                    "lastRun": job.last_run.isoformat(),
                    "nextRun": job.next_run.isoformat()
                }

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            job.last_status = "ERROR"
            job.last_duration_ms = duration_ms
            job.last_run = datetime.now()
            job.next_run = datetime.now() + timedelta(seconds=job.interval_seconds)
            job.last_error = str(e)
            job.total_errors += 1
            logger.error(f"Background Job [{job_id}] failed after {duration_ms:.1f}ms: {e}", exc_info=True)
            return {
                "jobId": job_id,
                "status": "ERROR",
                "durationMs": duration_ms,
                "error": str(e),
                "lastRun": job.last_run.isoformat(),
                "nextRun": job.next_run.isoformat()
            }

    async def _loop(self):
        """Scheduler background loop that checks and runs pending jobs."""
        logger.info("Background job scheduler loop started.")
        while not self._is_stopping:
            now = datetime.now()
            for job_id, job in self._jobs.items():
                if job.enabled and job.next_run and now >= job.next_run and job.last_status != "RUNNING":
                    try:
                        # Run in thread pool to avoid blocking asyncio event loop
                        await asyncio.to_thread(self.execute_job, job_id)
                    except Exception as e:
                        logger.error(f"Error executing scheduled job {job_id}: {e}")
            await asyncio.sleep(10)

    def start(self):
        """Start background scheduler loop."""
        if self._running_task is None or self._running_task.done():
            self._is_stopping = False
            self._running_task = asyncio.create_task(self._loop())

    def stop(self):
        """Stop background scheduler loop."""
        self._is_stopping = True
        if self._running_task and not self._running_task.done():
            self._running_task.cancel()
            self._running_task = None
        logger.info("Background job scheduler loop stopped.")

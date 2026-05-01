import logging
import time

from app.clients.alert_client import create_alert
from app.clients.audit_client import log
from app.clients.file_client import get_file_content, update_risk
from app.clients.risk_client import score as risk_score
from app.queue.redis_queue import dequeue
from app.workers.scanner import scan_content

logger = logging.getLogger(__name__)


def process_job(job: dict):
    file_id = job["file_id"]
    owner_id = job["owner_id"]
    stored_name = job.get("stored_name", "")
    # sensitivity is now passed from gateway-api via the queue payload
    sensitivity = job.get("sensitivity", "INTERNAL")

    logger.info(f"Processing job: file_id={file_id} owner_id={owner_id} sensitivity={sensitivity}")

    # 1. Run DLP scan on file content
    dlp_clean = True
    dlp_matches = []
    try:
        content = get_file_content(stored_name)
        if content:
            try:
                text = content.decode("utf-8", errors="ignore")
            except Exception:
                text = ""
            dlp_clean, dlp_matches = scan_content(text)
    except Exception as e:
        logger.warning(f"DLP scan failed: {e} — treating as clean")

    # 2. Score via risk-service
    # Use FILE_UPLOAD event type — this is a post-upload scan, not a download.
    # Pass sensitivity so the risk-service can apply secret-file rules correctly.
    risk_result = risk_score(
        owner_id=owner_id,
        sensitivity=sensitivity,
        dlp_matched=not dlp_clean,
    )
    score = risk_result.get("risk_score", 0)

    # 3. Determine final file status
    # DLP match overrides risk score — quarantine immediately
    if not dlp_clean:
        final_status = "QUARANTINED"
        final_score = max(score, 90)
        logger.warning(f"DLP matches found for file_id={file_id}: {dlp_matches}")
    elif score >= 80:
        final_status = "QUARANTINED"
        final_score = score
    else:
        final_status = "ACTIVE"
        final_score = score

    # 4. Update file in file-service with final risk score and status
    updated = update_risk(file_id=file_id, risk_score=int(final_score), status=final_status)
    logger.info(f"File updated: {updated}")

    # 5. Audit log
    log(
        actor=owner_id,
        action="SCAN_COMPLETE",
        resource=file_id,
        result=final_status,
    )

    # 6. Alert if quarantined
    if final_status == "QUARANTINED":
        reason = "DLP_MATCH" if not dlp_clean else "HIGH_RISK_SCORE"
        alert = create_alert(
            actor=owner_id,
            severity="HIGH",
            score_delta=int(final_score),
            details=f"file_id={file_id} reason={reason} risk_score={final_score} sensitivity={sensitivity}",
        )
        logger.info(f"Alert created: {alert}")


def run():
    logger.info("Worker started — polling Redis queue")

    while True:
        job = dequeue()

        if job:
            try:
                process_job(job)
            except Exception as e:
                logger.error(f"Job failed: {e} — job={job}")

        time.sleep(2)

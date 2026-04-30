import time

from app.clients.alert_client import create_alert
from app.clients.audit_client import log
from app.clients.file_client import get_file_content, update_risk
from app.clients.risk_client import score as risk_score
from app.queue.redis_queue import dequeue
from app.workers.scanner import scan_content


def process_job(job: dict):
    file_id = job["file_id"]
    owner_id = job["owner_id"]
    stored_name = job.get("stored_name", "")

    print(f"Processing job: file_id={file_id} owner_id={owner_id}")

    # 1. Run DLP scan on file content
    dlp_clean = True
    dlp_matches = []
    try:
        content = get_file_content(stored_name)
        if content:
            # Decode bytes to string for text-based scanning
            try:
                text = content.decode("utf-8", errors="ignore")
            except Exception:
                text = ""
            dlp_clean, dlp_matches = scan_content(text)
    except Exception as e:
        print(f"DLP scan failed: {e} — treating as clean")

    # 2. Get risk score from risk service
    risk_result = risk_score(file_id=file_id, owner_id=owner_id)
    score = risk_result.get("risk_score", 0)

    # 3. Determine final status
    # DLP match overrides risk score — quarantine immediately
    if not dlp_clean:
        final_status = "QUARANTINED"
        final_score = max(score, 90)  # DLP match = high risk
        print(f"DLP matches found: {dlp_matches}")
    elif score >= 80:
        final_status = "QUARANTINED"
        final_score = score
    else:
        final_status = "ACTIVE"
        final_score = score

    # 4. Update file in file-service
    updated = update_risk(file_id=file_id, risk_score=final_score, status=final_status)
    print(f"File updated: {updated}")

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
            score_delta=final_score,
            details=f"file_id={file_id} reason={reason} risk_score={final_score}",
        )
        print(f"Alert created: {alert}")


def run():
    print("Worker started — polling Redis queue")

    while True:
        job = dequeue()

        if job:
            try:
                process_job(job)
            except Exception as e:
                print(f"Job failed: {e} — job={job}")

        time.sleep(2)

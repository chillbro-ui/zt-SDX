#!/bin/bash
set -e
OUT=".kiro_tmp/results.txt"
echo "" > $OUT

check() {
  echo "=== $1 ===" >> $OUT
  echo "$2" >> $OUT
  echo "" >> $OUT
}

# ── Service health ────────────────────────────────────────────────────────────
check "gateway"      "$(curl -s http://localhost:8000/)"
check "auth"         "$(curl -s http://localhost:8001/)"
check "policy"       "$(curl -s http://localhost:8002/)"
check "file"         "$(curl -s http://localhost:8003/)"
check "audit"        "$(curl -s http://localhost:8004/)"
check "risk"         "$(curl -s http://localhost:8005/)"
check "alert"        "$(curl -s http://localhost:8006/)"

# ── Seed policies ─────────────────────────────────────────────────────────────
check "seed_policies" "$(curl -s -X POST http://localhost:8002/policy/seed)"

# ── Register user ─────────────────────────────────────────────────────────────
REGISTER=$(curl -s -X POST "http://localhost:8001/auth/register?email=alice@acme.com&password=Test1234!&role=EMPLOYEE&department=Engineering")
check "register" "$REGISTER"

# ── Login ─────────────────────────────────────────────────────────────────────
LOGIN=$(curl -s -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@acme.com","password":"Test1234!"}')
check "login" "$LOGIN"

TOKEN=$(echo $LOGIN | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','MISSING'))")
check "token_extracted" "$TOKEN"

# ── Get /me ───────────────────────────────────────────────────────────────────
check "me" "$(curl -s http://localhost:8000/me -H "Authorization: Bearer $TOKEN")"

# ── Upload file ───────────────────────────────────────────────────────────────
echo "test pdf content for dlp scan" > /tmp/test.txt
UPLOAD=$(curl -s -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test.txt")
check "upload" "$UPLOAD"

FILE_ID=$(echo $UPLOAD | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file',{}).get('id','MISSING'))")
check "file_id_extracted" "$FILE_ID"

# ── Wait for worker DLP scan ──────────────────────────────────────────────────
sleep 5

# ── Get file status after scan ────────────────────────────────────────────────
check "file_after_scan" "$(curl -s "http://localhost:8000/files/$FILE_ID" -H "Authorization: Bearer $TOKEN")"

# ── Download file ─────────────────────────────────────────────────────────────
check "download" "$(curl -s "http://localhost:8000/files/$FILE_ID/download" -H "Authorization: Bearer $TOKEN")"

# ── Create share ──────────────────────────────────────────────────────────────
SHARE=$(curl -s -X POST "http://localhost:8000/shares" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"file_id\":\"$FILE_ID\",\"recipient_email\":\"vendor@ext.com\",\"expiry_hours\":1,\"max_downloads\":1}")
check "create_share" "$SHARE"

SHARE_TOKEN=$(echo $SHARE | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('share_token','MISSING'))")
check "share_token_extracted" "$SHARE_TOKEN"

# ── Download via share ────────────────────────────────────────────────────────
check "share_download" "$(curl -s "http://localhost:8000/shares/$SHARE_TOKEN")"

# ── Audit events ──────────────────────────────────────────────────────────────
check "audit_events" "$(curl -s "http://localhost:8000/audit/events" -H "Authorization: Bearer $TOKEN")"

# ── Audit chain verify ────────────────────────────────────────────────────────
check "audit_verify" "$(curl -s "http://localhost:8000/audit/verify" -H "Authorization: Bearer $TOKEN")"

# ── Alerts ────────────────────────────────────────────────────────────────────
check "alerts" "$(curl -s "http://localhost:8000/alerts" -H "Authorization: Bearer $TOKEN")"

# ── Logout ────────────────────────────────────────────────────────────────────
check "logout" "$(curl -s -X POST "http://localhost:8000/logout" -H "Authorization: Bearer $TOKEN")"

# ── Token revoked after logout ────────────────────────────────────────────────
check "token_revoked" "$(curl -s "http://localhost:8000/me" -H "Authorization: Bearer $TOKEN")"

echo "DONE" >> $OUT

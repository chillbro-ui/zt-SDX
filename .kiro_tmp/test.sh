#!/bin/bash
OUT=".kiro_tmp/results.txt"
echo "" > $OUT

check() {
  echo "=== $1 ===" >> $OUT
  echo "$2" >> $OUT
  echo "" >> $OUT
}

# Use unique email per run to avoid Redis revocation from previous runs
EMAIL="testuser_$(date +%s)@acme.com"
check "test_email" "$EMAIL"

# ── Service health ────────────────────────────────────────────────────────────
check "gateway"   "$(curl -s http://localhost:8000/)"
check "auth"      "$(curl -s http://localhost:8001/)"
check "policy"    "$(curl -s http://localhost:8002/)"
check "file"      "$(curl -s http://localhost:8003/)"
check "audit"     "$(curl -s http://localhost:8004/)"
check "risk"      "$(curl -s http://localhost:8005/)"
check "alert"     "$(curl -s http://localhost:8006/)"

# ── Seed policies ─────────────────────────────────────────────────────────────
check "seed_policies" "$(curl -s -X POST http://localhost:8002/policy/seed)"

# ── Register user ─────────────────────────────────────────────────────────────
REGISTER=$(curl -s -X POST "http://localhost:8001/auth/register?email=${EMAIL}&password=Test1234!&role=EMPLOYEE&department=Engineering")
check "register" "$REGISTER"

# ── Login ─────────────────────────────────────────────────────────────────────
LOGIN=$(curl -s -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"Test1234!\"}")
check "login" "$LOGIN"

TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','MISSING'))" 2>/dev/null)
REFRESH_TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('refresh_token','MISSING'))" 2>/dev/null)
check "token_extracted" "$TOKEN"

if [ "$TOKEN" = "MISSING" ] || [ -z "$TOKEN" ]; then
  echo "LOGIN FAILED — stopping tests" >> $OUT
  exit 1
fi

# ── Get /me ───────────────────────────────────────────────────────────────────
check "me" "$(curl -s http://localhost:8000/me -H "Authorization: Bearer $TOKEN")"

# ── Upload file ───────────────────────────────────────────────────────────────
echo "This is a test document for ZT-SDX upload testing." > /tmp/testdoc.pdf
UPLOAD=$(curl -s -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/testdoc.pdf")
check "upload" "$UPLOAD"

FILE_ID=$(echo "$UPLOAD" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file',{}).get('id','MISSING'))" 2>/dev/null)
check "file_id_extracted" "$FILE_ID"

if [ "$FILE_ID" = "MISSING" ] || [ -z "$FILE_ID" ]; then
  check "upload_failed_detail" "$UPLOAD"
else
  # ── Wait for worker DLP scan ────────────────────────────────────────────────
  echo "Waiting 6s for worker DLP scan..." >> $OUT
  sleep 6

  # ── File status after scan ──────────────────────────────────────────────────
  check "file_after_scan" "$(curl -s "http://localhost:8000/files/$FILE_ID" -H "Authorization: Bearer $TOKEN")"

  # ── List files ──────────────────────────────────────────────────────────────
  check "list_files" "$(curl -s "http://localhost:8000/files" -H "Authorization: Bearer $TOKEN")"

  # ── Download file ───────────────────────────────────────────────────────────
  check "download" "$(curl -s "http://localhost:8000/files/$FILE_ID/download" -H "Authorization: Bearer $TOKEN")"

  # ── Create share ────────────────────────────────────────────────────────────
  SHARE=$(curl -s -X POST "http://localhost:8000/shares" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"file_id\":\"$FILE_ID\",\"recipient_email\":\"vendor@ext.com\",\"expiry_hours\":1,\"max_downloads\":2,\"watermark\":true}")
  check "create_share" "$SHARE"

  SHARE_TOKEN=$(echo "$SHARE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('share_token','MISSING'))" 2>/dev/null)
  check "share_token_extracted" "$SHARE_TOKEN"

  if [ "$SHARE_TOKEN" != "MISSING" ] && [ -n "$SHARE_TOKEN" ]; then
    check "share_download_1" "$(curl -s "http://localhost:8000/shares/$SHARE_TOKEN")"
    check "share_download_2" "$(curl -s "http://localhost:8000/shares/$SHARE_TOKEN")"
    check "share_download_3_exhausted" "$(curl -s "http://localhost:8000/shares/$SHARE_TOKEN")"
  fi

  # ── Delete file ─────────────────────────────────────────────────────────────
  check "delete_file" "$(curl -s -X DELETE "http://localhost:8000/files/$FILE_ID" -H "Authorization: Bearer $TOKEN")"
fi

# ── Audit events ──────────────────────────────────────────────────────────────
check "audit_events" "$(curl -s "http://localhost:8000/audit/events" -H "Authorization: Bearer $TOKEN")"

# ── Audit chain verify ────────────────────────────────────────────────────────
check "audit_verify" "$(curl -s "http://localhost:8000/audit/verify" -H "Authorization: Bearer $TOKEN")"

# ── Alerts ────────────────────────────────────────────────────────────────────
check "alerts" "$(curl -s "http://localhost:8000/alerts" -H "Authorization: Bearer $TOKEN")"

# ── Token refresh ─────────────────────────────────────────────────────────────
check "refresh" "$(curl -s -X POST "http://localhost:8000/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}")"

# ── Logout ────────────────────────────────────────────────────────────────────
check "logout" "$(curl -s -X POST "http://localhost:8000/logout" -H "Authorization: Bearer $TOKEN")"

# ── Token revoked after logout ────────────────────────────────────────────────
check "token_revoked_after_logout" "$(curl -s "http://localhost:8000/me" -H "Authorization: Bearer $TOKEN")"

echo "=== ALL TESTS DONE ===" >> $OUT

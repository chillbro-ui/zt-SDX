#!/bin/bash
OUT=".kiro_tmp/fulltest.txt"
echo "" > $OUT

check() {
  echo "=== $1 ===" >> $OUT
  echo "$2" >> $OUT
  echo "" >> $OUT
}

fail() {
  echo "=== FAIL: $1 ===" >> $OUT
  echo "$2" >> $OUT
  echo "" >> $OUT
}

sleep 4  # wait for services to be ready

EMAIL="test_$(date +%s)@acme.com"
check "test_email" "$EMAIL"

# ── Health ────────────────────────────────────────────────────────────────────
check "health_gateway"  "$(curl -s http://localhost:8000/)"
check "health_auth"     "$(curl -s http://localhost:8001/)"
check "health_policy"   "$(curl -s http://localhost:8002/)"
check "health_file"     "$(curl -s http://localhost:8003/)"
check "health_audit"    "$(curl -s http://localhost:8004/)"
check "health_risk"     "$(curl -s http://localhost:8005/)"
check "health_alert"    "$(curl -s http://localhost:8006/)"

# ── Seed policies ─────────────────────────────────────────────────────────────
check "seed_policies" "$(curl -s -X POST http://localhost:8002/policy/seed)"

# ── Register SUPER_ADMIN ──────────────────────────────────────────────────────
ADMIN_EMAIL="admin_$(date +%s)@acme.com"
check "register_admin" "$(curl -s -X POST "http://localhost:8001/auth/register?email=${ADMIN_EMAIL}&password=Admin123!&role=SUPER_ADMIN&department=security")"

# ── Register EMPLOYEE ─────────────────────────────────────────────────────────
check "register_employee" "$(curl -s -X POST "http://localhost:8001/auth/register?email=${EMAIL}&password=Test1234!&role=EMPLOYEE&department=Engineering")"

# ── Login as EMPLOYEE ─────────────────────────────────────────────────────────
LOGIN=$(curl -s -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"Test1234!\"}")
check "login_employee" "$LOGIN"

TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','MISSING'))" 2>/dev/null)
REFRESH=$(echo "$LOGIN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('refresh_token','MISSING'))" 2>/dev/null)

if [ "$TOKEN" = "MISSING" ] || [ -z "$TOKEN" ]; then
  fail "login_failed" "$LOGIN"
  echo "ABORT: login failed" >> $OUT
  exit 1
fi

# ── Get /me ───────────────────────────────────────────────────────────────────
check "me" "$(curl -s http://localhost:8000/me -H "Authorization: Bearer $TOKEN")"

# ── Rate limit test (login) ───────────────────────────────────────────────────
check "rate_limit_login" "$(for i in 1 2 3 4 5 6 7 8 9 10 11; do curl -s -X POST http://localhost:8000/login -H 'Content-Type: application/json' -d '{"email":"x@x.com","password":"x"}'; done | tail -c 200)"

# ── Upload INTERNAL file (EMPLOYEE allowed) ───────────────────────────────────
echo "Test document for ZT-SDX" > /tmp/test_internal.pdf
UPLOAD_OK=$(curl -s -X POST "http://localhost:8000/upload?sensitivity=INTERNAL" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_internal.pdf")
check "upload_internal_allowed" "$UPLOAD_OK"

FILE_ID=$(echo "$UPLOAD_OK" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file',{}).get('id','MISSING'))" 2>/dev/null)

# ── Upload CONFIDENTIAL file (EMPLOYEE should be DENIED) ─────────────────────
echo "Confidential doc" > /tmp/test_conf.pdf
check "upload_confidential_denied" "$(curl -s -X POST "http://localhost:8000/upload?sensitivity=CONFIDENTIAL" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_conf.pdf")"

# ── Upload SECRET file (EMPLOYEE should be DENIED) ───────────────────────────
echo "Secret doc" > /tmp/test_secret.pdf
check "upload_secret_denied" "$(curl -s -X POST "http://localhost:8000/upload?sensitivity=SECRET" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_secret.pdf")"

# ── Login as SUPER_ADMIN ──────────────────────────────────────────────────────
ADMIN_LOGIN=$(curl -s -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"Admin123!\"}")
check "login_admin" "$ADMIN_LOGIN"
ADMIN_TOKEN=$(echo "$ADMIN_LOGIN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','MISSING'))" 2>/dev/null)

# ── Upload SECRET file (SUPER_ADMIN allowed) ──────────────────────────────────
echo "Top secret doc" > /tmp/test_secret2.pdf
check "upload_secret_admin_allowed" "$(curl -s -X POST "http://localhost:8000/upload?sensitivity=SECRET" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -F "file=@/tmp/test_secret2.pdf")"

# ── Wait for worker DLP scan ──────────────────────────────────────────────────
echo "Waiting 6s for DLP scan..." >> $OUT
sleep 6

# ── File status after scan ────────────────────────────────────────────────────
if [ "$FILE_ID" != "MISSING" ] && [ -n "$FILE_ID" ]; then
  check "file_after_scan" "$(curl -s "http://localhost:8000/files/$FILE_ID" -H "Authorization: Bearer $TOKEN")"

  # ── Download (decrypted) ──────────────────────────────────────────────────
  DL=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "http://localhost:8000/files/$FILE_ID/download" -H "Authorization: Bearer $TOKEN")
  check "download_file" "$DL"

  # ── Create share ──────────────────────────────────────────────────────────
  SHARE=$(curl -s -X POST "http://localhost:8000/shares" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"file_id\":\"$FILE_ID\",\"recipient_email\":\"vendor@ext.com\",\"expiry_hours\":1,\"max_downloads\":2,\"watermark\":true}")
  check "create_share" "$SHARE"

  SHARE_TOKEN=$(echo "$SHARE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('share_token','MISSING'))" 2>/dev/null)

  if [ "$SHARE_TOKEN" != "MISSING" ] && [ -n "$SHARE_TOKEN" ]; then
    # ── Share download 1 ────────────────────────────────────────────────────
    SDL1=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "http://localhost:8000/shares/$SHARE_TOKEN")
    check "share_download_1" "$SDL1"
    # ── Share download 2 ────────────────────────────────────────────────────
    SDL2=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "http://localhost:8000/shares/$SHARE_TOKEN")
    check "share_download_2" "$SDL2"
    # ── Share download 3 (exhausted) ────────────────────────────────────────
    check "share_download_3_exhausted" "$(curl -s "http://localhost:8000/shares/$SHARE_TOKEN")"
  fi

  # ── Delete file ──────────────────────────────────────────────────────────
  check "delete_file" "$(curl -s -X DELETE "http://localhost:8000/files/$FILE_ID" -H "Authorization: Bearer $TOKEN")"
fi

# ── Audit events (EMPLOYEE should be DENIED) ─────────────────────────────────
check "audit_events_employee_denied" "$(curl -s "http://localhost:8000/audit/events" -H "Authorization: Bearer $TOKEN")"

# ── Audit events (SUPER_ADMIN allowed) ───────────────────────────────────────
check "audit_events_admin" "$(curl -s "http://localhost:8000/audit/events" -H "Authorization: Bearer $ADMIN_TOKEN")"

# ── Audit chain verify ────────────────────────────────────────────────────────
check "audit_verify" "$(curl -s "http://localhost:8000/audit/verify" -H "Authorization: Bearer $ADMIN_TOKEN")"

# ── Alerts (EMPLOYEE denied) ──────────────────────────────────────────────────
check "alerts_employee_denied" "$(curl -s "http://localhost:8000/alerts" -H "Authorization: Bearer $TOKEN")"

# ── Alerts (SUPER_ADMIN allowed) ─────────────────────────────────────────────
check "alerts_admin" "$(curl -s "http://localhost:8000/alerts" -H "Authorization: Bearer $ADMIN_TOKEN")"

# ── Org create (EMPLOYEE denied) ─────────────────────────────────────────────
check "org_create_employee_denied" "$(curl -s -X POST "http://localhost:8000/orgs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Org","domain":"test.com"}')"

# ── Org create (SUPER_ADMIN allowed) ─────────────────────────────────────────
ORG=$(curl -s -X POST "http://localhost:8000/orgs" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Acme Corp","domain":"acme-test.com","country":"IN"}')
check "org_create_admin" "$ORG"
ORG_ID=$(echo "$ORG" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id','MISSING'))" 2>/dev/null)

# ── List departments ──────────────────────────────────────────────────────────
if [ "$ORG_ID" != "MISSING" ] && [ -n "$ORG_ID" ]; then
  check "list_departments" "$(curl -s "http://localhost:8000/orgs/$ORG_ID/departments" -H "Authorization: Bearer $ADMIN_TOKEN")"
fi

# ── Token refresh ─────────────────────────────────────────────────────────────
check "token_refresh" "$(curl -s -X POST "http://localhost:8000/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH\"}")"

# ── Login lockout test ────────────────────────────────────────────────────────
LOCK_EMAIL="locktest_$(date +%s)@acme.com"
curl -s -X POST "http://localhost:8001/auth/register?email=${LOCK_EMAIL}&password=Correct1!&role=EMPLOYEE&department=Engineering" > /dev/null
for i in 1 2 3 4 5; do
  curl -s -X POST "http://localhost:8000/login" -H "Content-Type: application/json" \
    -d "{\"email\":\"${LOCK_EMAIL}\",\"password\":\"WrongPass\"}" > /dev/null
done
check "lockout_after_5_attempts" "$(curl -s -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${LOCK_EMAIL}\",\"password\":\"Correct1!\"}")"

# ── Logout ────────────────────────────────────────────────────────────────────
check "logout" "$(curl -s -X POST "http://localhost:8000/logout" -H "Authorization: Bearer $TOKEN")"

# ── Token revoked after logout ────────────────────────────────────────────────
check "token_revoked" "$(curl -s "http://localhost:8000/me" -H "Authorization: Bearer $TOKEN")"

echo "=== ALL TESTS COMPLETE ===" >> $OUT

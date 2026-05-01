#!/bin/bash
OUT=".kiro_tmp/fulltest.txt"
echo "" > $OUT

check() {
  echo "=== $1 ===" >> $OUT
  echo "$2" >> $OUT
  echo "" >> $OUT
}

sleep 4

EMAIL="test_$(date +%s)@acme.com"
ADMIN_EMAIL="admin_$(date +%s)@acme.com"
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

# ── Register both users ───────────────────────────────────────────────────────
check "register_admin"    "$(curl -s -X POST "http://localhost:8001/auth/register?email=${ADMIN_EMAIL}&password=Admin123!&role=SUPER_ADMIN&department=security")"
check "register_employee" "$(curl -s -X POST "http://localhost:8001/auth/register?email=${EMAIL}&password=Test1234!&role=EMPLOYEE&department=Engineering")"

# ── Login EMPLOYEE ────────────────────────────────────────────────────────────
LOGIN=$(curl -s -X POST "http://localhost:8000/login" -H "Content-Type: application/json" -d "{\"email\":\"${EMAIL}\",\"password\":\"Test1234!\"}")
check "login_employee" "$LOGIN"
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','MISSING'))" 2>/dev/null)
REFRESH=$(echo "$LOGIN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('refresh_token','MISSING'))" 2>/dev/null)
[ "$TOKEN" = "MISSING" ] && { echo "ABORT: employee login failed" >> $OUT; exit 1; }

# ── Login SUPER_ADMIN ─────────────────────────────────────────────────────────
ADMIN_LOGIN=$(curl -s -X POST "http://localhost:8000/login" -H "Content-Type: application/json" -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"Admin123!\"}")
check "login_admin" "$ADMIN_LOGIN"
ADMIN_TOKEN=$(echo "$ADMIN_LOGIN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','MISSING'))" 2>/dev/null)
[ "$ADMIN_TOKEN" = "MISSING" ] && { echo "ABORT: admin login failed" >> $OUT; exit 1; }

# ── /me ───────────────────────────────────────────────────────────────────────
check "me_employee" "$(curl -s http://localhost:8000/me -H "Authorization: Bearer $TOKEN")"

# ── Upload permissions ────────────────────────────────────────────────────────
echo "Test document for ZT-SDX" > /tmp/test.pdf
check "upload_internal_employee_ALLOW"      "$(curl -s -X POST "http://localhost:8000/upload?sensitivity=INTERNAL"      -H "Authorization: Bearer $TOKEN"       -F "file=@/tmp/test.pdf")"
check "upload_confidential_employee_DENY"   "$(curl -s -X POST "http://localhost:8000/upload?sensitivity=CONFIDENTIAL"  -H "Authorization: Bearer $TOKEN"       -F "file=@/tmp/test.pdf")"
check "upload_secret_employee_DENY"         "$(curl -s -X POST "http://localhost:8000/upload?sensitivity=SECRET"        -H "Authorization: Bearer $TOKEN"       -F "file=@/tmp/test.pdf")"
check "upload_secret_admin_ALLOW"           "$(curl -s -X POST "http://localhost:8000/upload?sensitivity=SECRET"        -H "Authorization: Bearer $ADMIN_TOKEN" -F "file=@/tmp/test.pdf")"

FILE_ID=$(curl -s -X POST "http://localhost:8000/upload?sensitivity=INTERNAL" -H "Authorization: Bearer $TOKEN" -F "file=@/tmp/test.pdf" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file',{}).get('id','MISSING'))" 2>/dev/null)
check "file_id" "$FILE_ID"

# ── Wait for DLP scan ─────────────────────────────────────────────────────────
echo "Waiting 6s for DLP scan..." >> $OUT
sleep 6

if [ "$FILE_ID" != "MISSING" ] && [ -n "$FILE_ID" ]; then
  check "file_after_scan"  "$(curl -s "http://localhost:8000/files/$FILE_ID" -H "Authorization: Bearer $TOKEN")"
  check "list_files"       "$(curl -s "http://localhost:8000/files"          -H "Authorization: Bearer $TOKEN")"
  check "download_file"    "$(curl -s -w '\nHTTP:%{http_code}' "http://localhost:8000/files/$FILE_ID/download" -H "Authorization: Bearer $TOKEN")"

  SHARE=$(curl -s -X POST "http://localhost:8000/shares" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d "{\"file_id\":\"$FILE_ID\",\"recipient_email\":\"vendor@ext.com\",\"expiry_hours\":1,\"max_downloads\":2,\"watermark\":true}")
  check "create_share" "$SHARE"
  SHARE_TOKEN=$(echo "$SHARE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('share_token','MISSING'))" 2>/dev/null)

  if [ "$SHARE_TOKEN" != "MISSING" ] && [ -n "$SHARE_TOKEN" ]; then
    check "share_dl_1"         "$(curl -s -w '\nHTTP:%{http_code}' "http://localhost:8000/shares/$SHARE_TOKEN")"
    check "share_dl_2"         "$(curl -s -w '\nHTTP:%{http_code}' "http://localhost:8000/shares/$SHARE_TOKEN")"
    check "share_dl_3_exhaust" "$(curl -s "http://localhost:8000/shares/$SHARE_TOKEN")"
  fi

  check "delete_file" "$(curl -s -X DELETE "http://localhost:8000/files/$FILE_ID" -H "Authorization: Bearer $TOKEN")"
fi

# ── Role enforcement ──────────────────────────────────────────────────────────
check "audit_events_employee_DENY"  "$(curl -s "http://localhost:8000/audit/events" -H "Authorization: Bearer $TOKEN")"
check "audit_events_admin_ALLOW"    "$(curl -s "http://localhost:8000/audit/events" -H "Authorization: Bearer $ADMIN_TOKEN")"
check "audit_verify_admin_ALLOW"    "$(curl -s "http://localhost:8000/audit/verify" -H "Authorization: Bearer $ADMIN_TOKEN")"
check "alerts_employee_DENY"        "$(curl -s "http://localhost:8000/alerts"       -H "Authorization: Bearer $TOKEN")"
check "alerts_admin_ALLOW"          "$(curl -s "http://localhost:8000/alerts"       -H "Authorization: Bearer $ADMIN_TOKEN")"
check "org_create_employee_DENY"    "$(curl -s -X POST "http://localhost:8000/orgs" -H "Authorization: Bearer $TOKEN"       -H "Content-Type: application/json" -d '{"name":"X","domain":"x.com"}')"
ORG=$(curl -s -X POST "http://localhost:8000/orgs" -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{"name":"Acme Corp","domain":"acme-test2.com","country":"IN"}')
check "org_create_admin_ALLOW"      "$ORG"
ORG_ID=$(echo "$ORG" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id','MISSING'))" 2>/dev/null)
[ "$ORG_ID" != "MISSING" ] && check "list_departments" "$(curl -s "http://localhost:8000/orgs/$ORG_ID/departments" -H "Authorization: Bearer $ADMIN_TOKEN")"

# ── Token refresh ─────────────────────────────────────────────────────────────
check "token_refresh" "$(curl -s -X POST "http://localhost:8000/refresh" -H "Content-Type: application/json" -d "{\"refresh_token\":\"$REFRESH\"}")"

# ── Login lockout (5 wrong attempts → account suspended) ─────────────────────
LOCK_EMAIL="lock_$(date +%s)@acme.com"
curl -s -X POST "http://localhost:8001/auth/register?email=${LOCK_EMAIL}&password=Correct1!&role=EMPLOYEE&department=Engineering" > /dev/null
for i in 1 2 3 4 5; do
  curl -s -X POST "http://localhost:8000/login" -H "Content-Type: application/json" -d "{\"email\":\"${LOCK_EMAIL}\",\"password\":\"WrongPass\"}" > /dev/null
done
check "lockout_correct_pass_blocked" "$(curl -s -X POST "http://localhost:8000/login" -H "Content-Type: application/json" -d "{\"email\":\"${LOCK_EMAIL}\",\"password\":\"Correct1!\"}")"

# ── Rate limit test (run LAST so it doesn't block other tests) ────────────────
check "rate_limit_fires_at_11" "$(for i in $(seq 1 11); do curl -s -X POST http://localhost:8000/login -H 'Content-Type: application/json' -d '{"email":"rl@x.com","password":"x"}'; done | python3 -c 'import sys; data=sys.stdin.read(); print("429_FOUND" if "Rate limit exceeded" in data else "NO_RATE_LIMIT")')"

# ── Logout + revocation ───────────────────────────────────────────────────────
check "logout"        "$(curl -s -X POST "http://localhost:8000/logout" -H "Authorization: Bearer $TOKEN")"
check "token_revoked" "$(curl -s "http://localhost:8000/me"             -H "Authorization: Bearer $TOKEN")"

echo "=== ALL TESTS COMPLETE ===" >> $OUT

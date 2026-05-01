#!/bin/bash
set -e
echo "Rebuilding changed services..."

docker compose build auth-service file-service gateway-api policy-service 2>&1 | tail -8

echo "Restarting..."
docker compose up -d auth-service file-service gateway-api policy-service 2>&1 | tail -5

echo "Waiting for services to be ready..."
sleep 6

echo "Health checks..."
curl -s http://localhost:8000/ | python3 -c "import sys,json; d=json.load(sys.stdin); print('gateway:', d['status'])"
curl -s http://localhost:8001/ | python3 -c "import sys,json; d=json.load(sys.stdin); print('auth:', d['status'])"
curl -s http://localhost:8002/ | python3 -c "import sys,json; d=json.load(sys.stdin); print('policy:', d['status'])"
curl -s http://localhost:8003/ | python3 -c "import sys,json; d=json.load(sys.stdin); print('file:', d['status'])"
echo "Done."

from app.core.config import settings

# All service URLs read from environment via settings — never hardcoded
AUTH_URL = settings.AUTH_URL
POLICY_URL = settings.POLICY_URL
FILE_URL = settings.FILE_URL
AUDIT_URL = settings.AUDIT_URL
ALERT_URL = settings.ALERT_URL
RISK_URL = settings.RISK_URL  # Placeholder — risk service owned by another team

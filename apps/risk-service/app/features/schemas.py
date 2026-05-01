from pydantic import BaseModel, Field
from app.core.enums import EventType

class FeatureVector(BaseModel):
    failed_logins_1h: float = 0.0
    failed_logins_24h: float = 0.0
    new_device: float = 0.0
    geo_distance_km: float = 0.0
    rapid_download_count: float = 0.0
    secret_file_accesses: float = 0.0
    denied_attempts: float = 0.0
    device_trust: float = 100.0

class TelemetryEvent(BaseModel):
    event: EventType
    user_id: str
    device_id: str | None = None
    ip: str | None = None
    geo: str | None = None
    sensitivity: str | None = None
    device_trust: float | None = None
    geo_distance_km: float | None = None

    # Device signals
    is_vpn: bool = False
    is_tor: bool = False
    is_vm: bool = False
    is_rooted: bool = False
    is_new_fingerprint: bool = False
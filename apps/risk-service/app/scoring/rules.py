from app.features.schemas import FeatureVector


# ── RULE WEIGHTS ──────────────────────────────────────────────────────────────
# Each rule defines a threshold and how many points to add.
# These are tunable — bump them up/down based on your security posture.

RULES = [

    # ── Auth rules ──────────────────────────────────────────────────────────
    {
        "name": "new_device",
        "description": "Login from a device we haven't seen before",
        "check": lambda v: v.new_device == 1,
        "score": 20,
    },
    {
        "name": "failed_logins_light",
        "description": "3–4 failed logins in the last hour",
        "check": lambda v: 3 <= v.failed_logins_1h < 5,
        "score": 15,
    },
    {
        "name": "failed_logins_medium",
        "description": "5–9 failed logins in the last hour (brute force attempt)",
        "check": lambda v: 5 <= v.failed_logins_1h < 10,
        "score": 25,
    },
    {
        "name": "failed_logins_heavy",
        "description": "10+ failed logins — clear brute force",
        "check": lambda v: v.failed_logins_1h >= 10,
        "score": 40,
    },
    {
        "name": "geo_distance_far",
        "description": "Login from location >1000 km from last known location",
        "check": lambda v: v.geo_distance_km >= 1000,
        "score": 20,
    },
    {
        "name": "impossible_travel",
        "description": "Login from location >5000 km away — physically impossible",
        "check": lambda v: v.geo_distance_km >= 5000,
        "score": 35,  # stacks on top of geo_distance_far
    },

    # ── Device rules ────────────────────────────────────────────────────────
    {
        "name": "low_trust_device",
        "description": "Device trust score below 60 (VPN / rooted / VM)",
        "check": lambda v: v.device_trust < 60,
        "score": 10,
    },
    {
        "name": "very_low_trust_device",
        "description": "Device trust score below 30 (TOR / heavily compromised)",
        "check": lambda v: v.device_trust < 30,
        "score": 20,  # stacks on top of low_trust_device
    },

    # ── File rules ──────────────────────────────────────────────────────────
    {
        "name": "rapid_download_light",
        "description": "5–9 downloads in short window",
        "check": lambda v: 5 <= v.rapid_download_count < 10,
        "score": 15,
    },
    {
        "name": "rapid_download_heavy",
        "description": "10+ downloads in short window — bulk exfiltration risk",
        "check": lambda v: v.rapid_download_count >= 10,
        "score": 35,
    },
    {
        "name": "secret_file_access",
        "description": "Accessed 1–2 SECRET sensitivity files",
        "check": lambda v: 1 <= v.secret_file_accesses < 3,
        "score": 10,
    },
    {
        "name": "secret_file_access_high",
        "description": "Accessed 3+ SECRET sensitivity files",
        "check": lambda v: v.secret_file_accesses >= 3,
        "score": 25,
    },

    # ── Policy rules ────────────────────────────────────────────────────────
    {
        "name": "policy_deny",
        "description": "1–2 policy denials",
        "check": lambda v: 1 <= v.denied_attempts < 3,
        "score": 15,
    },
    {
        "name": "policy_deny_repeated",
        "description": "3+ policy denials — privilege abuse pattern",
        "check": lambda v: v.denied_attempts >= 3,
        "score": 30,
    },
]


class RuleEngine:
    """
    Stage 1 of the scoring pipeline.

    Loops through all rules, checks each one against the feature vector,
    and sums up the score. Returns the total capped at 100, plus a list
    of which rules fired (for explainability / audit trail).
    """

    def score(self, vector: FeatureVector) -> tuple[float, list[dict]]:
        """
        Returns:
            score       - float between 0 and 100
            fired_rules - list of rule dicts that matched (for logging/alerts)
        """
        total = 0.0
        fired = []

        for rule in RULES:
            if rule["check"](vector):
                total += rule["score"]
                fired.append({
                    "name": rule["name"],
                    "description": rule["description"],
                    "score": rule["score"],
                })

        # Cap at 100
        return min(total, 100.0), fired

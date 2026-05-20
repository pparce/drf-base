from rest_framework.throttling import AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    """Stricter throttle for authentication endpoints (login, register, password reset)."""
    scope = "auth"

from ipaddress import ip_address, AddressValueError

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config.settings import settings


def _parse_ip(value: str) -> str | None:
    """Return a normalized IP string, or None if invalid."""
    try:
        return str(ip_address(value.strip()))
    except (AddressValueError, ValueError):
        return None


def _trusted_proxies() -> set[str]:
    """
    MVP setting: comma-separated list of trusted proxy IPs.
    Example env: TRUSTED_PROXY_IPS="10.0.0.5,172.18.0.2"
    If empty, X-Forwarded-For is ignored entirely.
    """
    raw = getattr(settings, "TRUSTED_PROXY_IPS", "") or ""
    if isinstance(raw, str):
        values = [item.strip() for item in raw.split(",") if item.strip()]
    else:
        values = list(raw)

    return {ip for ip in (_parse_ip(v) for v in values) if ip}


def _get_forwarded_client_ip(request: Request) -> str | None:
    """
    Only trust X-Forwarded-For when the direct peer is a configured trusted proxy.
    Walk right-to-left so spoofed left-most values are not trusted blindly.
    """
    direct_ip = request.client.host if request.client else None
    if not direct_ip:
        return None

    direct_ip = _parse_ip(direct_ip)
    trusted = _trusted_proxies()

    if not direct_ip or direct_ip not in trusted:
        return None

    forwarded_for = request.headers.get("x-forwarded-for")
    if not forwarded_for:
        return None

    # XFF is usually: client, proxy1, proxy2
    # Walk from right to left, skipping trusted proxies.
    for raw_ip in reversed(forwarded_for.split(",")):
        parsed_ip = _parse_ip(raw_ip)
        if parsed_ip is None:
            continue
        if parsed_ip in trusted:
            continue
        return parsed_ip

    return None


def get_rate_limit_key(request: Request) -> str:
    """
    Custom key function for rate limiting.
    Priority: Authenticated User ID -> trusted forwarded client IP -> direct client IP.
    """
    # 1. Authenticated user ID
    user = getattr(request.state, "user", None)
    user_id = getattr(user, "id", None)
    if user_id is not None:
        return f"user:{user_id}"

    # 2. Trusted proxy header, only if direct peer is a trusted proxy
    forwarded_ip = _get_forwarded_client_ip(request)
    if forwarded_ip:
        return f"ip:{forwarded_ip}"

    # 3. Direct client IP fallback
    return f"ip:{get_remote_address(request)}"


# MVP: keep fixed-window for simplicity.
# Later: consider moving-window if burst behavior matters.
limiter = Limiter(
    key_func=get_rate_limit_key,
    storage_uri=settings.REDIS_URL,
    default_limits=[settings.RATE_LIMIT_DEFAULT_FALLBACK],
    strategy="fixed-window",
)

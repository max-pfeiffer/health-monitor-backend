import json
import time

import httpx2
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

bearer_scheme = HTTPBearer(auto_error=False)

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


# Keycloak may rotate its signing keys while the app is running, so the JWKS
# must not be cached for the process lifetime.
_JWKS_TTL_SECONDS = 900

_jwks_cache: dict | None = None
_jwks_fetched_at: float = 0.0


def _fetch_jwks() -> dict:
    if settings.keycloak_jwks_json:
        return json.loads(settings.keycloak_jwks_json)
    url = (
        f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"
        "/protocol/openid-connect/certs"
    )
    with httpx2.Client() as client:
        resp = client.get(url, timeout=10.0)
        resp.raise_for_status()
        return resp.json()


def _get_jwks(force_refresh: bool = False) -> dict:
    global _jwks_cache, _jwks_fetched_at
    if (
        force_refresh
        or _jwks_cache is None
        or time.monotonic() - _jwks_fetched_at > _JWKS_TTL_SECONDS
    ):
        _jwks_cache = _fetch_jwks()
        _jwks_fetched_at = time.monotonic()
    return _jwks_cache


def _get_signing_jwks(token: str) -> dict:
    jwks = _get_jwks()
    kid = jwt.get_unverified_header(token).get("kid")
    if kid is not None and not any(
        key.get("kid") == kid for key in jwks.get("keys", [])
    ):
        # Unknown key id: the keys may have just rotated, refresh once.
        jwks = _get_jwks(force_refresh=True)
    return jwks


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise _credentials_exception
    try:
        payload = jwt.decode(
            credentials.credentials,
            _get_signing_jwks(credentials.credentials),
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise _credentials_exception
        return user_id
    except JWTError:
        raise _credentials_exception

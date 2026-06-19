import json
from functools import lru_cache

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


@lru_cache(maxsize=1)
def _get_jwks() -> dict:
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


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise _credentials_exception
    try:
        payload = jwt.decode(
            credentials.credentials,
            _get_jwks(),
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise _credentials_exception
        return user_id
    except JWTError:
        raise _credentials_exception

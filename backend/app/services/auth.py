from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Header, HTTPException

from ..config import get_settings


@dataclass
class AuthenticatedUser:
    id: str
    name: str


@lru_cache
def _jwks_client() -> jwt.PyJWKClient:
    settings = get_settings()
    url = settings.supabase_jwks_url or f'{settings.supabase_url.rstrip("/")}/auth/v1/.well-known/jwks.json'
    return jwt.PyJWKClient(url, cache_keys=True, lifespan=3600)


def require_user(authorization: str | None = Header(default=None)) -> AuthenticatedUser:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Authentication required')
    token = authorization.removeprefix('Bearer ').strip()
    settings = get_settings()
    if settings.app_env == 'development' and token == 'dev-token':
        return AuthenticatedUser(id='demo-user', name='Demo Contributor')
    if not settings.supabase_url:
        raise HTTPException(status_code=401, detail='Authentication is not configured')
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=['RS256', 'ES256'],
            audience=settings.supabase_jwt_audience,
            issuer=f'{settings.supabase_url.rstrip("/")}/auth/v1',
        )
        metadata = claims.get('user_metadata') or {}
        name = metadata.get('name') or claims.get('email') or 'Contributor'
        return AuthenticatedUser(id=claims['sub'], name=name)
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=401, detail='Invalid authentication token') from exc

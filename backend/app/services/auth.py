from dataclasses import dataclass

from fastapi import Header, HTTPException

from ..config import get_settings


@dataclass
class AuthenticatedUser:
    id: str
    name: str


def require_user(authorization: str | None = Header(default=None)) -> AuthenticatedUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.removeprefix("Bearer ").strip()
    if get_settings().app_env == "development" and token == "dev-token":
        return AuthenticatedUser(id="demo-user", name="Demo Contributor")
    try:
        import firebase_admin
        from firebase_admin import auth
        if not firebase_admin._apps:
            firebase_admin.initialize_app(options={"projectId": get_settings().firebase_project_id})
        claims = auth.verify_id_token(token)
        return AuthenticatedUser(id=claims["uid"], name=claims.get("name") or claims.get("email") or "Contributor")
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc

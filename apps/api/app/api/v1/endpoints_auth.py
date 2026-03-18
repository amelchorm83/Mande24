from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import enforce_rate_limit, resolve_client_identifier
from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.core.user_roles import ensure_user_roles, get_user_roles_sorted
from app.db.models import User, UserRole
from app.db.session import get_db
from app.models.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> UserResponse:
    email = payload.email.strip().lower()
    identifier = resolve_client_identifier(request, extra=email)
    enforce_rate_limit(
        "auth:register",
        identifier,
        limit=settings.auth_register_rate_limit,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.flush()
    roles_payload = payload.roles or [payload.role]
    desired_roles: list[UserRole] = []
    for item in [payload.role, *roles_payload]:
        if item not in desired_roles:
            desired_roles.append(item)
    ensure_user_roles(db, user, desired_roles)
    db.commit()
    db.refresh(user)
    role_values = get_user_roles_sorted(user)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        roles=[UserRole(item) for item in role_values],
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.strip().lower()
    identifier = resolve_client_identifier(request, extra=email)
    enforce_rate_limit(
        "auth:login",
        identifier,
        limit=settings.auth_login_rate_limit,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")

    token = create_access_token(subject=user.id, role=user.role.value, roles=get_user_roles_sorted(user))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    role_values = get_user_roles_sorted(user)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        roles=[UserRole(item) for item in role_values],
    )

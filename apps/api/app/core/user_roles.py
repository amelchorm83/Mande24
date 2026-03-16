from sqlalchemy.orm import Session

from app.db.models import User, UserRole, UserRoleLink


ROLE_PRIORITY = [UserRole.admin, UserRole.station, UserRole.rider, UserRole.client]


def get_user_role_values(user: User) -> set[str]:
    roles = {user.role.value}
    for link in getattr(user, "role_links", []) or []:
        roles.add(link.role.value)
    return roles


def get_user_roles_sorted(user: User) -> list[str]:
    values = get_user_role_values(user)
    ordered = [role.value for role in ROLE_PRIORITY if role.value in values]
    extras = sorted(values - set(ordered))
    return ordered + extras


def user_has_role(user: User, role: UserRole) -> bool:
    return role.value in get_user_role_values(user)


def user_has_any_role(user: User, allowed: set[str]) -> bool:
    return bool(get_user_role_values(user).intersection(allowed))


def ensure_user_roles(
    db: Session,
    user: User,
    roles: list[UserRole],
    *,
    replace_existing: bool = False,
) -> None:
    desired = {item.value for item in roles}
    existing_links = db.query(UserRoleLink).filter(UserRoleLink.user_id == user.id).all()
    existing = {item.role.value for item in existing_links}

    if replace_existing:
        for link in existing_links:
            if link.role.value not in desired:
                db.delete(link)

    missing = desired - existing
    for value in missing:
        db.add(UserRoleLink(user_id=user.id, role=UserRole(value)))

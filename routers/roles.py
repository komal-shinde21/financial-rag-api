from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.role import RoleCreate, RoleOut, AssignRole, RolePermissionsOut
from services import role_service
from utils.security import require_permission

router = APIRouter(tags=["Roles & Permissions"])


@router.post("/roles/create", response_model=RoleOut, status_code=201)
def create_role(
    data: RoleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("all")),  # Admin only
):
    """Create a new role. Admin only."""
    return role_service.create_role(data, db)


@router.post("/users/assign-role")
def assign_role(
    data: AssignRole,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("all")),  # Admin only
):
    """Assign a role to a user. Admin only."""
    user = role_service.assign_role(data.user_id, data.role_name, db)
    return {
        "message": f"Role '{data.role_name}' assigned to user '{user.username}'",
        "user_id": user.id,
        "roles": [r.name for r in user.roles],
    }


@router.get("/users/{user_id}/roles")
def get_user_roles(
    user_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("view")),
):
    """Get all roles assigned to a user."""
    user = role_service.get_user_roles(user_id, db)
    return {"user_id": user.id, "username": user.username, "roles": [r.name for r in user.roles]}


@router.get("/users/{user_id}/permissions", response_model=RolePermissionsOut)
def get_user_permissions(
    user_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("view")),
):
    """View all permissions a user has (derived from their roles)."""
    user = role_service.get_user_roles(user_id, db)
    return RolePermissionsOut(
        user_id=user.id,
        username=user.username,
        roles=[r.name for r in user.roles],
        permissions=user.permissions,
    )

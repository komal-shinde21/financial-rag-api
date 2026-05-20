from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.user import Role, User
from schemas.role import RoleCreate


def create_role(data: RoleCreate, db: Session) -> Role:
    if db.query(Role).filter(Role.name == data.name).first():
        raise HTTPException(status_code=400, detail=f"Role '{data.name}' already exists")

    role = Role(
        name=data.name,
        description=data.description,
        permissions=",".join(data.permissions),
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def assign_role(user_id: str, role_name: str, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{role_name}' not found")

    if role not in user.roles:
        user.roles.append(role)
        db.commit()
        db.refresh(user)

    return user


def get_user_roles(user_id: str, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

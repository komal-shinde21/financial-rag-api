from pydantic import BaseModel
from datetime import datetime


class RoleCreate(BaseModel):
    name: str
    description: str | None = None
    permissions: list[str]       # e.g. ["upload", "edit", "delete"]


class RoleOut(BaseModel):
    id: str
    name: str
    description: str | None
    permissions: str             # stored as comma-separated string
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignRole(BaseModel):
    user_id: str
    role_name: str


class RolePermissionsOut(BaseModel):
    user_id: str
    username: str
    roles: list[str]
    permissions: list[str]

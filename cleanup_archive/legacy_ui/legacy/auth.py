from enum import Enum
from fastapi import HTTPException

# Define user roles using Enum
class Role(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

# Function to verify user role
def verify_user(user_role: Role, required_role: Role):
    if user_role == required_role or user_role == Role.ADMIN:
        return True
    else:
        raise HTTPException(status_code=403, detail="Insufficient permissions.")

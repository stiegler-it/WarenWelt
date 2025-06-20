from pydantic import BaseModel, EmailStr
from typing import Optional

# Role Schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleRead(RoleBase):
    id: int

    class Config:
        from_attributes = True # Pydantic V2, formerly orm_mode = True

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str
    role_id: int

class UserRead(UserBase):
    id: int
    role: RoleRead # Nested Role information

    class Config:
        from_attributes = True

class UserInDB(UserBase): # Potentially include hashed_password if needed internally
    id: int
    hashed_password: str
    role_id: int

    class Config:
        from_attributes = True


# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

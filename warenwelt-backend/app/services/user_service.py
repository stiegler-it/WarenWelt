from sqlalchemy.orm import Session
from typing import Optional

from app.models.user_model import User, Role
from app.schemas.user_schema import UserCreate, RoleCreate # RoleCreate might be used for initial setup
from app.models.user_model import pwd_context # For password hashing

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = User.hash_password(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role_id=user.role_id,
        is_active=user.is_active if user.is_active is not None else True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    return db.query(Role).filter(Role.name == name).first()

def create_role(db: Session, role: RoleCreate) -> Role:
    db_role = Role(name=role.name, description=role.description)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

# Placeholder for initial role creation if needed by other modules
def get_or_create_role(db: Session, role_name: str, role_description: Optional[str] = None) -> Role:
    db_role = get_role_by_name(db, name=role_name)
    if not db_role:
        role_in = RoleCreate(name=role_name, description=role_description)
        db_role = create_role(db, role=role_in)
    return db_role

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not user.verify_password(password):
        return None
    return user

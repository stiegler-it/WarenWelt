from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core import security
from app.services import user_service
from app.schemas import user_schema, token_schema # Assuming token_schema will be created or merged
from app.db.session import get_db
from app.core.config import settings

router = APIRouter()

@router.post("/login", response_model=user_schema.Token)
async def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = user_service.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=user_schema.UserRead)
async def read_users_me(current_user: user_schema.UserRead = Depends(security.get_current_active_user)):
    # FastAPI Depends will convert the DB model (UserModel) to UserRead schema
    return current_user

# Placeholder for a user creation endpoint (maybe admin only)
# @router.post("/users/", response_model=user_schema.UserRead, status_code=status.HTTP_201_CREATED)
# def create_user_endpoint(
#     *,
#     db: Session = Depends(get_db),
#     user_in: user_schema.UserCreate,
#     # current_user: models.User = Depends(security.get_current_active_superuser) # Example of admin protection
# ):
#     db_user = user_service.get_user_by_email(db, email=user_in.email)
#     if db_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email already registered",
#         )
#     # For MVP, let's assume role "Mitarbeiter" (employee) exists with ID 2, Admin with ID 1
#     # This should be handled more robustly, e.g. by fetching role by name
#     # Ensure roles are created (e.g. via initial data script)
#     # default_role_id = 2 # Example: Mitarbeiter
#     # user_in.role_id = user_in.role_id if user_in.role_id else default_role_id
#
#     # Ensure role exists
#     role = db.query(user_model.Role).filter(user_model.Role.id == user_in.role_id).first()
#     if not role:
#         raise HTTPException(status_code=400, detail=f"Role with ID {user_in.role_id} not found.")
#
#     created_user = user_service.create_user(db=db, user=user_in)
#     return created_user

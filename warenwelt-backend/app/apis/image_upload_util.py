import shutil
import uuid
from pathlib import Path
from fastapi import HTTPException, status, UploadFile

# Define the upload directory relative to the application root
UPLOAD_DIR = Path("static") / "product_images"
# Ensure the upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]

def save_upload_file(upload_file: UploadFile) -> str:
    if not upload_file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded.")

    if upload_file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"File size exceeds limit of {MAX_FILE_SIZE / (1024*1024)}MB.")

    if upload_file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"Unsupported file type. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}")

    try:
        # Generate a unique filename to prevent overwrites and handle non-ASCII characters
        file_extension = Path(upload_file.filename).suffix
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        # Return the relative path to be stored in DB (e.g., "product_images/xxxxxxxx.jpg")
        # The StaticFiles mount will handle the "static/" part of the URL
        return str(Path("product_images") / unique_filename)

    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {str(e)}")
    finally:
        upload_file.file.close()

def remove_file(relative_path: str) -> bool:
    """Removes a file given its relative path from UPLOAD_DIR's parent (static)."""
    if not relative_path:
        return False

    # Construct the full path from the application root static directory
    full_path = Path("static") / relative_path
    try:
        if full_path.is_file():
            full_path.unlink()
            return True
    except Exception as e:
        # Log error (e.g., permission denied)
        # print(f"Error deleting file {full_path}: {e}")
        return False
    return False

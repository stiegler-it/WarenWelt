from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def read_pos_stub():
    return {"message": "This is a stub for the Point of Sale (POS) endpoints."}

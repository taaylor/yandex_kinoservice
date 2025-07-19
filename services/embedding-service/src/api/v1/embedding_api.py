from fastapi import APIRouter

router = APIRouter()


@router.get(path="")
async def fetch_embedding():
    return "OK"

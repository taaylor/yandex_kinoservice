from fastapi import APIRouter

router = APIRouter()


@router.get(path="")
async def test() -> str:
    return "Succsess"

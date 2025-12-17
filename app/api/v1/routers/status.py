from fastapi import APIRouter

router = APIRouter(
    prefix="/statuses",
    tags=["status"],
)
@router.get("")
def list_statuses():
    return [{"code":"lost"}, {"code":"found"}, {"code":"returned"}]

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.post("/logout")
async def logout(request: Request):
    del request.session["user"]
    return RedirectResponse(url="/login", status_code=303)
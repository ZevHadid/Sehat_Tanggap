from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

async def unauthorized_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return RedirectResponse(url="/login")
    return await request.app.default_exception_handler(request, exc)

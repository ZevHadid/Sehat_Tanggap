from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database import get_db_connection
from auth import check_session

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, session: dict = Depends(check_session)):

    nis = session.get("nis")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT nama, kelas, tel FROM siswa WHERE nis = %s"
        cursor.execute(query, (nis,))
        nama, kelas, tel = cursor.fetchone()

    finally:
        cursor.close()

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "title": "Profile",
        "username": nama,
        "nis": nis,
        "kelas": kelas,
        "tel": tel
    })
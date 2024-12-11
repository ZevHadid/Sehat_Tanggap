from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import timedelta, datetime
import bcrypt

from database import get_db_connection
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(request: Request, username_entered: int = Form(...), password_entered: str = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT nis, password FROM petugas_pmr WHERE nis = %s"
        cursor.execute(query, (username_entered,))
        result = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    if result is None:
        return RedirectResponse(url="/login", status_code=303)

    correct_password_hash = result[1]

    if bcrypt.checkpw(password_entered.encode('utf-8'), correct_password_hash.encode('utf-8')):
        session_data = {
            "nis": username_entered,
            "expires_at": (datetime.now() + timedelta(minutes=1440)).isoformat()
        }
        request.session["user"] = session_data
        return RedirectResponse(url="/dashboard", status_code=303)
    else:
        return RedirectResponse(url="/login", status_code=303)

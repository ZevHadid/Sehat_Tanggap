from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import timedelta

from database import get_db_connection
from auth import check_session

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/jadwal-penjaga", response_class=HTMLResponse)
async def jadwal_penjaga(request: Request, session: dict = Depends(check_session)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to select all rows
        query = "SELECT nis, hari, waktu_mulai, waktu_selesai FROM petugas_pmr"
        cursor.execute(query)
        result = cursor.fetchall()

        petugas_pmr = []
        for row in result:
            row = list(row)
            row[1] = str(row[1])
            
            if isinstance(row[2], timedelta):
                total_seconds = int(row[2].total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                row[2] = f"{hours:02}:{minutes:02}"

            if isinstance(row[3], timedelta):
                total_seconds = int(row[3].total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                row[3] = f"{hours:02}:{minutes:02}"
            
            query = "SELECT nama FROM siswa WHERE nis = %s"
            cursor.execute(query, (row[0],))
            nama = cursor.fetchone()[0]

            row.append(nama)
            petugas_pmr.append(row)

    finally:
        cursor.close()
        conn.close()

    # Pass the result to the template
    return templates.TemplateResponse("jadwal_penjaga.html", {
        "request": request,
        "title": "Jadwal Penjaga",
        "petugas_pmr": petugas_pmr
    })

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import timedelta, datetime, date

from database import get_db_connection
from auth import check_session
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return RedirectResponse(url="/dashboard")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, session: dict = Depends(check_session)):
    waktu_sekarang = datetime.now().strftime('%H:%M:%S')
    nama_hari = ['senin', 'selasa', 'rabu', 'kamis', 'jumat', 'sabtu', 'minggu']
    hari = nama_hari[datetime.now().weekday()]
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT COUNT(DISTINCT nis) AS unique_count FROM pasien WHERE tanggal >= %s AND tanggal < %s"
        cursor.execute(query, (start_of_day, end_of_day))
        jumlah_pasien_hari_ini = cursor.fetchone()[0]

        query = "SELECT COUNT(nis) FROM petugas_pmr WHERE hari = %s AND waktu_mulai <= %s AND waktu_selesai > %s"
        cursor.execute(query, (hari, waktu_sekarang, waktu_sekarang))
        jumlah_petugas_hari_ini = cursor.fetchone()[0]

        query = "SELECT nis, keluhan FROM pasien ORDER BY tanggal DESC LIMIT 4"
        cursor.execute(query)
        data_pasien = [list(row) for row in cursor.fetchall()]

        cursor.execute("SELECT SUM(stok_obat) AS total_jumlah_obat FROM obat_uks")
        jumlah_semua_obat = cursor.fetchone()[0]

        for i in range(len(data_pasien)):
            query = "SELECT nama, kelas, tel FROM siswa WHERE nis = %s"
            cursor.execute(query, (data_pasien[i][0],))
            data_siswa = cursor.fetchone()
            data_pasien[i].extend(data_siswa)

    finally:
        cursor.close()
        conn.close()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Dashboard",
        "jumlah_pasien_hari_ini": jumlah_pasien_hari_ini,
        "jumlah_petugas_hari_ini": jumlah_petugas_hari_ini,
        "pasien_terbaru": data_pasien,
        "jumlah_semua_obat": jumlah_semua_obat
    })

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import timedelta, datetime, date

from database import get_db_connection
from auth import check_session

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/pasien", response_class=HTMLResponse)
async def pasien(request: Request, session: dict = Depends(check_session)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT nama_obat FROM obat_uks")
        obat2 = [obat[0] for obat in cursor.fetchall()]

        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)

        nis = []
        keluhan = []
        obat = []
        penjaga = []

        query = "SELECT nis, keluhan, nama_obat, nama_penjaga FROM pasien WHERE tanggal >= %s AND tanggal < %s"
        cursor.execute(query, (start_of_day, end_of_day))
        result = cursor.fetchall()
        if not result:
            return templates.TemplateResponse("pasien.html", {
                "request": request,
                "title": "Pasien",
                "nis": [],
                "nama": [],
                "kelas": [],
                "tel": [],
                "keluhan": [],
                "obat": [],
                "penjaga": "",
                "obat2": obat2
            })
        else:
            penjaga, nis, keluhan, obat = [], [], [], []
            for row in result:
                nis.append(row[0])
                keluhan.append(row[1])
                obat.append(row[2]) if row[2] != None else obat.append("Tidak Ada")
                penjaga.append(row[3])


        nama = []
        kelas = []
        tel = []
        
        for i in range(len(nis)):
            query = "SELECT nama, kelas, tel FROM siswa WHERE nis = %s"
            cursor.execute(query, (nis[i],))
            n, k, t = cursor.fetchone()
            nama.append(n)
            kelas.append(k)
            tel.append(t)

    finally:
        cursor.close()
        conn.close()

    return templates.TemplateResponse("pasien.html", {
        "request": request,
        "title": "Pasien",
        "nis": nis,
        "nama": nama,
        "kelas": kelas,
        "tel": tel,
        "keluhan": keluhan,
        "obat": obat,
        "penjaga": penjaga,
        "obat2": obat2
    })

@router.post("/tambah-pasien")
async def add_patient(request: Request, session: dict = Depends(check_session)):
    data = await request.json()

    nis = session.get("nis")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT nama FROM siswa WHERE nis = %s"
        cursor.execute(query, (nis,))
        nama_petugas_pmr = cursor.fetchone()[0]

        query = "SELECT * FROM siswa WHERE nama = %s AND nis = %s AND kelas = %s AND tel = %s"
        cursor.execute(query, (data["nama"], int(data["nis"]), int(data["kelas"]), int(data["tel"]),))
        row = cursor.fetchone()

        if not row:
            input_patient_res = f"{data["nama"]} + {int(data["nis"])} + {int(data["kelas"])} + {int(data["tel"])}"
            return {"input_patient_res": input_patient_res, "username": nama_petugas_pmr}

        query = "INSERT INTO pasien (nis, nama_obat, jumlah_obat, keluhan, nama_penjaga) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (data["nis"], data["obat"], data["jumlah"], data["keluhan"], nama_petugas_pmr))
        conn.commit()

        query = "UPDATE obat_uks SET stok_obat = stok_obat - %s WHERE nama_obat = %s"
        cursor.execute(query, (data["jumlah"], data["obat"]))
        conn.commit()

    finally:
        cursor.close()
        conn.close()

    input_patient_res = f"""
        Pasien telah masuk database.

        nis: {data["nis"]}
        nama: {data["nama"]}
        kelas: {data["kelas"]}
        tel: {data["tel"]}
        obat yang dipakai: {data["obat"]}
        jumlah obat dipakai: {data["jumlah"]}

        keluhan:
        {data["keluhan"]}
    """

    return {
        "input_patient_res": input_patient_res,
        "username": nama_petugas_pmr,
    }

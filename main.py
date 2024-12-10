from fastapi import FastAPI, Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException


from starlette.middleware.sessions import SessionMiddleware
from datetime import timedelta, datetime, date
from mysql.connector import pooling

from test import predict

import numpy as np
import ollama
import bcrypt
import warnings

#warnings.filterwarnings("ignore", category=UserWarning, message=".*SQLAlchemy.*")

dbconfig = {
    "host": "localhost",
    "user": "root",
    "password": "ZEVhs27*8*",
    "database": "manajemen_uks"
}

connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=20,
    **dbconfig
)

def get_db_connection():
    return connection_pool.get_connection()

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

def pred_whatvr():
    pass

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def check_password(entered_password: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(entered_password.encode('utf-8'), stored_hash.encode('utf-8'))

def check_session(request: Request):
    session = request.session.get("user")
    if session is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    session_expiration = datetime.fromisoformat(session["expires_at"])
    if datetime.now() > session_expiration:
        del request.session["user"]
        raise HTTPException(status_code=401, detail="Session expired")
    return session

@app.exception_handler(HTTPException)
async def unauthorized_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return RedirectResponse(url="/login")
    return await request.app.default_exception_handler(request, exc)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard", response_class=HTMLResponse)
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

        cursor.execute("SELECT SUM(jumlah_obat) AS total_jumlah_obat FROM stok_obat")
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

@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot(request: Request, session: dict = Depends(check_session)):
    conversation_history = [
        {
            'role': 'system',
            'content': 'Nama saya Dokter UKS dan saya melayani siswa SMK Telkom Jakarta dan memberikan saran atau jawaban terkait kesehatan atau medis'
        }
        
    ]

    return templates.TemplateResponse("chatbot.html", {
        "request": request,
        "title": "Chatbot",
        "conversation_history": conversation_history
    })

@app.post("/send-prompt")
async def send_prompt(request: Request):
    conversation_history = await request.json()

    response = ollama.chat(
        model='llama3.2',
        messages=conversation_history
    )

    ai_response = response['message']['content']

    return PlainTextResponse(content=ai_response)

@app.get("/obat", response_class=HTMLResponse)
async def medicine(request: Request, session: dict = Depends(check_session)):
    current_date = datetime.now()
    bulan_hari_ini = current_date.month
    tahun_hari_ini = current_date.year
    prediksi_stok_akhir = []
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT nama_obat FROM obat_uks")
        obat_uks = [obat[0] for obat in cursor.fetchall()]
        
        cursor.execute("SELECT deskripsi_obat FROM obat_uks")
        deskripsi_obat2 = [desk[0] for desk in cursor.fetchall()]

        cursor.execute("SELECT stok_awal, stok_akhir, nama_obat, bulan, tahun FROM data_obat")
        data = cursor.fetchall()
        training_data = {
            'stok_awal': [x[0] for x in data],
            'stok_akhir': [x[1] for x in data],  # Fix: this should be x[1] for stok_akhir
            'nama_obat': [x[2] for x in data],
            'bulan': [x[3] for x in data],
            'tahun': [x[4] for x in data]
        }

        cursor.execute("SELECT nama_obat FROM stok_obat")
        nama_obat = [r[0] for r in cursor.fetchall()]
        
        cursor.execute("SELECT jumlah_obat FROM stok_obat")
        jumlah_obat = [r[0] for r in cursor.fetchall()]

        # Ensure 'nama_obat' and 'jumlah_obat' match up correctly in the current data
        for i in range(len(jumlah_obat)):
            current_data = {
                'stok_awal': [jumlah_obat[i]],  # Current stock level
                'bulan': [bulan_hari_ini],      # Current month
                'tahun': [tahun_hari_ini],      # Current year
                'nama_obat': [nama_obat[i]]     # Current medicine name
            }

            try:
                # Predict and append to list
                prediksi_stok_akhir.append(predict(training_data, current_data))

            except Exception as e:
                prediksi_stok_akhir.append(f"Error: {str(e)}")
                print(f"Error predicting stock for {nama_obat[i]}: {str(e)}")


        prediksi_stok_akhir = [round(x[0]) for x in prediksi_stok_akhir]
        cursor.execute("SELECT (stok_awal - stok_akhir) AS simulated_difference FROM data_obat")
        rata2_obat_yg_dipakai = [rata2[0] for rata2 in cursor.fetchall()]

        rata_obat_yg_dipakai = []
        for i in range(len(obat_uks)):
            sublist = rata2_obat_yg_dipakai[i::len(obat_uks)]
            rata_obat_yg_dipakai.append(sublist)
        rata_obat_yg_dipakai = [round(np.mean(group)) for group in rata_obat_yg_dipakai]

        cursor.execute("SELECT jumlah_obat FROM stok_obat")
        stok_obat2 = [jumlah[0] for jumlah in cursor.fetchall()]

    finally:
        cursor.close()
        conn.close()

    return templates.TemplateResponse("medicine.html", {
        "request": request,
        "title": "Medicine",
        "obat_uks": obat_uks,
        "prediksi_stok_akhir": prediksi_stok_akhir,
        "jumlah_obat": len(obat_uks),
        "rata2_obat_yg_dipakai": rata_obat_yg_dipakai,
        "stok_obat2": stok_obat2,
        "deskripsi_obat2": deskripsi_obat2
    })


@app.post("/tambah-obat")
async def tambah_obat(request: Request, session: dict = Depends(check_session)):
    data = await request.json()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "UPDATE stok_obat SET jumlah_obat = jumlah_obat + %s WHERE nama_obat = %s"
        cursor.execute(query, (data["jumlahObat"], data["namaObat"]))
        conn.commit()

    finally:
        cursor.close()
        conn.close()

@app.get("/pasien", response_class=HTMLResponse)
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

@app.post("/tambah-pasien")
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

        query = "UPDATE stok_obat SET jumlah_obat = jumlah_obat - %s WHERE nama_obat = %s"
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

@app.get("/jadwal-penjaga", response_class=HTMLResponse)
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

@app.get("/profile", response_class=HTMLResponse)
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

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
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

@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request, session: dict = Depends(check_session)):
    nis = session.get("nis")
    if nis != 123:
        return RedirectResponse(url="/dashboard", status_code=303)
    
    return templates.TemplateResponse("admin.html", {
        "request": request
    })

@app.get("/admin/edit-petugas", response_class=HTMLResponse)
async def edit_petugas(request: Request, session: dict = Depends(check_session)):
    nis = session.get("nis")
    if nis != 123:
        return RedirectResponse(url="/dashboard", status_code=303)
    
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT nis FROM siswa"
        cursor.execute(query)
        nisSiswa = list(cursor.fetchall())

        query = "SELECT nis FROM petugas_pmr"
        cursor.execute(query)
        nisPetugas = cursor.fetchall()

        nisSiswa = [n for n in nisSiswa if n in nisPetugas]

    finally:
        cursor.close()
        conn.close()

    return templates.TemplateResponse("edit_petugas.html", {
        "request": request,
        "nisSiswa": nisSiswa
    })

@app.post("/admin/edit-petugas")
async def edit_petugasPOST(
        request: Request,
        nis: int = Form(...),
        password: str = Form(...),
        hari: str = Form(...),
        waktu_mulai: str = Form(...),
        waktu_selesai: str = Form(...),
        session: dict = Depends(check_session)
    ):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "UPDATE petugas_pmr SET password = %s, hari = %s, waktu_mulai = %s, waktu_selesai = %s WHERE nis = %s"
        cursor.execute(query, (hash_password(password), hari, waktu_mulai, waktu_selesai, nis))
        conn.commit()

    finally:    
        cursor.close()
        conn.close()

    return RedirectResponse(url="/admin/edit-petugas?success=true", status_code=303)

@app.get("/admin/tambah-petugas", response_class=HTMLResponse)
async def tambah_petugas(request: Request, session: dict = Depends(check_session)):
    nis = session.get("nis")
    if nis != 123:
        return RedirectResponse(url="/dashboard", status_code=303)
    
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT nis FROM siswa"
        cursor.execute(query)
        nisSiswa = list(cursor.fetchall())

        query = "SELECT nis FROM petugas_pmr"
        cursor.execute(query)
        nisPetugas = cursor.fetchall()

        nisSiswa = [n for n in nisSiswa if n not in nisPetugas]

    finally:
        cursor.close()
        conn.close()

    return templates.TemplateResponse("tambah_petugas.html", {
        "request": request,
        "nisSiswa": nisSiswa
    })

@app.post("/admin/tambah-petugas")
async def tambah_petugasPOST(
        request: Request,
        nis: int = Form(...),
        password: str = Form(...),
        hari: str = Form(...),
        waktu_mulai: str = Form(...),
        waktu_selesai: str = Form(...),
        session: dict = Depends(check_session)
    ):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "INSERT INTO petugas_pmr VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (nis, hash_password(password), hari, waktu_mulai, waktu_selesai))
        conn.commit()

    finally:    
        cursor.close()
        conn.close()

    return RedirectResponse(url="/admin/tambah-petugas?success=true", status_code=303)

@app.get("/admin/hapus-petugas", response_class=HTMLResponse)
async def hapus_petugas(request: Request, session: dict = Depends(check_session)):
    nis = session.get("nis")
    if nis != 123:
        return RedirectResponse(url="/dashboard", status_code=303)
    
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT nis FROM siswa"
        cursor.execute(query)
        nisSiswa = list(cursor.fetchall())

        query = "SELECT nis FROM petugas_pmr"
        cursor.execute(query)
        nisPetugas = cursor.fetchall()

        nisSiswa = [n for n in nisSiswa if n in nisPetugas]

    finally:
        cursor.close()
        conn.close()

    return templates.TemplateResponse("hapus_petugas.html", {
        "request": request,
        "nisSiswa": nisSiswa
    })

@app.post("/admin/hapus-petugas")
async def hapus_petugasPOST(
        request: Request,
        nis: int = Form(...),
        session: dict = Depends(check_session)
    ):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "DELETE FROM petugas_pmr WHERE nis = %s"
        cursor.execute(query, (nis,))
        conn.commit()

    finally:
        cursor.close()
        conn.close()

    return RedirectResponse(url="/admin/hapus-petugas?success=true", status_code=303)

@app.post("/logout")
async def logout(request: Request):
    del request.session["user"]
    return RedirectResponse(url="/login", status_code=303)

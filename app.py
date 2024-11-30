from fastapi import FastAPI, Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware
from datetime import timedelta, datetime, date
import mysql.connector
from mysql.connector import pooling
import bcrypt
import ollama

dbconfig = {
    "host": "localhost",
    "user": "root",
    "password": "ZEVhs27*8*",
    "database": "manajemen_uks"
}

connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=10,
    **dbconfig
)

def get_db_connection():
    return connection_pool.get_connection()

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

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
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = start_of_day + timedelta(days=1)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT COUNT(DISTINCT nis) AS unique_count FROM pasien WHERE tanggal >= %s AND tanggal < %s"
        cursor.execute(query, (start_of_day, end_of_day))
        jumlah_pasien_hari_ini = cursor.fetchone()[0]

    finally:
        cursor.close()
        conn.close()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Dashboard",
        "jumlah_pasien_hari_ini": jumlah_pasien_hari_ini
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

@app.get("/medicine", response_class=HTMLResponse)
async def medicine(request: Request, session: dict = Depends(check_session)):
    return templates.TemplateResponse("medicine.html", {"request": request, "title": "Medicine"})

@app.get("/pasien", response_class=HTMLResponse)
async def pasien(request: Request, session: dict = Depends(check_session)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

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
                "penjaga": ""
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
    })

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

@app.post("/send-prompt")
async def send_prompt(request: Request):
    conversation_history = await request.json()

    response = ollama.chat(
        model='llama3.2',
        messages=conversation_history
    )

    ai_response = response['message']['content']

    return PlainTextResponse(content=ai_response)

@app.post("/add-patient")
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
            input_patient_res = f"Siswa dengan nis [{data['nis']}] tidak tertemu."
            return {"input_patient_res": input_patient_res, "username": nama_petugas_pmr}

        query = "INSERT INTO pasien (nis, nama_obat, jumlah_obat, keluhan, nama_penjaga) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (data["nis"], data["obat"], data["jumlah"], data["keluhan"], nama_petugas_pmr))
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

    return {"input_patient_res": input_patient_res, "username": nama_petugas_pmr}

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

@app.post("/logout")
async def logout(request: Request):
    del request.session["user"]
    return RedirectResponse(url="/login", status_code=303)

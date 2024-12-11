from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import numpy as np

from database import get_db_connection
from auth import check_session
from test import predict

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/obat", response_class=HTMLResponse)
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
            'stok_akhir': [x[1] for x in data],
            'nama_obat': [x[2] for x in data],
            'bulan': [x[3] for x in data],
            'tahun': [x[4] for x in data]
        }

        cursor.execute("SELECT nama_obat FROM obat_uks")
        nama_obat = [r[0] for r in cursor.fetchall()]
        
        cursor.execute("SELECT stok_obat FROM obat_uks")
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

        cursor.execute("SELECT stok_obat FROM obat_uks")
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


@router.post("/tambah-obat")
async def tambah_obat(request: Request, session: dict = Depends(check_session)):
    data = await request.json()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "UPDATE obat_uks SET stok_obat = stok_obat + %s WHERE nama_obat = %s"
        cursor.execute(query, (data["jumlahObat"], data["namaObat"]))
        conn.commit()

    finally:
        cursor.close()
        conn.close()
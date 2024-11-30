use actix_files as fs;
use actix_session::{Session, SessionMiddleware, storage::CookieSessionStore};
use actix_web::{
    App, HttpServer, HttpResponse, Responder, HttpRequest, middleware::Logger,
    web::{self, Data, Form, Json},
    error::ErrorUnauthorized,
};
use bcrypt::{hash, verify, DEFAULT_COST};
use chrono::{NaiveDate, NaiveDateTime, Utc, Duration};
use serde::{Deserialize, Serialize};
use sqlx::{MySql, Pool, Row};
use tera::{Context, Tera};

// Database Configuration
#[derive(Clone)]
struct AppState {
    pool: Pool<MySql>,
    tera: Tera,
}

#[derive(Debug, Deserialize)]
struct LoginData {
    username_entered: String,
    password_entered: String,
}

#[derive(Serialize)]
struct DashboardData {
    title: &'static str,
    jumlah_pasien_hari_ini: i64,
}

#[derive(Serialize)]
struct PasienData {
    title: &'static str,
    nis: Vec<i32>,
    nama: Vec<String>,
    kelas: Vec<String>,
    tel: Vec<String>,
    keluhan: Vec<String>,
    obat: Vec<String>,
    penjaga: Vec<String>,
}

// Utility for hashing passwords
fn hash_password(password: &str) -> String {
    hash(password, DEFAULT_COST).expect("Failed to hash password")
}

// Check hashed password
fn check_password(entered: &str, stored: &str) -> bool {
    verify(entered, stored).unwrap_or(false)
}

// Middleware for session checking
fn check_session(session: &Session) -> actix_web::Result<i32> {
    if let Some(nis) = session.get::<i32>("nis")? {
        if let Some(expiration) = session.get::<String>("expires_at")? {
            let expiration = NaiveDateTime::parse_from_str(&expiration, "%Y-%m-%dT%H:%M:%S")
                .map_err(|_| ErrorUnauthorized("Session expired"))?;
            if Utc::now().naive_utc() < expiration {
                return Ok(nis);
            }
        }
    }
    Err(ErrorUnauthorized("Unauthorized"))
}

// Routes
async fn dashboard(state: Data<AppState>, session: Session) -> actix_web::Result<HttpResponse> {
    let _nis = check_session(&session)?;
    let conn = &state.pool;
    let today = Utc::now().naive_utc().date();
    let start_of_day = NaiveDateTime::new(today, chrono::NaiveTime::from_hms_opt(0, 0, 0).unwrap());
    let end_of_day = start_of_day + Duration::days(1);

    let result: (i64,) = sqlx::query_as(
        "SELECT COUNT(DISTINCT nis) AS unique_count 
         FROM pasien 
         WHERE tanggal >= ? AND tanggal < ?"
    )
    .bind(start_of_day)
    .bind(end_of_day)
    .fetch_one(conn)
    .await?;

    let mut ctx = Context::new();
    ctx.insert("jumlah_pasien_hari_ini", &result.0);
    let rendered = state.tera.render("dashboard.html", &ctx)?;
    Ok(HttpResponse::Ok().content_type("text/html").body(rendered))
}

async fn pasien(state: Data<AppState>, session: Session) -> actix_web::Result<HttpResponse> {
    let _nis = check_session(&session)?;
    let conn = &state.pool;
    let today = Utc::now().naive_utc().date();
    let start_of_day = NaiveDateTime::new(today, chrono::NaiveTime::from_hms_opt(0, 0, 0).unwrap());
    let end_of_day = start_of_day + Duration::days(1);

    let result = sqlx::query!(
        "SELECT nis, keluhan, nama_obat, nama_penjaga 
         FROM pasien 
         WHERE tanggal >= ? AND tanggal < ?",
        start_of_day,
        end_of_day
    )
    .fetch_all(conn)
    .await?;

    let mut pasien_data = PasienData {
        title: "Pasien",
        nis: vec![],
        nama: vec![],
        kelas: vec![],
        tel: vec![],
        keluhan: vec![],
        obat: vec![],
        penjaga: vec![],
    };

    for row in result {
        let (nama, kelas, tel) = sqlx::query!(
            "SELECT nama, kelas, tel FROM siswa WHERE nis = ?",
            row.nis
        )
        .fetch_one(conn)
        .await?
        .try_into()?;
        pasien_data.nis.push(row.nis);
        pasien_data.nama.push(nama);
        pasien_data.kelas.push(kelas);
        pasien_data.tel.push(tel);
        pasien_data.keluhan.push(row.keluhan.unwrap_or_default());
        pasien_data.obat.push(row.nama_obat.unwrap_or("Tidak Ada".to_string()));
        pasien_data.penjaga.push(row.nama_penjaga.unwrap_or_default());
    }

    let mut ctx = Context::new();
    ctx.insert("pasien_data", &pasien_data);
    let rendered = state.tera.render("pasien.html", &ctx)?;
    Ok(HttpResponse::Ok().content_type("text/html").body(rendered))
}

async fn login(
    state: Data<AppState>,
    form: Form<LoginData>,
    session: Session,
) -> actix_web::Result<HttpResponse> {
    let conn = &state.pool;
    let row = sqlx::query!(
        "SELECT nis, password FROM petugas_pmr WHERE nis = ?",
        form.username_entered
    )
    .fetch_optional(conn)
    .await?;

    if let Some(row) = row {
        if check_password(&form.password_entered, &row.password) {
            let expires_at = Utc::now() + Duration::minutes(1440);
            session.insert("nis", row.nis)?;
            session.insert("expires_at", expires_at.to_rfc3339())?;
            return Ok(HttpResponse::SeeOther().header("Location", "/dashboard").finish());
        }
    }

    Ok(HttpResponse::SeeOther().header("Location", "/login").finish())
}

async fn logout(session: Session) -> impl Responder {
    session.purge();
    HttpResponse::SeeOther().header("Location", "/login").finish()
}

// Main Function
#[actix_web::main]
async fn main() -> std::io::Result<()> {
    std::env::set_var("RUST_LOG", "actix_web=info");
    env_logger::init();

    let tera = Tera::new("templates/**/*").expect("Error parsing templates");
    let pool = Pool::<MySql>::connect("mysql://root:ZEVhs27*8*@localhost/manajemen_uks")
        .await
        .expect("Failed to connect to database");

    let state = Data::new(AppState { tera, pool });

    HttpServer::new(move || {
        App::new()
            .app_data(state.clone())
            .wrap(Logger::default())
            .wrap(SessionMiddleware::new(
                CookieSessionStore::default(),
                b"your-secret-key".to_vec(),
            ))
            .service(web::resource("/").to(|| async { HttpResponse::SeeOther().header("Location", "/dashboard").finish() }))
            .service(web::resource("/dashboard").route(web::get().to(dashboard)))
            .service(web::resource("/pasien").route(web::get().to(pasien)))
            .service(web::resource("/login").route(web::post().to(login)))
            .service(web::resource("/logout").route(web::post().to(logout)))
            .service(fs::Files::new("/static", "static").show_files_listing())
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}

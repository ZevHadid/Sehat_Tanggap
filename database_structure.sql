CREATE DATABASE manajemen_uks;
USE manajemen_uks;

CREATE TABLE petugas_pmr (
	nis INT PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    hari ENUM('senin', 'selasa', 'rabu', 'kamis', 'jumat') NOT NULL,
    waktu_mulai TIME NOT NULL,
    waktu_selesai TIME NOT NULL,	
    foreign key (nis) references siswa(nis)
);

CREATE TABLE pasien (
	nis INT,
    nama_obat VARCHAR(255),
    jumlah_obat INT,
    tanggal DATETIME DEFAULT CURRENT_TIMESTAMP,
    keluhan TEXT,
    nama_penjaga VARCHAR(255),
    foreign key (nis) references siswa(nis)
);

CREATE TABLE data_obat (
  nama_obat VARCHAR(255) NOT NULL,
  stok_awal INT NOT NULL,
  stok_akhir INT NOT NULL,
  bulan INT,
  tahun INT
);

CREATE TABLE obat_uks (
	nama_obat VARCHAR(255) NOT NULL PRIMARY KEY,
    deskripsi_obat TEXT NOT NULL,
    stok_obat INT NOT NULL
);

CREATE TABLE siswa (
	nis INT PRIMARY KEY,
    nama varchar(255) not null,
    kelas int not null,
    tel int not null
);

INSERT INTO obat_uks (nama_obat, deskripsi_obat) VALUES
    ('Panadol Merah', 'Obat pereda nyeri dan demam.'),
    ('Bodrex', 'Obat sakit kepala dan flu.'),
    ('Paramex', 'Obat untuk sakit kepala dan migrain.'),
    ('Asam Mefenamat', 'Obat anti-inflamasi untuk nyeri.'),
    ('Panadol Hijau', 'Obat untuk nyeri ringan dan demam.'),
    ('Decolgen', 'Obat untuk pilek dan hidung tersumbat.'),
    ('Stop Cold', 'Obat flu dan pilek.'),
    ('Komix', 'Sirup obat batuk.'),
    ('Alpara', 'Obat nyeri otot dan sendi.'),
    ('Promag', 'Obat untuk mengatasi maag dan asam lambung.'),
    ('Paracetamol', 'Obat pereda demam dan nyeri.'),
    ('Panadol biru', 'Obat untuk demam dan nyeri ringan.'),
    ('CTM', 'Obat untuk alergi dan gatal-gatal.'),
    ('Aleron', 'Obat alergi antihistamin.'),
    ('FG troches', 'Obat tablet hisap untuk sakit tenggorokan.'),
    ('Dexamethasone', 'Obat anti-inflamasi steroid.'),
    ('Insto', 'Obat tetes mata untuk iritasi.'),
    ('Tolak angin cair', 'Minuman herbal untuk masuk angin.'),
    ('Amoxicilin', 'Antibiotik untuk infeksi bakteri.'),
    ('Feminax', 'Obat pereda nyeri menstruasi.'),
    ('Softex', 'Pembalut wanita.');

    INSERT INTO siswa (nis, nama, kelas, tel) VALUES
	(539231359, 'Zahra Qirana Shalsabilla', 10, 4),
	(539231360, 'Isnaen Galih Athif', 11, 6),
	(539231361, 'Sherli Octaviani', 11, 5),
	(539231362, 'Alfiona Sarah Aulia', 11, 7),
	(539231363, 'M. Daffa Taufiqurrahman A.', 11, 8),
	(539231364, 'Dimas Irawan', 11, 7),
	(539231365, 'Banyu Biru Jibril Andharu', 11, 10),
	(539231366, 'Muhammad Zafran', 11, 13),
	(539231367, 'Nur Aulia Ramadhansyah', 10, 3),
	(53923139, 'Boydo Harmonis Pasaribu', 11, 10),
	(53923140, 'M. Syahid', 11, 9),
	(53923141, 'Keyko Cecillia El Nenong', 10, 6),
	(53923142, 'Mohammad Juan Firdaus', 11, 7),
	(53923143, 'Desi Romauli Nababan', 11, 6),
	(53923144, 'Heri Yana', 10, 1);
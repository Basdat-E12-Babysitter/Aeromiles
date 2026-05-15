# ✈️ Aeromiles  
**Tugas Basis Data 2025/2026**  
**Babysitter - Kelas E**

---

## 🗺️ Struktur Repository

```text
Aeromiles/
├── aeromiles/          # Settings & URL project
├── core/               # Central (Navbar, base.html, css, supabase.js
├── accounts/           # Login, Profil
├── dashboard/          # Dashboard
├── membership/         # Manajemen Member, Identitas
├── miles/              # Claim, Transfer Miles
├── partners/           # Manajemen Penyedia, Mitra Hadiah
├── rewards/            # Manajemen Hadiah, Package, Laporan Transaksi
└── theme/              # Tailwind (Konfigurasi & Source)
```

---

## 👥 Anggota Kelompok

| No | Nama Lengkap                     | NPM        |
|----|----------------------------------|------------|
| 1  | Anya Aleena Wardhany             | 2406401773 |
| 2  | Jessica Tandra                   | 2406355445 |
| 3  | Azzahra Anjelika Borselano       | 2406419663 |
| 4  | Kanayra Maritza Sanika Adeeva    | 2406437880 |
| 5  | Zhafira Uzma                     | 2406495451 |

---

## 🩷 Pembagian Tugas 

| Warna Kategori | Fitur & Deskripsi Tugas | Trigger & Stored Procedure | Penanggung Jawab |
| :--- | :--- | :--- | :--- |
| ⬜ Putih | Navbar (fitur wajib) <br> R - Login & Logout <br> CR - Registrasi <br> R - Dashboard <br> RU - Pengaturan Profil | 1. Pemeriksaan Duplikasi Email saat Registrasi <br> 2. Verifikasi Kredensial saat Login | **Jessica** |
| 🟨 Kuning | CRUD - Manajemen Data Member <br> CRUD - Manajemen Identitas Member | 1. Pencegahan transfer Miles Melebihi Saldo <br> 2. Pencatatan Log Riwayat Transfer Miles | **Anya** |
| 🟩 Hijau | CRUD - Manajemen Claim Missing Miles Member <br> RU - Manajemen Claim Missing Miles Staf <br> CR - Transfer Miles antar Member | 1. Validasi dan Update Saldo award Miles saat Redeem Hadiah <br> 2. Sinkronisasi Award Miles setelah Transaksi Pembelian Package | **Azzahra** |
| 🟦 Biru | CR - Redeem Hadiah <br> CR - Pembelian Award Miles Package <br> R - Informasi Tier & Keuntungan <br> RD - Laporan & Riwayat Transaksi Miles | 1. Pemeriksaan Status Klaim Missing Miles Duplikat <br> 2. Pembaruan Tier Member secara Otomatis berdasarkan Total Miles | **Zhafira** |
| 🟥 Merah | CRUD - Manajemen Hadiah & Penyedia <br> CRUD - Manajemen Mitra | 1. Sinkronisasi Total Miles Member setelah Klaim Missing Miles Disetujui <br> 2. Pemeringkatan Top 5 Member berdasarkan Total Miles | **Kanayra** |

---

## 🛠️ Tools

- **Frontend:** HTML, Tailwind CSS, JavaScript  
- **Backend:** Django (Python)  
- **Database:** Supabase, PostgreSQL
- **Tools:** GitHub, Google Docs

---


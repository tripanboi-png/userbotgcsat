# 🤖 Telegram Userbot Full Management System

> **Python + Telethon + MongoDB + APScheduler + Heroku Worker Dyno**

Userbot Telegram berbasis akun pribadi yang mendukung multi-session, global broadcast, auto broadcast, session management langsung dari Telegram, dan deployment ke Heroku.

---

## 📋 Daftar Isi

1. [Cara Membuat API_ID & API_HASH](#1-cara-membuat-api_id--api_hash)
2. [Cara Membuat String Session](#2-cara-membuat-string-session)
3. [Cara Membuat MongoDB Atlas](#3-cara-membuat-mongodb-atlas)
4. [Cara Deploy ke Heroku](#4-cara-deploy-ke-heroku)
5. [Cara Mengisi Config Vars](#5-cara-mengisi-config-vars)
6. [Semua Commands](#6-semua-commands)
7. [Cara Menambah Session](#7-cara-menambah-session)
8. [Cara Menghapus Session](#8-cara-menghapus-session)
9. [Cara Menjalankan Multi Akun](#9-cara-menjalankan-multi-akun)
10. [Struktur Project](#10-struktur-project)
11. [Tech Stack](#11-tech-stack)

---

## 1. Cara Membuat API_ID & API_HASH

1. Buka browser dan kunjungi: **https://my.telegram.org/apps**
2. Login menggunakan **nomor telepon** akun Telegram Anda.
3. Masukkan kode OTP yang dikirim ke Telegram Anda.
4. Klik **"Create new application"**
5. Isi form:
   - **App title**: Bebas (contoh: `MyUserbot`)
   - **Short name**: Bebas (contoh: `myuserbot`)
   - **URL**: Bisa kosong
   - **Platform**: Other
   - **Description**: Bebas
6. Klik **"Create application"**
7. Anda akan mendapatkan:
   - `App api_id` → ini adalah **API_ID**
   - `App api_hash` → ini adalah **API_HASH**
8. Simpan kedua nilai ini dengan aman.

> ⚠️ **PENTING**: Jangan pernah share API_ID dan API_HASH ke siapapun!

---

## 2. Cara Membuat String Session

String Session adalah representasi sesi login Telegram dalam bentuk string teks.

### Cara 1: Menggunakan Script Bawaan

```bash
# Clone project
git clone https://github.com/yourrepo/userbot.git
cd userbot

# Install dependencies
pip install Telethon

# Jalankan generator
python generate_session.py
```

Ikuti instruksi:
1. Masukkan `API_ID` Anda
2. Masukkan `API_HASH` Anda
3. Masukkan nomor telepon (format internasional, contoh: `+62812345678`)
4. Masukkan kode OTP yang dikirim ke Telegram Anda
5. Jika ada 2FA (Two-Factor Authentication), masukkan password Anda
6. String Session akan tampil di layar

### Cara 2: Menggunakan Replit (Online)

1. Buka **https://replit.com**
2. Buat repl baru dengan Python
3. Install Telethon: `pip install Telethon`
4. Copy isi `generate_session.py` dan jalankan
5. Salin string session yang muncul

### Format String Session

String session terlihat seperti ini:
```
1BVtsOKIBu4kWbJSUz8GZXB3tnPbV7ELzN8t....(panjang)
```

> ⚠️ **PENTING**: String session setara dengan password. Jaga kerahasiaannya!

---

## 3. Cara Membuat MongoDB Atlas

MongoDB Atlas adalah layanan database cloud gratis (tier M0).

1. Buka **https://www.mongodb.com/atlas**
2. Klik **"Try Free"** dan buat akun
3. Setelah login, klik **"Create a deployment"**
4. Pilih **"M0"** (Free tier) → Klik **"Create"**
5. Pilih **region terdekat** (Singapore/Tokyo untuk Indonesia)
6. Tunggu cluster dibuat (1-3 menit)

### Buat Database User

1. Di sidebar kiri, klik **"Database Access"**
2. Klik **"Add New Database User"**
3. Authentication Method: **Password**
4. Isi **Username** dan **Password** (simpan dengan aman!)
5. Database User Privileges: **"Atlas admin"** atau **"Read and write to any database"**
6. Klik **"Add User"**

### Whitelist IP (Allow All)

1. Di sidebar kiri, klik **"Network Access"**
2. Klik **"Add IP Address"**
3. Klik **"Allow Access from Anywhere"** (untuk Heroku)
4. Klik **"Confirm"**

### Dapatkan Connection String

1. Di sidebar, klik **"Database"**
2. Klik **"Connect"** pada cluster Anda
3. Pilih **"Drivers"**
4. Driver: **Python**, Version: **3.12 or later**
5. Salin connection string yang terlihat seperti:
   ```
   mongodb+srv://username:<password>@cluster0.xxxxx.mongodb.net/
   ```
6. Ganti `<password>` dengan password user yang Anda buat
7. Tambahkan nama database di akhir URL:
   ```
   mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/userbot_db?retryWrites=true&w=majority
   ```

---

## 4. Cara Deploy ke Heroku

### Prasyarat

- Akun Heroku (https://signup.heroku.com)
- Heroku CLI terinstall (https://devcenter.heroku.com/articles/heroku-cli)
- Git terinstall

### Langkah Deployment

```bash
# 1. Login ke Heroku CLI
heroku login

# 2. Clone/masuk ke direktori project
cd userbot

# 3. Inisialisasi git (jika belum)
git init
git add .
git commit -m "Initial commit"

# 4. Buat Heroku app baru
heroku create nama-app-anda

# 5. Set Config Vars (lihat bagian 5)
heroku config:set API_ID=12345678
heroku config:set API_HASH=abcdef1234567890abcdef1234567890
heroku config:set OWNER_ID=123456789
heroku config:set OWNER_SESSION=string_session_anda
heroku config:set MONGO_URI=mongodb+srv://...

# 6. Deploy ke Heroku
git push heroku main

# 7. Scale worker dyno (BUKAN web dyno!)
heroku ps:scale worker=1

# 8. Cek logs
heroku logs --tail
```

### Cara Menggunakan Heroku Dashboard

1. Buka **https://dashboard.heroku.com**
2. Pilih app Anda
3. Tab **"Settings"** → **"Config Vars"** → **"Reveal Config Vars"**
4. Tambahkan semua config vars yang diperlukan
5. Tab **"Resources"**:
   - **Matikan** `web` dyno (OFF)
   - **Hidupkan** `worker` dyno (ON)

### Deploy Ulang (Update)

```bash
git add .
git commit -m "Update"
git push heroku main
```

### Restart Dyno

```bash
heroku ps:restart worker
```

---

## 5. Cara Mengisi Config Vars

| Variable | Wajib | Keterangan |
|----------|-------|------------|
| `API_ID` | ✅ | Dari https://my.telegram.org/apps |
| `API_HASH` | ✅ | Dari https://my.telegram.org/apps |
| `OWNER_ID` | ✅ | Telegram User ID Anda |
| `OWNER_SESSION` | ✅ | String session akun owner |
| `MONGO_URI` | ✅ | MongoDB Atlas connection string |
| `DB_NAME` | ❌ | Nama database (default: `userbot_db`) |
| `BROADCAST_DELAY` | ❌ | Delay antar pesan broadcast dalam detik (default: `1.5`) |
| `FLOOD_SLEEP_THRESHOLD` | ❌ | Batas FloodWait sleep (default: `60`) |
| `LOG_LEVEL` | ❌ | Level log: DEBUG/INFO/WARNING/ERROR (default: `INFO`) |

### Cara Mendapatkan OWNER_ID

1. Buka Telegram
2. Cari bot **@userinfobot**
3. Kirim `/start`
4. Bot akan membalas dengan **Id:** `xxxxxxxxx` — itulah OWNER_ID Anda

---

## 6. Semua Commands

> Semua command hanya bisa digunakan oleh **OWNER_ID** (akun yang menjalankan bot).
> Prefix command: **titik (`.`)**

### 🔧 General

| Command | Deskripsi |
|---------|-----------|
| `.ping` | Cek latency bot |
| `.alive` | Cek status bot berjalan |
| `.help` | Tampilkan semua command |

**Contoh output `.ping`:**
```
🏓 Pong!
⚡ 123.45ms
```

**Contoh output `.alive`:**
```
🤖 USERBOT ALIVE

👤 Name: Nama Anda
🆔 ID: 123456789
🐍 Framework: Telethon
📦 Session: owner
✅ Status: Online & Running
```

---

### 📱 Session Management

| Command | Deskripsi |
|---------|-----------|
| `.addsession <string>` | Tambah session baru |
| `.delsession <nama>` | Hapus session |
| `.sessions` | Lihat semua session aktif |

**Contoh output `.sessions`:**
```
📱 ACTIVE SESSIONS

1. 🟢 AkunUtama
   └ @username1 | ID: 123456789
2. 🟢 AkunDua
   └ @username2 | ID: 987654321
3. 🔴 AkunTiga
   └ — | ID: 111222333

Total: 3
```

---

### 📢 Broadcast (Manual)

| Command | Deskripsi |
|---------|-----------|
| `.gcast <pesan>` | Broadcast menggunakan akun owner |
| `.gcastall <pesan>` | Broadcast menggunakan semua akun |
| `.gcastsession <nama> <pesan>` | Broadcast menggunakan akun tertentu |

**Contoh penggunaan:**
```
.gcast Halo semua! Ini pesan broadcast dari userbot.

.gcastall Pesan ini dikirim oleh semua akun!

.gcastsession akun2 Hanya akun2 yang mengirim pesan ini.
```

**Contoh output `.gcast`:**
```
📢 GCAST SELESAI

👥 Grup: 45
✅ Berhasil: 43
❌ Gagal: 2
⏱ Durasi: 1.2m
🆔 Task: A1B2C3D4
```

---

### ⏰ Auto Broadcast

| Command | Deskripsi |
|---------|-----------|
| `.autogcast <menit> <pesan>` | Auto broadcast owner setiap X menit |
| `.autogcastall <menit> <pesan>` | Auto broadcast semua akun setiap X menit |
| `.autogcastsession <nama> <menit> <pesan>` | Auto broadcast akun tertentu |

**Contoh penggunaan:**
```
.autogcast 10 Pesan otomatis setiap 10 menit!

.autogcastall 30 Semua akun broadcast setiap 30 menit!

.autogcastsession akun2 15 Hanya akun2, setiap 15 menit.
```

**Fitur Auto Delete:**
- Setiap run baru akan **otomatis menghapus** pesan lama sebelum mengirim yang baru.
- Jika hapus gagal, proses tetap lanjut mengirim pesan baru.

---

### 🛑 Stop Auto Broadcast

| Command | Deskripsi |
|---------|-----------|
| `.stopgcast` | Stop semua auto broadcast |
| `.stopgcastsession <nama>` | Stop auto broadcast akun tertentu |

---

### 📊 Status & Statistik

| Command | Deskripsi |
|---------|-----------|
| `.gcaststatus` | Status auto broadcast owner |
| `.gcaststatusall` | Status semua auto broadcast |
| `.gcaststats` | Statistik broadcast (hari ini, minggu, total) |
| `.gcasterror` | Log error broadcast terbaru |

**Contoh output `.gcaststatus`:**
```
📊 AUTO GCAST STATUS

📱 Session: owner
🟢 Status: RUNNING
⏱ Interval: 10 Menit
🔢 Total Run: 15
🕐 Last Run: 2024-01-15 10:30:00 UTC
⏭ Next Run: 2024-01-15 10:40:00 UTC
🆔 Task ID: AGC_OWNER_1234567890

💬 Pesan:
Halo semua! Pesan otomatis...
```

**Contoh output `.gcaststats`:**
```
📈 GCAST STATS

Hari Ini:
  ✅ Berhasil: 135
  ❌ Gagal: 5

Minggu Ini:
  ✅ Berhasil: 890
  ❌ Gagal: 23

Total:
  ✅ Berhasil: 4521
  ❌ Gagal: 89
```

---

## 7. Cara Menambah Session

### Metode 1: Dari Telegram (Direkomendasikan)

1. Buka Telegram di akun owner
2. Di chat mana saja (atau saved messages), ketik:
   ```
   .addsession <string_session_akun_baru>
   ```
3. Bot akan memvalidasi dan menambahkan session secara otomatis
4. Akun baru langsung aktif tanpa perlu restart

### Metode 2: Via Config Vars Heroku

Untuk akun owner utama, set `OWNER_SESSION` di config vars Heroku dengan string session Anda.

### Cara Generate String Session untuk Akun Tambahan

```bash
python generate_session.py
```

Jalankan untuk setiap akun yang ingin ditambahkan. Gunakan nomor telepon akun yang berbeda.

---

## 8. Cara Menghapus Session

```
.delsession NamaAkun
```

Contoh:
```
.delsession AkunDua
```

Bot akan:
1. Menghentikan client akun tersebut
2. Menandai session sebagai tidak aktif di database
3. Menghentikan semua auto broadcast untuk akun tersebut

> **Catatan:** Nama session adalah nama yang tampil di `.sessions` (nama akun Telegram).

---

## 9. Cara Menjalankan Multi Akun

### Setup Awal

1. Generate string session untuk setiap akun:
   ```bash
   python generate_session.py
   ```
   Lakukan untuk setiap akun yang ingin ditambahkan.

2. Set `OWNER_SESSION` untuk akun utama (owner) di Heroku.

3. Deploy ke Heroku dan pastikan worker dyno berjalan.

### Menambah Akun Tambahan (Runtime)

Dari chat Telegram akun owner:
```
.addsession 1BVtsOKIBu4kW....(session akun2)
.addsession 2CWuPLJCv5lX....(session akun3)
```

### Broadcast dengan Multi Akun

```
# Semua akun broadcast bersamaan
.gcastall Pesan dari semua akun

# Semua akun auto broadcast setiap 30 menit
.autogcastall 30 Pesan otomatis semua akun

# Akun tertentu saja
.gcastsession AkunDua Hanya akun dua yang broadcast ini
```

### Melihat Status Semua Akun

```
.sessions         → Lihat semua akun aktif
.gcaststatusall   → Status auto broadcast semua akun
.gcaststats       → Statistik gabungan semua akun
```

### Catatan Penting Multi Akun

- Setiap akun broadcast ke **grup mereka masing-masing** (bukan grup yang sama)
- Jika akun A dan B sama-sama ada di grup X, kedua akun akan mengirim pesan ke grup X
- FloodWait ditangani per-akun secara independen
- Database menyimpan message ID terakhir per-chat per-session untuk auto-delete

---

## 10. Struktur Project

```
project/
├── main.py                 # Entry point, ClientManager
├── config.py               # Konfigurasi & env vars
├── generate_session.py     # Script generator string session
├── requirements.txt        # Python dependencies
├── Procfile                # Heroku process definition
├── runtime.txt             # Python version untuk Heroku
├── README.md               # Dokumentasi ini
├── .env.example            # Template environment variables
├── .gitignore              # File yang diabaikan git
│
├── modules/
│   ├── __init__.py
│   ├── owner.py            # .ping, .alive, .help
│   ├── gcast.py            # .gcast, .gcastall, .gcastsession
│   ├── autogcast.py        # .autogcast, .stopgcast, .gcaststatus
│   ├── session_manager.py  # .addsession, .delsession, .sessions
│   ├── stats.py            # .gcaststats, .gcasterror
│   └── help.py             # Help module reference
│
├── database/
│   ├── __init__.py
│   ├── mongo.py            # MongoDB Motor connection
│   ├── sessions.py         # CRUD sessions collection
│   ├── autogcast.py        # CRUD autogcast collection
│   └── logs.py             # CRUD gcast_logs & sent_messages
│
├── utils/
│   ├── __init__.py
│   ├── filters.py          # Custom Telethon filters
│   ├── scheduler.py        # APScheduler wrapper
│   ├── floodwait.py        # FloodWait handler
│   ├── logger.py           # Centralized logging
│   └── helpers.py          # General utilities
│
└── sessions/               # Empty dir (sessions di MongoDB)
    └── .gitkeep
```

---

## 11. Tech Stack

| Teknologi | Versi | Fungsi |
|-----------|-------|--------|
| Python | 3.12 | Runtime |
| Telethon | 1.36.0 | Telegram MTProto client |
| Motor | 3.6.0 | Async MongoDB driver |
| PyMongo | 4.10.1 | MongoDB base driver |
| APScheduler | 3.10.4 | Task scheduler |
| python-dotenv | 1.0.1 | Environment variable loader |
| cryptg | 0.4.0 | Crypto optimization untuk Telethon |

---

## ⚙️ MongoDB Collections

### `sessions`
```json
{
  "name": "AkunUtama",
  "user_id": 123456789,
  "username": "myusername",
  "session": "1BVtsOKIBu4k...",
  "active": true,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

### `autogcast`
```json
{
  "task_id": "agc_owner_1705312800",
  "session_name": "owner",
  "user_id": 123456789,
  "interval_minutes": 10,
  "message": "Halo semua!",
  "all_sessions": false,
  "active": true,
  "last_run": "2024-01-15T10:30:00Z",
  "next_run": "2024-01-15T10:40:00Z",
  "run_count": 15,
  "created_at": "2024-01-15T10:00:00Z"
}
```

### `sent_messages`
```json
{
  "chat_id": -1001234567890,
  "message_id": 12345,
  "session_name": "akunutama",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### `gcast_logs`
```json
{
  "task_id": "A1B2C3D4",
  "session_name": "owner",
  "chat_id": -1001234567890,
  "message_id": 12345,
  "success": true,
  "error": null,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 🔒 Security Notes

1. **Jangan commit `.env`** ke repository (sudah ada di `.gitignore`)
2. **Jangan share string session** ke siapapun — setara dengan password akun Telegram
3. **Gunakan IP Whitelist MongoDB** dengan bijak — untuk Heroku gunakan "Allow from Anywhere" karena IP Heroku dinamis
4. **Aktifkan 2FA** pada akun Telegram untuk keamanan tambahan
5. **Backup string session** di tempat aman

---

## ❓ Troubleshooting

### Bot tidak merespons command
- Pastikan Anda mengirim command dari **akun yang sama** dengan OWNER_ID
- Command menggunakan prefix **titik (`.`)**
- Pastikan worker dyno Heroku sedang **ON** (bukan web)
- Cek logs: `heroku logs --tail`

### Error `AuthKeyUnregisteredError`
- String session expired atau invalid
- Generate ulang string session dengan `python generate_session.py`

### Error `UserDeactivatedBanError`
- Akun Telegram terkena banned
- Gunakan akun Telegram yang berbeda

### Error MongoDB connection
- Pastikan MONGO_URI benar
- Pastikan IP Heroku sudah di-whitelist di MongoDB Atlas
- Pastikan user MongoDB memiliki permission yang benar

### FloodWait banyak
- Kurangi frekuensi broadcast (tambah interval menit)
- Tambah `BROADCAST_DELAY` (default 1.5 detik)
- Kurangi jumlah akun yang melakukan broadcast bersamaan

### Auto broadcast berhenti setelah restart Heroku
- Tidak perlu khawatir! Auto broadcast akan **otomatis restore** dari database saat startup
- Cek dengan `.gcaststatusall` setelah restart

---

## 📞 Support

Jika mengalami masalah:
1. Cek logs Heroku: `heroku logs --tail`
2. Pastikan semua Config Vars sudah diisi dengan benar
3. Pastikan string session valid dengan `generate_session.py`

---

*Built with ❤️ using Python + Telethon + MongoDB*

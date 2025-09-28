# trash-classifier-webapp


# 🗑️ Trash Classifier Web App

Aplikasi web berbasis **Flask + TensorFlow Lite + SQLite** untuk:
- Klasifikasi gambar sampah (plastik, kertas, kaca, kardus, logam, residu).
- Memberikan reward poin berdasarkan kategori sampah.
- Mencatat hasil klasifikasi tiap user ke database.
- Mendukung login/signup user.
- Admin dashboard untuk melihat semua user dan semua record klasifikasi.

---

## 🚀 Fitur Utama

### 👤 User
- **Login / Signup / Logout**  
- **Home**: menu utama untuk memilih fitur.  
- **Klasifikasi Sampah**: upload gambar → sistem memprediksi jenis sampah menggunakan model TFLite.  
  - Reward poin otomatis diberikan sesuai kategori.  
  - Hasil disimpan ke database (`records`).  
- **Riwayat Pencatatan**: user dapat melihat semua hasil klasifikasi miliknya + total poin.  

### 👨‍💼 Admin
- Login dengan **username: `admin`, password: `admin`**.  
- **Admin Dashboard**:
  - 🔹 **Semua Record** → melihat seluruh data klasifikasi (7 tabel: semua data, kertas, plastik, kaca, kardus, logam, residu).  
  - 🔹 **Semua User** → melihat daftar user yang terdaftar di aplikasi.  

---

## 🛠️ Teknologi
- **Backend**: Flask (Python)  
- **Database**: SQLite  
- **Model AI**: TensorFlow Lite (`model_fix.tflite`)  
- **Frontend**: HTML + CSS (template Flask)  

---

## 📂 Struktur Project
project/
│── app.py # Main Flask app
│── init_db.py # Script untuk membuat database & tabel
│── trash.db # SQLite database (terbuat setelah init_db dijalankan)
│── model_fix.tflite # Model klasifikasi TFLite
│── static/
│ └── uploads/ # Folder untuk menyimpan gambar yang diupload
│── templates/
│ ├── login.html
│ ├── signup.html
│ ├── home.html
│ ├── classify.html
│ ├── records.html
│ ├── admin.html
│ ├── admin_records.html
│ └── admin_users.html
└── README.md


### 4. Jalankan Aplikasi

```bash
python app.py
```

Aplikasi akan berjalan di browser lokal:

```
http://127.0.0.1:5000
```

---



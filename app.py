import os, time, sqlite3
import numpy as np
import tensorflow as tf
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, g, flash
from PIL import Image
from datetime import datetime

# === Flask Setup ===
app = Flask(__name__)
app.secret_key = "secret123"
DATABASE = "trash.db"
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === Load TFLite Model ===
interpreter = tf.lite.Interpreter(model_path="model_fix.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
input_shape = input_details[0]['shape']

# === Kelas Sampah ===
class_names = ["kaca", "kardus", "kertas", "logam", "plastik", "residu"]

# === Reward Poin ===
reward_points = {
    "plastik": 20,
    "kertas": 15,
    "kardus": 10,
    "kaca": 25,
    "logam": 30,
    "residu": 5
}

# === DB Helpers ===
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# === Decorator proteksi halaman ===
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("⚠️ Silakan login dulu.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# === Preprocess Gambar ===
def preprocess_image(image_path):
    img = Image.open(image_path).convert("RGB")
    img = img.resize((input_shape[1], input_shape[2]))
    img = np.array(img, dtype=np.float32) / 255.0
    img = np.expand_dims(img, axis=0)
    return img

# === Routes ===
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Cek apakah admin
        if username == "admin" and password == "admin":
            session["user_id"] = 0   # bisa pakai 0 untuk admin
            session["username"] = "admin"
            flash("✅ Login sebagai Admin berhasil!")
            return redirect(url_for("admin"))

        # Kalau bukan admin → cek di database
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("✅ Login berhasil!")
            return redirect(url_for("home"))
        else:
            flash("❌ Username atau password salah!")

    return render_template("login.html")



@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            db.commit()
            flash("✅ Akun berhasil dibuat! Silakan login.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("❌ Username sudah digunakan!")
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("👋 Anda sudah logout.")
    return redirect(url_for("login"))

# === Halaman Home (menu utama) ===
@app.route("/home")
@login_required
def home():
    return render_template("home.html", username=session["username"])

# === Halaman Klasifikasi ===
@app.route("/classify", methods=["GET", "POST"])
@login_required
def classify():
    if request.method == "POST":
        file = request.files["file"]
        if file.filename == "":
            flash("❌ Tidak ada file yang diupload!")
            return redirect(url_for("classify"))

        # Simpan file upload
        filename = f"{int(time.time())}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Preprocess gambar
        input_data = preprocess_image(file_path)

        # Prediksi pakai TFLite
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]['index'])[0]

        predicted_index = int(np.argmax(output_data))
        predicted_class = class_names[predicted_index]
        confidence = float(np.max(output_data))
        poin = reward_points.get(predicted_class, 0)

        # Simpan hasil ke DB
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO records (user_id, waktu, kategori, poin)
            VALUES (?, ?, ?, ?)
        """, (session["user_id"],
              datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              predicted_class,
              poin))
        db.commit()

        return render_template(
            "classify.html",
            filename=filename,
            predicted_class=predicted_class,
            confidence=confidence
        )

    return render_template("classify.html")

# === Halaman Riwayat Pencatatan ===
@app.route("/records")
@login_required
def records():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM records WHERE user_id=?", (session["user_id"],))
    records = cursor.fetchall()

    cursor.execute("SELECT SUM(poin) as total FROM records WHERE user_id=?", (session["user_id"],))
    total_poin = cursor.fetchone()["total"] or 0

    return render_template("records.html", records=records, total_poin=total_poin)

# === Admin Dashboard ===
@app.route("/admin")
@login_required
def admin():
    if session.get("username") != "admin":
        flash("❌ Anda bukan admin!")
        return redirect(url_for("home"))
    return render_template("admin.html")

# === Semua User ===
@app.route("/admin/users")
@login_required
def admin_users():
    if session.get("username") != "admin":
        flash("❌ Anda bukan admin!")
        return redirect(url_for("home"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    return render_template("admin_users.html", users=users)



@app.route("/admin/records")
@login_required
def admin_records():
    if session.get("username") != "admin":
        flash("❌ Anda bukan admin!")
        return redirect(url_for("home"))

    db = get_db()
    cursor = db.cursor()

    # Semua data
    cursor.execute("SELECT * FROM records")
    all_records = cursor.fetchall()

    # Filter per kategori
    def get_records_by_category(cat):
        cursor.execute("SELECT * FROM records WHERE kategori=?", (cat,))
        return cursor.fetchall()

    kertas = get_records_by_category("kertas")
    plastik = get_records_by_category("plastik")
    kaca = get_records_by_category("kaca")
    kardus = get_records_by_category("kardus")
    logam = get_records_by_category("logam")
    residu = get_records_by_category("residu")

    return render_template(
        "admin_records.html",
        all_records=all_records,
        kertas=kertas,
        plastik=plastik,
        kaca=kaca,
        kardus=kardus,
        logam=logam,
        residu=residu
    )


# === Run Flask ===
if __name__ == "__main__":
    app.run(debug=True)

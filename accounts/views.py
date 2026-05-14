import json
import bcrypt
from django.db import connection
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["GET", "POST"])
def login(request):
    if request.method == "GET":
        # Kalau sudah login, redirect ke dashboard
        if request.session.get("user_email"):
            return _redirect_dashboard(request)
        return render(request, "login.html")

    try:
        email    = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
 
        if not email or not password:
            return render(request, "login.html", {"ERROR": "Email dan password wajib diisi."})
 
        with connection.cursor() as cur:
            cur.execute("SELECT * FROM verifikasi_login(%s)", [email])
            row  = cur.fetchone()
            cols = [col[0] for col in cur.description]
            user = dict(zip(cols, row))
 
        # Bandingkan password input dengan hash di DB (bcrypt)
        password_cocok = bcrypt.checkpw(
            password.encode("utf-8"),
            user["password_hash"].encode("utf-8")
        )
 
        if not password_cocok:
            return render(request, "login.html", {
                "ERROR": "Email atau password salah, silakan coba lagi."
            })
 
        # Simpan session
        request.session["user_email"]      = user["email"]
        request.session["user_role"]       = user["role"]
        request.session["user_name"]       = f"{user['first_mid_name']} {user['last_name']}"
        request.session["user_salutation"] = user["salutation"]
 
        if user["role"] == "member":
            request.session["nomor_member"] = user["nomor_member"]
            request.session["id_tier"]      = user["id_tier"]
            request.session["nama_tier"]    = user["nama_tier"]
            request.session["award_miles"]  = str(user["award_miles"])
            request.session["total_miles"]  = str(user["total_miles"])
 
        return _redirect_dashboard(request)
 
    except Exception as e:
        error_msg = str(e)
        # Bersihkan pesan psycopg2 yang verbose
        if "ERROR:" in error_msg:
            error_msg = error_msg.split("ERROR:")[-1].strip()
        return render(request, "login.html", {"error": error_msg})

def _redirect_dashboard(request):
    role = request.session.get("user_role")
    if role == "member":
        return redirect("dashboard:member")
    elif role == "staf":
        return redirect("dashboard:staf")
    else:
        return redirect("accounts:login")

def logout(request):
    request.session.flush()
    return redirect("accounts:login")

@csrf_exempt
@require_http_methods(["GET", "POST"])
def register(request):
    if request.method == "GET":
        return render(request, "register.html")
 
    try:
        role             = request.POST.get("reg-role", "member")
        email            = request.POST.get("email", "").strip()
        password         = request.POST.get("password", "").strip()
        password_confirm = request.POST.get("password_confirm", "").strip()
        salutation       = request.POST.get("salutation", "").strip()
        first_mid_name   = request.POST.get("first_mid_name", "").strip()
        last_name        = request.POST.get("last_name", "").strip()
        country_code     = request.POST.get("country_code", "").strip()
        mobile_number    = request.POST.get("mobile_number", "").strip()
        tanggal_lahir    = request.POST.get("tanggal_lahir", "").strip()
        kewarganegaraan  = request.POST.get("kewarganegaraan", "").strip()
        kode_maskapai    = request.POST.get("kode_maskapai", "").strip()
 
        # Validasi
        if not email or not password:
            return render(request, "register.html", {"ERROR": "Email dan password wajib diisi."})
 
        if password != password_confirm:
            return render(request, "register.html", {"ERROR": "Konfirmasi password tidak cocok."})
 
        if len(password) < 8:
            return render(request, "register.html", {"ERROR": "Password minimal 8 karakter."})
 
        if role == "staf" and not kode_maskapai:
            return render(request, "register.html", {"ERROR": "Kode maskapai wajib diisi untuk staf."})
 
        # Hash password sebelum disimpan
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
 
        with connection.cursor() as cur:
            # insert ke tabel pengguna 
            cur.execute("""
                INSERT INTO PENGGUNA
                    (email, password, salutation, first_mid_name, last_name,
                     country_code, mobile_number, tanggal_lahir, kewarganegaraan)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                email, hashed, salutation, first_mid_name, last_name,
                country_code, mobile_number, tanggal_lahir, kewarganegaraan
            ])
 
            if role == "member":
                # insert ke table member (nomor_member dari sequence)
                cur.execute("""
                    INSERT INTO MEMBER (email, tanggal_bergabung, id_tier, award_miles, total_miles)
                    VALUES (%s, CURRENT_DATE, 'T001', 0, 0)
                """, [email])
 
            elif role == "staf":
                # insert ke table staf (id_staf dari sequence)
                cur.execute("""
                    INSERT INTO STAF (email, kode_maskapai)
                    VALUES (%s, %s)
                """, [email, kode_maskapai])
 
        return render(request, "login.html", {
            "success": "Akun berhasil dibuat! Silakan login."
        })
 
    except Exception as e:
        error_msg = str(e)
        if "ERROR:" in error_msg:
            error_msg = error_msg.split("ERROR:")[-1].strip()
        return render(request, "register.html", {"ERROR": error_msg})
    
def profile_member(request):
    if not request.session.get("user_email") or request.session.get("user_role") != "member":
        return redirect("accounts:login")
 
    email = request.session["user_email"]
 
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                pg.email, pg.salutation, pg.first_mid_name, pg.last_name,
                pg.country_code, pg.mobile_number, pg.tanggal_lahir, pg.kewarganegaraan,
                m.nomor_member, m.tanggal_bergabung, m.award_miles, m.total_miles,
                t.nama AS nama_tier
            FROM PENGGUNA pg
            JOIN MEMBER m ON m.email = pg.email
            JOIN TIER   t ON t.id_tier = m.id_tier
            WHERE pg.email = %s
        """, [email])
        row  = cur.fetchone()
        cols = [col[0] for col in cur.description]
        member = dict(zip(cols, row))
 
    return render(request, "profile_member.html", {"member": member})

def profile_staf(request):
    if not request.session.get("user_email") or request.session.get("user_role") != "staf":
        return redirect("accounts:login")
 
    email = request.session["user_email"]
 
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                pg.email, pg.salutation, pg.first_mid_name, pg.last_name,
                pg.country_code, pg.mobile_number, pg.tanggal_lahir, pg.kewarganegaraan,
                s.id_staf, mk.nama_maskapai, mk.kode_maskapai
            FROM PENGGUNA pg
            JOIN STAF     s  ON s.email         = pg.email
            JOIN MASKAPAI mk ON mk.kode_maskapai = s.kode_maskapai
            WHERE pg.email = %s
        """, [email])
        row  = cur.fetchone()
        cols = [col[0] for col in cur.description]
        staf = dict(zip(cols, row))
 
    return render(request, "profile_staf.html", {"staf": staf})
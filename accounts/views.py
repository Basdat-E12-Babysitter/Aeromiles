from django.contrib.auth.hashers import make_password, check_password
from django.db import connection
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["GET", "POST"])
def login(request):
    if request.method == "GET":
        if request.session.get("user_email"):
            return _redirect_dashboard(request)
        return render(request, "login.html")

    try:
        email    = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        if not email or not password:
            return render(request, "login.html", {"error": "Email dan password wajib diisi."})

        # SP ambil data profil + password_hash, raise exception kalau email tidak ada
        with connection.cursor() as cur:
            cur.execute("SELECT * FROM verifikasi_login(%s)", [email])
            row  = cur.fetchone()
            cols = [col[0] for col in cur.description]
            user = dict(zip(cols, row))

        # Compare password
        if not check_password(password, user["password_hash"]):
            return render(request, "login.html", {
                "error": "Email atau password salah, silakan coba lagi."
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
        error_msg = error_msg.split("\n")[0]
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

        if not email or not password:
            return render(request, "register.html", {"error": "Email dan password wajib diisi."})

        if password != password_confirm:
            return render(request, "register.html", {"error": "Konfirmasi password tidak cocok."})

        if len(password) < 8:
            return render(request, "register.html", {"error": "Password minimal 8 karakter."})

        if role == "staf" and not kode_maskapai:
            return render(request, "register.html", {"error": "Kode maskapai wajib diisi untuk staf."})
        
        if not salutation or not first_mid_name or not last_name:
            return render(request, "register.html", {"error": "Semua field wajib diisi."})

        if not tanggal_lahir:
            return render(request, "register.html", {"error": "Tanggal lahir wajib diisi."})

        if not kewarganegaraan:
            return render(request, "register.html", {"error": "Kewarganegaraan wajib diisi."})

        if not country_code:
            return render(request, "register.html", {"error": "Kode negara wajib diisi."})

        if not mobile_number:
            return render(request, "register.html", {"error": "Nomor HP wajib diisi."})

        # Hash pakai Django built-in
        hashed = make_password(password)

        with connection.cursor() as cur:
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
                cur.execute("""
                    INSERT INTO MEMBER (email, tanggal_bergabung, id_tier, award_miles, total_miles)
                    VALUES (%s, CURRENT_DATE, 'T001', 0, 0)
                """, [email])
            elif role == "staf":
                cur.execute("""
                    INSERT INTO STAF (email, kode_maskapai)
                    VALUES (%s, %s)
                """, [email, kode_maskapai])

        return render(request, "login.html", {
            "success": "Akun berhasil dibuat! Silakan login."
        })

    except Exception as e:
        error_msg = str(e)
        error_msg = error_msg.split("\n")[0]
        if "ERROR:" in error_msg:
            error_msg = error_msg.split("ERROR:")[-1].strip()
        return render(request, "register.html", {"error": error_msg})

def _get_member(email):
    with connection.cursor() as cur:
        cur.execute("""
            SELECT pg.email, pg.salutation, pg.first_mid_name, pg.last_name,
                   pg.country_code, pg.mobile_number, pg.tanggal_lahir, pg.kewarganegaraan,
                   m.nomor_member, m.tanggal_bergabung, m.award_miles, m.total_miles,
                   t.nama AS nama_tier
            FROM PENGGUNA pg
            JOIN MEMBER m ON m.email   = pg.email
            JOIN TIER   t ON t.id_tier = m.id_tier
            WHERE pg.email = %s
        """, [email])
        row  = cur.fetchone()
        cols = [col[0] for col in cur.description]
        return dict(zip(cols, row))


def _get_staf(email):
    with connection.cursor() as cur:
        cur.execute("""
            SELECT pg.email, pg.salutation, pg.first_mid_name, pg.last_name,
                   pg.country_code, pg.mobile_number, pg.tanggal_lahir, pg.kewarganegaraan,
                   s.id_staf, mk.nama_maskapai, mk.kode_maskapai
            FROM PENGGUNA pg
            JOIN STAF     s  ON s.email          = pg.email
            JOIN MASKAPAI mk ON mk.kode_maskapai = s.kode_maskapai
            WHERE pg.email = %s
        """, [email])
        row  = cur.fetchone()
        cols = [col[0] for col in cur.description]
        return dict(zip(cols, row))


@csrf_exempt
@require_http_methods(["GET", "POST"])
def profile_member(request):
    if not request.session.get("user_email") or request.session.get("user_role") != "member":
        return redirect("accounts:login")

    email = request.session["user_email"]

    if request.method == "GET":
        return render(request, "profile_member.html", {"member": _get_member(email)})

    try:
        with connection.cursor() as cur:
            cur.execute("""
                UPDATE PENGGUNA SET
                    salutation      = %s,
                    first_mid_name  = %s,
                    last_name       = %s,
                    country_code    = %s,
                    mobile_number   = %s,
                    tanggal_lahir   = %s,
                    kewarganegaraan = %s
                WHERE email = %s
            """, [
                request.POST.get("salutation"),
                request.POST.get("first_mid_name"),
                request.POST.get("last_name"),
                request.POST.get("country_code"),
                request.POST.get("mobile_number"),
                request.POST.get("tanggal_lahir"),
                request.POST.get("kewarganegaraan"),
                email
            ])
        request.session["user_name"]       = f"{request.POST.get('first_mid_name')} {request.POST.get('last_name')}"
        request.session["user_salutation"] = request.POST.get("salutation")
        return render(request, "profile_member.html", {
            "member":  _get_member(email),
            "success": "Profil berhasil diperbarui!"
        })
    except Exception as e:
        return render(request, "profile_member.html", {
            "member": _get_member(email),
            "error":  str(e)
        })

@csrf_exempt
@require_http_methods(["GET", "POST"])
def profile_staf(request):
    if not request.session.get("user_email") or request.session.get("user_role") != "staf":
        return redirect("accounts:login")

    email = request.session["user_email"]

    if request.method == "GET":
        return render(request, "profile_staf.html", {"staf": _get_staf(email)})

    try:
        with connection.cursor() as cur:
            cur.execute("""
                UPDATE PENGGUNA SET
                    salutation      = %s,
                    first_mid_name  = %s,
                    last_name       = %s,
                    country_code    = %s,
                    mobile_number   = %s,
                    tanggal_lahir   = %s,
                    kewarganegaraan = %s
                WHERE email = %s
            """, [
                request.POST.get("salutation"),
                request.POST.get("first_mid_name"),
                request.POST.get("last_name"),
                request.POST.get("country_code"),
                request.POST.get("mobile_number"),
                request.POST.get("tanggal_lahir"),
                request.POST.get("kewarganegaraan"),
                email
            ])
        request.session["user_name"]       = f"{request.POST.get('first_mid_name')} {request.POST.get('last_name')}"
        request.session["user_salutation"] = request.POST.get("salutation")
        return render(request, "profile_staf.html", {
            "staf":    _get_staf(email),
            "success": "Profil berhasil diperbarui!"
        })
    except Exception as e:
        return render(request, "profile_staf.html", {
            "staf":  _get_staf(email),
            "error": str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def ubah_password(request):
    if not request.session.get("user_email"):
        return redirect("accounts:login")

    email            = request.session["user_email"]
    password_lama    = request.POST.get("password_lama", "").strip()
    password_baru    = request.POST.get("password_baru", "").strip()
    password_confirm = request.POST.get("password_confirm", "").strip()
    role             = request.session.get("user_role")
    template         = "profile_member.html" if role == "member" else "profile_staf.html"

    def render_with_data(context):
        if role == "member":
            context["member"] = _get_member(email)
        else:
            context["staf"] = _get_staf(email)
        return render(request, template, context)

    if not password_lama or not password_baru or not password_confirm:
        return render_with_data({"password_error": "Semua field password wajib diisi."})

    if len(password_baru) < 8:
        return render_with_data({"password_error": "Password baru minimal 8 karakter."})

    if password_baru != password_confirm:
        return render_with_data({"password_error": "Konfirmasi password tidak cocok."})

    try:
        with connection.cursor() as cur:
            cur.execute("SELECT password FROM PENGGUNA WHERE email = %s", [email])
            hash_lama = cur.fetchone()[0]

        # Compare pakai Django built-in
        if not check_password(password_lama, hash_lama):
            return render_with_data({"password_error": "Password lama tidak sesuai."})

        # Hash baru pakai Django built-in
        hash_baru = make_password(password_baru)
        with connection.cursor() as cur:
            cur.execute(
                "UPDATE PENGGUNA SET password = %s WHERE email = %s",
                [hash_baru, email]
            )

        return render_with_data({"password_success": "Password berhasil diubah!"})

    except Exception as e:
        return render_with_data({"password_error": str(e)})
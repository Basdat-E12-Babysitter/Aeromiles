import json
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


# ── HELPER ───────────────────────────────────────────────────────────────────
def _require_staf(request):
    return request.session.get("user_role") == "staf"

def _require_member(request):
    return request.session.get("user_role") == "member"


# ── KELOLA MEMBER (STAF) ─────────────────────────────────────────────────────
def kelola_member(request):
    if not _require_staf(request):
        return redirect("accounts:login")
    return render(request, "membership/kelola_member.html")


@csrf_exempt
@require_http_methods(["GET"])
def get_members(request):
    if not _require_staf(request):
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        with connection.cursor() as cur:
            cur.execute("""
                SELECT m.email, m.nomor_member, m.tanggal_bergabung,
                       m.id_tier, m.total_miles, m.award_miles,
                       p.salutation, p.first_mid_name, p.last_name,
                       p.country_code, p.mobile_number, p.tanggal_lahir, p.kewarganegaraan,
                       t.nama
                FROM MEMBER m
                JOIN PENGGUNA p ON m.email = p.email
                LEFT JOIN TIER t ON m.id_tier = t.id_tier
                ORDER BY m.nomor_member
            """)
            cols = [col[0] for col in cur.description]
            members = [dict(zip(cols, row)) for row in cur.fetchall()]
        return JsonResponse(members, safe=False)
    except Exception as e:
        error_msg = str(e)
        if "ERROR:" in error_msg:
            error_msg = error_msg.split("ERROR:")[-1].strip()
        return JsonResponse({"error": error_msg}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def tambah_member(request):
    if not _require_staf(request):
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        data            = json.loads(request.body)
        email           = data.get("email", "").strip()
        password        = data.get("password", "").strip()
        salutation      = data.get("salutation", "").strip()
        first_mid_name  = data.get("first_mid_name", "").strip()
        last_name       = data.get("last_name", "").strip()
        country_code    = data.get("country_code", "").strip()
        mobile_number   = data.get("mobile_number", "").strip()
        tanggal_lahir   = data.get("tanggal_lahir", "").strip()
        kewarganegaraan = data.get("kewarganegaraan", "").strip()

        if not all([email, password, first_mid_name, last_name]):
            return JsonResponse({"error": "Field wajib tidak boleh kosong."}, status=400)

        import bcrypt
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        with connection.cursor() as cur:
            cur.execute("""
                INSERT INTO PENGGUNA
                    (email, password, salutation, first_mid_name, last_name,
                     country_code, mobile_number, tanggal_lahir, kewarganegaraan)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [email, hashed, salutation, first_mid_name, last_name,
                  country_code, mobile_number, tanggal_lahir, kewarganegaraan])

            cur.execute("""
                INSERT INTO MEMBER (email, tanggal_bergabung, id_tier, award_miles, total_miles)
                VALUES (%s, CURRENT_DATE, 'T001', 0, 0)
            """, [email])

            cur.execute("SELECT nomor_member FROM MEMBER WHERE email = %s", [email])
            nomor_member = cur.fetchone()[0]

        return JsonResponse({"success": True, "nomor_member": nomor_member})

    except Exception as e:
        error_msg = str(e)
        if "ERROR:" in error_msg:
            error_msg = error_msg.split("ERROR:")[-1].strip()
        return JsonResponse({"error": error_msg}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def edit_member(request, email):
    if not _require_staf(request):
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        data = json.loads(request.body)
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
                data.get("salutation"), data.get("first_mid_name"),
                data.get("last_name"), data.get("country_code"),
                data.get("mobile_number"), data.get("tanggal_lahir"),
                data.get("kewarganegaraan"), email
            ])

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def hapus_member(request, email):
    if not _require_staf(request):
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        with connection.cursor() as cur:
            # Hapus data terkait dulu (sesuai urutan FK)
            cur.execute("DELETE FROM REDEEM WHERE email_member = %s", [email])
            cur.execute("DELETE FROM TRANSFER WHERE email_member_1 = %s OR email_member_2 = %s", [email, email])
            cur.execute("DELETE FROM CLAIM_MISSING_MILES WHERE email_member = %s", [email])
            cur.execute("DELETE FROM MEMBER_AWARD_MILES_PACKAGE WHERE email_member = %s", [email])
            cur.execute("DELETE FROM IDENTITAS WHERE email_member = %s", [email])
            cur.execute("DELETE FROM MEMBER WHERE email = %s", [email])
            cur.execute("DELETE FROM PENGGUNA WHERE email = %s", [email])

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ── IDENTITAS (MEMBER) ───────────────────────────────────────────────────────
def identitas(request):
    if not _require_member(request):
        return redirect("accounts:login")
    return render(request, "membership/identitas.html")


@csrf_exempt
@require_http_methods(["POST"])
def tambah_identitas(request):
    if not _require_member(request):
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        data            = json.loads(request.body)
        email           = request.session["user_email"]
        nomor           = data.get("nomor", "").strip()
        jenis           = data.get("jenis", "").strip()
        negara_penerbit = data.get("negara_penerbit", "").strip()
        tanggal_terbit  = data.get("tanggal_terbit", "").strip()
        tanggal_habis   = data.get("tanggal_habis", "").strip()

        if not all([nomor, jenis, negara_penerbit, tanggal_terbit, tanggal_habis]):
            return JsonResponse({"error": "Semua field wajib diisi."}, status=400)

        with connection.cursor() as cur:
            cur.execute("""
                INSERT INTO IDENTITAS
                    (nomor, email_member, jenis, negara_penerbit, tanggal_terbit, tanggal_habis)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [nomor, email, jenis, negara_penerbit, tanggal_terbit, tanggal_habis])

        return JsonResponse({"success": True})

    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg or "unique" in error_msg.lower():
            error_msg = "Nomor dokumen sudah terdaftar di sistem."
        return JsonResponse({"error": error_msg}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def edit_identitas(request, nomor):
    if not _require_member(request):
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        data  = json.loads(request.body)
        email = request.session["user_email"]

        with connection.cursor() as cur:
            cur.execute("""
                UPDATE IDENTITAS SET
                    jenis           = %s,
                    negara_penerbit = %s,
                    tanggal_terbit  = %s,
                    tanggal_habis   = %s
                WHERE nomor = %s AND email_member = %s
            """, [
                data.get("jenis"), data.get("negara_penerbit"),
                data.get("tanggal_terbit"), data.get("tanggal_habis"),
                nomor, email
            ])

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def hapus_identitas(request, nomor):
    if not _require_member(request):
        return JsonResponse({"error": "Unauthorized"}, status=403)
    try:
        email = request.session["user_email"]
        with connection.cursor() as cur:
            cur.execute(
                "DELETE FROM IDENTITAS WHERE nomor = %s AND email_member = %s",
                [nomor, email]
            )
        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
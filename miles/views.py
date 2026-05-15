# miles/views.py

import json
from django.shortcuts import render, redirect
from django.db import connection, IntegrityError
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

def _member_required(request):
    return (
        request.session.get("user_email") and
        request.session.get("user_role") == "member"
    )

def _staf_required(request):
    return (
        request.session.get("user_email") and
        request.session.get("user_role") == "staf"
    )

# KLAIM MISSING MILES (MEMBER)

def klaim_list(request):
    if not _member_required(request):
        return redirect("accounts:login")

    email = request.session["user_email"]

    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                c.id,
                c.maskapai AS kode_maskapai,
                mk.nama_maskapai AS maskapai,
                c.bandara_asal,
                c.bandara_tujuan,
                c.tanggal_penerbangan,
                c.flight_number,
                c.nomor_tiket,
                c.kelas_kabin,
                c.pnr,
                c.status_penerimaan,
                TO_CHAR(c.tanggal_penerbangan, 'YYYY-MM-DD') AS tanggal_penerbangan
            FROM CLAIM_MISSING_MILES c
            JOIN MASKAPAI mk ON mk.kode_maskapai = c.maskapai
            WHERE c.email_member = %s
            ORDER BY c.id ASC
        """, [email])
        cols  = [col[0] for col in cur.description]
        klaim = [dict(zip(cols, row)) for row in cur.fetchall()]

    # Dropdown: daftar maskapai & bandara untuk form
    with connection.cursor() as cur:
        cur.execute("SELECT kode_maskapai, nama_maskapai FROM MASKAPAI ORDER BY nama_maskapai")
        maskapai_list = [{"kode": r[0], "nama": r[1]} for r in cur.fetchall()]

        cur.execute("SELECT iata_code, nama FROM BANDARA ORDER BY nama")
        bandara_list  = [{"kode": r[0], "nama": r[1]} for r in cur.fetchall()]

    return render(request, "miles/claim_miles.html", {
        "klaim_list":    klaim,
        "maskapai_list": maskapai_list,
        "bandara_list":  bandara_list,
    })

@csrf_exempt
@require_http_methods(["POST"])
def klaim_create(request):
    if not _member_required(request):
        return redirect("accounts:login")

    email = request.session["user_email"]

    maskapai = request.POST.get("maskapai", "").strip()
    kelas_kabin = request.POST.get("kelas_kabin", "").strip()
    bandara_asal = request.POST.get("bandara_asal", "").strip()
    bandara_tujuan = request.POST.get("bandara_tujuan", "").strip()
    tanggal = request.POST.get("tanggal_penerbangan", "").strip()
    flight_number = request.POST.get("flight_number", "").strip().upper()
    nomor_tiket = request.POST.get("nomor_tiket", "").strip()
    pnr = request.POST.get("pnr", "").strip().upper()

    try:
        with connection.cursor() as cur:
            cur.execute("""
                INSERT INTO CLAIM_MISSING_MILES
                    (email_member, maskapai, bandara_asal, bandara_tujuan,
                     tanggal_penerbangan, flight_number, nomor_tiket,
                     kelas_kabin, pnr, status_penerimaan, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Menunggu', NOW())
            """, [email, maskapai, bandara_asal, bandara_tujuan,
                  tanggal, flight_number, nomor_tiket, kelas_kabin, pnr])

        messages.success(request, "Klaim berhasil diajukan.")

    except IntegrityError as e:
        err = str(e)
        if "ERROR:" in err:
            err = err.split("ERROR:")[-1].strip()
        messages.error(request, err)

    except Exception as e:
        err = str(e)
        if "ERROR:" in err:
            err = err.split("ERROR:")[-1].strip()
        messages.error(request, err)

    return redirect("miles:klaim_list")

@csrf_exempt
@require_http_methods(["POST"])
def klaim_update(request, pk):
    if not _member_required(request):
        return redirect("accounts:login")

    email = request.session["user_email"]

    # Pastikan klaim milik member ini dan masih Menunggu
    with connection.cursor() as cur:
        cur.execute("""
            SELECT status_penerimaan FROM CLAIM_MISSING_MILES
            WHERE id = %s AND email_member = %s
        """, [pk, email])
        row = cur.fetchone()

    if not row:
        messages.error(request, "Klaim tidak ditemukan.")
        return redirect("miles:klaim_list")
    if row[0] != "Menunggu":
        messages.error(request, "Hanya klaim berstatus Menunggu yang dapat diedit.")
        return redirect("miles:klaim_list")

    maskapai = request.POST.get("maskapai", "").strip()
    kelas_kabin = request.POST.get("kelas_kabin", "").strip()
    bandara_asal = request.POST.get("bandara_asal", "").strip()
    bandara_tujuan = request.POST.get("bandara_tujuan", "").strip()
    tanggal = request.POST.get("tanggal_penerbangan", "").strip()
    flight_number = request.POST.get("flight_number", "").strip().upper()
    nomor_tiket = request.POST.get("nomor_tiket", "").strip()
    pnr = request.POST.get("pnr", "").strip().upper()

    try:
        with connection.cursor() as cur:
            cur.execute("""
                UPDATE CLAIM_MISSING_MILES
                SET
                    maskapai = %s,
                    kelas_kabin = %s,
                    bandara_asal = %s,
                    bandara_tujuan = %s,
                    tanggal_penerbangan = %s,
                    flight_number = %s,
                    nomor_tiket = %s,
                    pnr = %s,
                    timestamp = NOW()
                WHERE id = %s
                  AND email_member = %s
                  AND status_penerimaan = 'Menunggu'
            """, [maskapai, kelas_kabin, bandara_asal, bandara_tujuan,
                  tanggal, flight_number, nomor_tiket, pnr, pk, email])

        messages.success(request, "Klaim berhasil diperbarui.")

    except IntegrityError as e:
        err = str(e)
        if "ERROR:" in err:
            err = err.split("ERROR:")[-1].strip()
        messages.error(request, err)

    except Exception as e:
        err = str(e)
        if "ERROR:" in err:
            err = err.split("ERROR:")[-1].strip()
        messages.error(request, err)

    return redirect("miles:klaim_list")


@csrf_exempt
@require_http_methods(["POST"])
def klaim_delete(request, pk):
    if not _member_required(request):
        return redirect("accounts:login")

    email = request.session["user_email"]

    with connection.cursor() as cur:
        cur.execute("""
            SELECT status_penerimaan FROM CLAIM_MISSING_MILES
            WHERE id = %s AND email_member = %s
        """, [pk, email])
        row = cur.fetchone()

    if not row:
        messages.error(request, "Klaim tidak ditemukan.")
        return redirect("miles:klaim_list")
    if row[0] != "Menunggu":
        messages.error(request, "Hanya klaim berstatus Menunggu yang dapat dihapus.")
        return redirect("miles:klaim_list")

    with connection.cursor() as cur:
        cur.execute("""
            DELETE FROM CLAIM_MISSING_MILES
            WHERE id = %s AND email_member = %s
        """, [pk, email])

    messages.success(request, "Klaim berhasil dihapus.")
    return redirect("miles:klaim_list")

def transfer_list(request):
    if not _member_required(request):
        return redirect("accounts:login")

    email = request.session["user_email"]

    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                email_member_1,
                email_member_2,
                TO_CHAR(timestamp, 'YYYY-MM-DD"T"HH24:MI:SS') AS timestamp,
                jumlah,
                catatan
            FROM TRANSFER
            WHERE email_member_1 = %s OR email_member_2 = %s
            ORDER BY timestamp DESC
        """, [email, email])
        cols = [col[0] for col in cur.description]
        transfer_list = [dict(zip(cols, row)) for row in cur.fetchall()]

    return render(request, "miles/transfer_miles.html", {
        "transfer_list": transfer_list,
        "transfer_list_json": json.dumps(transfer_list),
        "award_miles": request.session.get("award_miles", 0),
        "user_email": email,
    })

@csrf_exempt
@require_http_methods(["POST"])
def transfer_create(request):
    if not _member_required(request):
        return redirect("accounts:login")

    email_pengirim = request.session["user_email"]
    email_penerima = request.POST.get("email_penerima", "").strip().lower()
    jumlah = request.POST.get("jumlah", "").strip()
    catatan = request.POST.get("catatan", "").strip() or None

    # Validasi input dasar
    if not email_penerima or not jumlah:
        messages.error(request, "Email penerima dan jumlah miles wajib diisi.")
        return redirect("miles:transfer_list")

    try:
        jumlah = int(jumlah)
        if jumlah <= 0:
            raise ValueError
    except ValueError:
        messages.error(request, "Jumlah miles harus berupa angka positif.")
        return redirect("miles:transfer_list")

    if email_pengirim == email_penerima:
        messages.error(request, "Tidak dapat transfer ke diri sendiri.")
        return redirect("miles:transfer_list")

    try:
        with connection.cursor() as cur:
            db_connection = connection.connection
            if db_connection is not None and hasattr(db_connection, "notices"):
                db_connection.notices.clear()

            # Cek penerima terdaftar sebagai member
            cur.execute("SELECT 1 FROM MEMBER WHERE email = %s", [email_penerima])
            if not cur.fetchone():
                messages.error(request, "Email penerima tidak ditemukan sebagai member.")
                return redirect("miles:transfer_list")

            # INSERT
            cur.execute("""
                INSERT INTO TRANSFER (email_member_1, email_member_2, timestamp, jumlah, catatan)
                VALUES (%s, %s, NOW(), %s, %s)
            """, [email_pengirim, email_penerima, jumlah, catatan])

        notice_text = None
        if db_connection is not None and hasattr(db_connection, "notices") and db_connection.notices:
            notice_text = db_connection.notices[-1].strip()
            if notice_text.startswith("NOTICE:"):
                notice_text = notice_text.split("NOTICE:", 1)[1].strip()


        messages.success(request, notice_text)


        # Update session saldo setelah berhasil
        saldo_lama = int(request.session.get("award_miles", 0))
        request.session["award_miles"] = str(saldo_lama - jumlah)

    except Exception as e:
        err = str(e)
        if "ERROR:" in err:
            err = err.split("ERROR:")[-1].strip()
        messages.error(request, err)

    return redirect("miles:transfer_list")

@csrf_exempt
@require_http_methods(["GET", "POST"])
def kelola_klaim(request):
    if not _staf_required(request):
        return redirect("accounts:login")

    if request.method == "POST":
        klaim_id = request.POST.get("klaim_id")
        aksi = request.POST.get("aksi")
        staf_email = request.session["user_email"]

        if aksi not in ("Disetujui", "Ditolak"):
            messages.error(request, "Aksi tidak valid.")
            return redirect("miles:kelola_klaim")

        with connection.cursor() as cur:
            cur.execute("""
                UPDATE CLAIM_MISSING_MILES
                SET status_penerimaan = %s,
                    email_staf = %s
                WHERE id = %s
                  AND status_penerimaan = 'Menunggu'
            """, [aksi, staf_email, klaim_id])
            updated = cur.rowcount

        if updated == 0:
            messages.error(request, "Klaim tidak ditemukan atau sudah diproses.")
        else:
            messages.success(request, f"Klaim berhasil di-{aksi.lower()}.")

        return redirect("miles:kelola_klaim")

    # SELECT
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                c.id,
                c.email_member,
                mk.nama_maskapai AS maskapai,
                c.bandara_asal,
                c.bandara_tujuan,
                TO_CHAR(c.tanggal_penerbangan, 'YYYY-MM-DD') AS tanggal_penerbangan,
                c.flight_number,
                c.nomor_tiket,
                c.kelas_kabin,
                c.pnr,
                c.status_penerimaan,
                TO_CHAR(c.timestamp, 'YYYY-MM-DD"T"HH24:MI:SS') AS timestamp,
                CASE WHEN c.email_staf IS NULL THEN '' ELSE c.email_staf END
            FROM CLAIM_MISSING_MILES c
            JOIN MASKAPAI mk ON mk.kode_maskapai = c.maskapai
            ORDER BY c.timestamp DESC
        """)
        cols  = [col[0] for col in cur.description]
        klaim = [dict(zip(cols, row)) for row in cur.fetchall()]

    return render(request, "miles/kelola_klaim.html", {
        "klaim_list": klaim,
    })
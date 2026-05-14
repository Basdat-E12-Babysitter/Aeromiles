from django.shortcuts import render, redirect
from django.db import connection

def dashboard_member(request):
    if not request.session.get("user_email") or request.session.get("user_role") != "member":
        return redirect("accounts:login")
 
    email = request.session["user_email"]
 
    with connection.cursor() as cur:
        # Data member + tier info
        cur.execute("""
            SELECT
                m.nomor_member, m.award_miles, m.total_miles, m.tanggal_bergabung,
                t.nama AS nama_tier, t.minimal_tier_miles,
                pg.salutation, pg.first_mid_name, pg.last_name,
                pg.email, pg.country_code, pg.mobile_number,
                pg.tanggal_lahir, pg.kewarganegaraan
            FROM MEMBER m
            JOIN PENGGUNA pg ON pg.email = m.email
            JOIN TIER     t  ON t.id_tier = m.id_tier
            WHERE m.email = %s
        """, [email])
        row  = cur.fetchone()
        cols = [col[0] for col in cur.description]
        member = dict(zip(cols, row))
 
        # Tier berikutnya (untuk progress bar)
        cur.execute("""
            SELECT nama, minimal_tier_miles
            FROM TIER
            WHERE minimal_tier_miles > %s
            ORDER BY minimal_tier_miles ASC
            LIMIT 1
        """, [member["total_miles"]])
        next_tier_row = cur.fetchone()
        next_tier = None
        if next_tier_row:
            next_tier = {
                "nama": next_tier_row[0],
                "minimal_tier_miles": next_tier_row[1]
            }
 
        # Jumlah klaim pending
        cur.execute("""
            SELECT COUNT(*) FROM CLAIM_MISSING_MILES
            WHERE email_member = %s AND status_penerimaan = 'Menunggu'
        """, [email])
        klaim_pending_count = cur.fetchone()[0]
 
        # Riwayat transaksi terbaru — gabungan klaim, redeem, transfer, package
        cur.execute("""
            SELECT 'Klaim' AS tipe,
                   flight_number AS deskripsi,
                   kelas_kabin AS sub,
                   status_penerimaan AS status,
                   timestamp,
                   NULL::NUMERIC AS miles_delta
            FROM CLAIM_MISSING_MILES
            WHERE email_member = %s
 
            UNION ALL
 
            SELECT 'Redeem',
                   h.nama,
                   NULL,
                   'Berhasil',
                   r.timestamp,
                   -h.miles
            FROM REDEEM r
            JOIN HADIAH h ON h.kode_hadiah = r.kode_hadiah
            WHERE r.email_member = %s
 
            UNION ALL
 
            SELECT 'Transfer Keluar',
                   'Ke ' || pg.first_mid_name || ' ' || pg.last_name,
                   t.email_member_2,
                   'Berhasil',
                   t.timestamp,
                   -t.jumlah
            FROM TRANSFER t
            JOIN PENGGUNA pg ON pg.email = t.email_member_2
            WHERE t.email_member_1 = %s
 
            UNION ALL
 
            SELECT 'Transfer Masuk',
                   'Dari ' || pg.first_mid_name || ' ' || pg.last_name,
                   t.email_member_1,
                   'Berhasil',
                   t.timestamp,
                   t.jumlah
            FROM TRANSFER t
            JOIN PENGGUNA pg ON pg.email = t.email_member_1
            WHERE t.email_member_2 = %s
 
            UNION ALL
 
            SELECT 'Package',
                   'Beli Award Miles Package',
                   amp.id,
                   'Berhasil',
                   mamp.timestamp,
                   amp.jumlah_award_miles
            FROM MEMBER_AWARD_MILES_PACKAGE mamp
            JOIN AWARD_MILES_PACKAGE amp ON amp.id = mamp.id_award_miles_package
            WHERE mamp.email_member = %s
 
            ORDER BY timestamp DESC
            LIMIT 5
        """, [email, email, email, email, email])
        rows = cur.fetchall()
        cols = [col[0] for col in cur.description]
        transaksi_terbaru = [dict(zip(cols, r)) for r in rows]
 
    # Hitung progress bar tier
    progress_pct = 0
    miles_kurang  = 0
    if next_tier:
        target = next_tier["minimal_tier_miles"]
        current = member["total_miles"] or 0
        progress_pct = min(int((current / target) * 100), 100)
        miles_kurang  = max(target - current, 0)
 
    return render(request, "dashboard/member/dashboard.html", {
        "member":              member,
        "next_tier":           next_tier,
        "progress_pct":        progress_pct,
        "miles_kurang":        miles_kurang,
        "klaim_pending_count": klaim_pending_count,
        "transaksi_terbaru":   transaksi_terbaru,
    })


def dashboard_staf(request):
    if not request.session.get("user_email") or request.session.get("user_role") != "staf":
        return redirect("accounts:login")
 
    email = request.session["user_email"]
 
    with connection.cursor() as cur:
        # Data staf
        cur.execute("""
            SELECT
                pg.salutation, pg.first_mid_name, pg.last_name, pg.email,
                pg.country_code, pg.mobile_number, pg.tanggal_lahir, pg.kewarganegaraan,
                s.id_staf, mk.nama_maskapai, mk.kode_maskapai
            FROM PENGGUNA pg
            JOIN STAF     s  ON s.email          = pg.email
            JOIN MASKAPAI mk ON mk.kode_maskapai = s.kode_maskapai
            WHERE pg.email = %s
        """, [email])
        row  = cur.fetchone()
        cols = [col[0] for col in cur.description]
        staf = dict(zip(cols, row))
 
        # Count klaim menunggu (semua staf)
        cur.execute("""
            SELECT COUNT(*) FROM CLAIM_MISSING_MILES
            WHERE status_penerimaan = 'Menunggu'
        """)
        klaim_menunggu_count = cur.fetchone()[0]
 
        # Count klaim disetujui & ditolak oleh staf ini
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status_penerimaan = 'Disetujui') AS disetujui,
                COUNT(*) FILTER (WHERE status_penerimaan = 'Ditolak')   AS ditolak
            FROM CLAIM_MISSING_MILES
            WHERE email_staf = %s
        """, [email])
        row = cur.fetchone()
        klaim_disetujui_count = row[0]
        klaim_ditolak_count   = row[1]
 
        # Total diproses staf ini (untuk progress bar)
        total_diproses = klaim_disetujui_count + klaim_ditolak_count
        pct_disetujui  = int((klaim_disetujui_count / total_diproses) * 100) if total_diproses > 0 else 0
        pct_ditolak    = int((klaim_ditolak_count   / total_diproses) * 100) if total_diproses > 0 else 0
 
 
    return render(request, "dashboard/staf/dashboard.html", {
        "staf":                   staf,
        "klaim_menunggu_count":   klaim_menunggu_count,
        "klaim_disetujui_count":  klaim_disetujui_count,
        "klaim_ditolak_count":    klaim_ditolak_count,
        "total_diproses":         total_diproses,
        "pct_disetujui":          pct_disetujui,
        "pct_ditolak":            pct_ditolak,
    })
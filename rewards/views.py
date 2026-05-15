import json
from django.db import connection
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

def _require_member(request):
    if request.session.get('user_role') == 'member':
        return request.session.get('user_email')
    return None


def _require_staf(request):
    if request.session.get('user_role') == 'staf':
        return request.session.get('user_email')
    return None


def _rows_to_dicts(cursor):
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _row_to_dict(cursor):
    cols = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    return dict(zip(cols, row)) if row else None

# 1. REDEEM HADIAH (CR) — Member
@csrf_exempt
@require_http_methods(["GET", "POST"])
def redeem_hadiah(request):
    email = _require_member(request)
    if not email:
        return redirect('accounts:login')
    if request.method == 'GET':
        with connection.cursor() as cur:
            cur.execute(
                "SELECT award_miles FROM MEMBER WHERE email = %s",
                [email]
            )
            row = cur.fetchone()
            award_miles = row[0] if row else 0
            cur.execute("""
                SELECT
                    h.kode_hadiah,
                    h.nama,
                    h.miles,
                    h.deskripsi,
                    h.valid_start_date,
                    h.program_end,
                    h.id_penyedia,
                    COALESCE(mk.nama_maskapai, mt.nama_mitra, 'Penyedia #' || h.id_penyedia) AS nama_penyedia
                FROM HADIAH h
                LEFT JOIN MASKAPAI mk ON mk.id_penyedia = h.id_penyedia
                LEFT JOIN MITRA    mt ON mt.id_penyedia = h.id_penyedia
                WHERE h.program_end >= CURRENT_DATE
                  AND h.valid_start_date <= CURRENT_DATE
                ORDER BY h.miles ASC
            """)
            katalog = _rows_to_dicts(cur)
            cur.execute("""
                SELECT
                    r.kode_hadiah,
                    r.timestamp,
                    h.nama      AS nama_hadiah,
                    h.miles     AS miles_digunakan,
                    COALESCE(mk.nama_maskapai, mt.nama_mitra, 'Penyedia #' || h.id_penyedia) AS penyedia
                FROM REDEEM r
                JOIN HADIAH   h  ON h.kode_hadiah = r.kode_hadiah
                LEFT JOIN MASKAPAI mk ON mk.id_penyedia = h.id_penyedia
                LEFT JOIN MITRA    mt ON mt.id_penyedia = h.id_penyedia
                WHERE r.email_member = %s
                ORDER BY r.timestamp DESC
            """, [email])
            riwayat = _rows_to_dicts(cur)

        context = {
            'award_miles': award_miles,
            'katalog':     katalog,
            'riwayat':     riwayat,
            'katalog_json': json.dumps([
                {
                    'kode_hadiah':  item['kode_hadiah'],
                    'nama_hadiah':  item['nama'],
                    'harga_miles':  item['miles'],
                    'penyedia':     item['nama_penyedia'],
                    'deskripsi':    item['deskripsi'] or '',
                    'valid_start':  str(item['valid_start_date']),
                    'program_end':  str(item['program_end']),
                    'kategori':     _kategori_hadiah(item['nama']),
                }
                for item in katalog
            ], ensure_ascii=False),
            'riwayat_json': json.dumps([
                {
                    'kode_hadiah':    r['kode_hadiah'],
                    'nama_hadiah':    r['nama_hadiah'],
                    'miles_digunakan': r['miles_digunakan'],
                    'penyedia':       r['penyedia'],
                    'waktu':          r['timestamp'].isoformat() if r['timestamp'] else '',
                    'status':         'Berhasil',   
                }
                for r in riwayat
            ], ensure_ascii=False),
        }
        return render(request, 'redeem_hadiah.html', context)

    kode_hadiah = request.POST.get('kode_hadiah', '').strip()
    if not kode_hadiah:
        return redirect('rewards:redeem_list')

    try:
        with connection.cursor() as cur:
            cur.execute("""
                INSERT INTO REDEEM (email_member, kode_hadiah, timestamp)
                VALUES (%s, %s, NOW())
            """, [email, kode_hadiah])

            cur.execute(
                "SELECT nama, miles FROM HADIAH WHERE kode_hadiah = %s",
                [kode_hadiah]
            )
            hadiah_row = cur.fetchone()
            nama_hadiah = hadiah_row[0] if hadiah_row else kode_hadiah
            miles_hadiah = hadiah_row[1] if hadiah_row else 0

            cur.execute(
                "SELECT award_miles FROM MEMBER WHERE email = %s",
                [email]
            )
            new_award = cur.fetchone()

        if new_award:
            request.session['award_miles'] = str(new_award[0])

        pesan_sukses = (
            f'SUKSES: Redeem hadiah "{nama_hadiah}" berhasil. '
            f'Award miles Anda berkurang {miles_hadiah:,} miles.'
        )
        return render(request, 'redeem_hadiah.html',
                      _build_redeem_context(request, email, success=pesan_sukses))

    except Exception as e:
        error_msg = str(e)
        if 'ERROR:' in error_msg:
            error_msg = error_msg.split('ERROR:')[-1].strip()
        return render(request, 'redeem_hadiah.html',
                      _build_redeem_context(request, email, error=error_msg))


def _kategori_hadiah(nama: str) -> str:
    nama_lower = nama.lower()
    if any(k in nama_lower for k in ['voucher', 'diskon', 'cashback', 'hotel', 'lounge']):
        return 'Voucher'
    if any(k in nama_lower for k in ['upgrade', 'kabin', 'business', 'first']):
        return 'Upgrade'
    if any(k in nama_lower for k in ['merchandise', 'souvenir', 'tas', 'topi']):
        return 'Merchandise'
    return 'Lainnya'

def _build_redeem_context(request, email: str, success: str = None, error: str = None) -> dict:
    with connection.cursor() as cur:
        cur.execute("SELECT award_miles FROM MEMBER WHERE email = %s", [email])
        row = cur.fetchone()
        award_miles = row[0] if row else 0

        cur.execute("""
            SELECT h.kode_hadiah, h.nama, h.miles, h.deskripsi,
                   h.valid_start_date, h.program_end, h.id_penyedia,
                   COALESCE(mk.nama_maskapai, mt.nama_mitra, 'Penyedia #' || h.id_penyedia) AS nama_penyedia
            FROM HADIAH h
            LEFT JOIN MASKAPAI mk ON mk.id_penyedia = h.id_penyedia
            LEFT JOIN MITRA    mt ON mt.id_penyedia = h.id_penyedia
            WHERE h.program_end >= CURRENT_DATE
              AND h.valid_start_date <= CURRENT_DATE
            ORDER BY h.miles ASC
        """)
        katalog = _rows_to_dicts(cur)

        cur.execute("""
            SELECT r.kode_hadiah, r.timestamp, h.nama AS nama_hadiah,
                   h.miles AS miles_digunakan,
                   COALESCE(mk.nama_maskapai, mt.nama_mitra, 'Penyedia #' || h.id_penyedia) AS penyedia
            FROM REDEEM r
            JOIN HADIAH h ON h.kode_hadiah = r.kode_hadiah
            LEFT JOIN MASKAPAI mk ON mk.id_penyedia = h.id_penyedia
            LEFT JOIN MITRA    mt ON mt.id_penyedia = h.id_penyedia
            WHERE r.email_member = %s
            ORDER BY r.timestamp DESC
        """, [email])
        riwayat = _rows_to_dicts(cur)

    ctx = {
        'award_miles':   award_miles,
        'katalog':       katalog,
        'riwayat':       riwayat,
        'katalog_json': json.dumps([
            {
                'kode_hadiah': i['kode_hadiah'],
                'nama_hadiah': i['nama'],
                'harga_miles': i['miles'],
                'penyedia':    i['nama_penyedia'],
                'deskripsi':   i['deskripsi'] or '',
                'valid_start': str(i['valid_start_date']),
                'program_end': str(i['program_end']),
                'kategori':    _kategori_hadiah(i['nama']),
            }
            for i in katalog
        ], ensure_ascii=False),
        'riwayat_json': json.dumps([
            {
                'kode_hadiah':     r['kode_hadiah'],
                'nama_hadiah':     r['nama_hadiah'],
                'miles_digunakan': r['miles_digunakan'],
                'penyedia':        r['penyedia'],
                'waktu':           r['timestamp'].isoformat() if r['timestamp'] else '',
                'status':          'Berhasil',
            }
            for r in riwayat
        ], ensure_ascii=False),
    }
    if success:
        ctx['success'] = success
    if error:
        ctx['error'] = error
    return ctx

# 2. BELI PACKAGE MILES (CR) — Member
@csrf_exempt
@require_http_methods(["GET", "POST"])
def beli_package(request):
    email = _require_member(request)
    if not email:
        return redirect('accounts:login')

    if request.method == 'GET':
        with connection.cursor() as cur:
            cur.execute(
                "SELECT award_miles FROM MEMBER WHERE email = %s",
                [email]
            )
            row = cur.fetchone()
            award_miles = row[0] if row else 0
            cur.execute("""
                SELECT id, harga_paket, jumlah_award_miles
                FROM AWARD_MILES_PACKAGE
                ORDER BY jumlah_award_miles ASC
            """)
            packages = _rows_to_dicts(cur)

            cur.execute("""
                SELECT
                    map.id_award_miles_package AS package_id,
                    amp.jumlah_award_miles,
                    amp.harga_paket,
                    map.timestamp
                FROM MEMBER_AWARD_MILES_PACKAGE map
                JOIN AWARD_MILES_PACKAGE amp ON amp.id = map.id_award_miles_package
                WHERE map.email_member = %s
                ORDER BY map.timestamp DESC
            """, [email])
            riwayat_beli = _rows_to_dicts(cur)

        context = {
            'award_miles':   award_miles,
            'packages':      packages,
            'riwayat_beli':  riwayat_beli,
        }
        return render(request, 'beli_package.html', context)

    package_kode = request.POST.get('package_kode', '').strip()
    if not package_kode:
        return redirect('rewards:package_list')

    try:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT id, jumlah_award_miles, harga_paket FROM AWARD_MILES_PACKAGE WHERE id = %s",
                [package_kode]
            )
            pkg = _row_to_dict(cur)
            if not pkg:
                raise ValueError(f'Package "{package_kode}" tidak ditemukan.')
            cur.execute("""
                INSERT INTO MEMBER_AWARD_MILES_PACKAGE
                    (id_award_miles_package, email_member, timestamp)
                VALUES (%s, %s, NOW())
            """, [package_kode, email])

            cur.execute(
                "SELECT award_miles, total_miles FROM MEMBER WHERE email = %s",
                [email]
            )
            new_row = cur.fetchone()

        if new_row:
            request.session['award_miles'] = str(new_row[0])
            request.session['total_miles'] = str(new_row[1])

        jumlah = pkg['jumlah_award_miles']
        pesan_sukses = (
            f'SUKSES: Pembelian package berhasil. '
            f'Award miles dan total miles Anda bertambah {jumlah:,} miles.'
        )
        return render(request, 'beli_package.html',
                      _build_package_context(request, email, success=pesan_sukses))

    except Exception as e:
        error_msg = str(e)
        if 'ERROR:' in error_msg:
            error_msg = error_msg.split('ERROR:')[-1].strip()
        return render(request, 'beli_package.html',
                      _build_package_context(request, email, error=error_msg))


def _build_package_context(request, email: str, success: str = None, error: str = None) -> dict:
    with connection.cursor() as cur:
        cur.execute("SELECT award_miles FROM MEMBER WHERE email = %s", [email])
        row = cur.fetchone()
        award_miles = row[0] if row else 0

        cur.execute("""
            SELECT id, harga_paket, jumlah_award_miles
            FROM AWARD_MILES_PACKAGE
            ORDER BY jumlah_award_miles ASC
        """)
        packages = _rows_to_dicts(cur)

        cur.execute("""
            SELECT map.id_award_miles_package AS package_id,
                   amp.jumlah_award_miles, amp.harga_paket, map.timestamp
            FROM MEMBER_AWARD_MILES_PACKAGE map
            JOIN AWARD_MILES_PACKAGE amp ON amp.id = map.id_award_miles_package
            WHERE map.email_member = %s
            ORDER BY map.timestamp DESC
        """, [email])
        riwayat_beli = _rows_to_dicts(cur)

    ctx = {
        'award_miles':  award_miles,
        'packages':     packages,
        'riwayat_beli': riwayat_beli,
    }
    if success:
        ctx['success'] = success
    if error:
        ctx['error'] = error
    return ctx

# 3. INFO TIER (R) — Member
@require_http_methods(["GET"])
def info_tier(request):
    email = _require_member(request)
    if not email:
        return redirect('accounts:login')

    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                m.nomor_member,
                m.tanggal_bergabung,
                m.award_miles,
                m.total_miles,
                m.id_tier,
                t.nama          AS nama_tier,
                t.minimal_tier_miles,
                t.minimal_frekuensi_terbang,
                pg.first_mid_name,
                pg.last_name,
                pg.salutation
            FROM MEMBER m
            JOIN TIER     t  ON t.id_tier  = m.id_tier
            JOIN PENGGUNA pg ON pg.email   = m.email
            WHERE m.email = %s
        """, [email])
        member = _row_to_dict(cur)

        if not member:
            return redirect('accounts:login')
        cur.execute("""
            SELECT
                id_tier,
                nama,
                minimal_frekuensi_terbang,
                minimal_tier_miles
            FROM TIER
            ORDER BY minimal_tier_miles ASC
        """)
        semua_tier = _rows_to_dicts(cur)
        cur.execute("""
            SELECT COUNT(*) AS frekuensi_terbang
            FROM CLAIM_MISSING_MILES
            WHERE email_member = %s
              AND status_penerimaan = 'Disetujui'
        """, [email])
        frek_row = cur.fetchone()
        frekuensi_terbang = frek_row[0] if frek_row else 0

    total_miles   = member['total_miles'] or 0
    id_tier_saat  = member['id_tier']

    tier_saat_ini  = None
    tier_berikutnya = None
    for i, t in enumerate(semua_tier):
        if t['id_tier'] == id_tier_saat:
            tier_saat_ini = t
            if i + 1 < len(semua_tier):
                tier_berikutnya = semua_tier[i + 1]
            break

    if tier_berikutnya:
        base_miles    = tier_saat_ini['minimal_tier_miles'] if tier_saat_ini else 0
        target_miles  = tier_berikutnya['minimal_tier_miles']
        range_miles   = target_miles - base_miles
        earned_miles  = total_miles - base_miles
        progress_pct  = min(100, round((earned_miles / range_miles) * 100, 1)) if range_miles > 0 else 100
        miles_kurang  = max(0, target_miles - total_miles)
    else:
        progress_pct  = 100
        miles_kurang  = 0

    context = {
        'member':            member,
        'semua_tier':        semua_tier,
        'frekuensi_terbang': frekuensi_terbang,
        'tier_berikutnya':   tier_berikutnya,
        'progress_pct':      progress_pct,
        'miles_kurang':      miles_kurang,
        'id_tier_aktif':     id_tier_saat,
    }
    return render(request, 'info_tier.html', context)

# 4. LAPORAN & RIWAYAT TRANSAKSI (RD) — Staf
@csrf_exempt
@require_http_methods(["GET", "POST"])
def laporan_transaksi(request):
    email_staf = _require_staf(request)
    if not email_staf:
        return redirect('accounts:login')

    if request.method == 'POST':
        return _hapus_transaksi(request, email_staf)

    filter_tipe    = request.GET.get('tipe', '').strip()
    filter_dari    = request.GET.get('dari', '').strip()
    filter_sampai  = request.GET.get('sampai', '').strip()
    filter_member  = request.GET.get('member', '').strip()

    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM REDEEM")
        total_redeem = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM MEMBER_AWARD_MILES_PACKAGE")
        total_package = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM CLAIM_MISSING_MILES WHERE status_penerimaan = 'Disetujui'")
        total_klaim = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM TRANSFER")
        total_transfer = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM MEMBER")
        active_members = cur.fetchone()[0]

        total_transaksi = total_redeem + total_package + total_transfer + total_klaim

        stats = {
            'total_transaksi': total_transaksi,
            'total_redeem': total_redeem,
            'total_package': total_package,
            'active_members': active_members,
        }

        transaksi = _get_riwayat_transaksi(
            filter_tipe, filter_dari, filter_sampai, filter_member
        )

        cur.execute("""
            SELECT 
                pg.salutation,
                pg.first_mid_name,
                pg.last_name,
                m.email,
                t.nama AS nama_tier,
                m.total_miles
            FROM MEMBER m
            JOIN PENGGUNA pg ON m.email = pg.email
            JOIN TIER t ON m.id_tier = t.id_tier
            ORDER BY m.total_miles DESC
            LIMIT 10
        """)
        cols_rank = [col[0] for col in cur.description]
        ranking = [dict(zip(cols_rank, row)) for row in cur.fetchall()]

    context = {
        'stats':          stats,   
        'ranking':        ranking,  
        'transaksi':      transaksi,
        'filter_tipe':    filter_tipe,
        'filter_dari':    filter_dari,
        'filter_sampai':  filter_sampai,
        'filter_member':  filter_member,
        'transaksi_json': json.dumps([
            {
                'id':           t['id'],
                'noTrx':        t['no_trx'],
                'tipe':         t['tipe'],
                'email':        t['email'],
                'miles':        t['miles'],
                'tanggal':      str(t['timestamp']),
                'status':       t['status'],
                'deletable':    t['deletable'],
            }
            for t in transaksi
        ], ensure_ascii=False, default=str),
    }
    return render(request, 'laporan_transaksi.html', context)


def _get_riwayat_transaksi(filter_tipe: str, filter_dari: str, filter_sampai: str, filter_member: str) -> list:
    where_clauses = []
    params = []

    if filter_tipe:
        where_clauses.append("tipe = %s")
        params.append(filter_tipe)
    if filter_dari:
        where_clauses.append("timestamp::date >= %s")
        params.append(filter_dari)
    if filter_sampai:
        where_clauses.append("timestamp::date <= %s")
        params.append(filter_sampai)
    if filter_member:
        where_clauses.append("email_member ILIKE %s")
        params.append(f'%{filter_member}%')

    where_sql = ('WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''

    union_query = f"""
        SELECT *
        FROM (
            SELECT
                'TR-' || email_member_1 || '-' || email_member_2 || '-' || EXTRACT(EPOCH FROM timestamp)::bigint AS id_unik,
                'TRX-' || LPAD(ROW_NUMBER() OVER (ORDER BY timestamp)::text, 4, '0')   AS no_trx,
                'Transfer Miles'   AS tipe,
                email_member_1 AS email_member,
                jumlah          AS miles,
                timestamp,
                'Berhasil'   AS status,
                TRUE         AS deletable
            FROM TRANSFER

            UNION ALL

            SELECT
                'RD-' || email_member || '-' || r.kode_hadiah || '-' || EXTRACT(EPOCH FROM timestamp)::bigint AS id_unik,
                'TRX-' || LPAD(ROW_NUMBER() OVER (ORDER BY timestamp)::text, 4, '0') AS no_trx,
                'Redeem Hadiah'     AS tipe,
                email_member,
                h.miles      AS miles,
                r.timestamp,
                'Berhasil'   AS status,
                TRUE         AS deletable
            FROM REDEEM r
            JOIN HADIAH h ON h.kode_hadiah = r.kode_hadiah

            UNION ALL

            SELECT
                'PK-' || email_member || '-' || id_award_miles_package || '-' || EXTRACT(EPOCH FROM timestamp)::bigint AS id_unik,
                'TRX-' || LPAD(ROW_NUMBER() OVER (ORDER BY timestamp)::text, 4, '0') AS no_trx,
                'Pembelian Package' AS tipe,
                map.email_member,
                amp.jumlah_award_miles AS miles,
                map.timestamp,
                'Berhasil'   AS status,
                TRUE         AS deletable
            FROM MEMBER_AWARD_MILES_PACKAGE map
            JOIN AWARD_MILES_PACKAGE amp ON amp.id = map.id_award_miles_package

            UNION ALL

            SELECT
                'KM-' || id AS id_unik,
                'TRX-' || LPAD(id::text, 4, '0') AS no_trx,
                'Klaim Miles' AS tipe,
                email_member,
                1000          AS miles,
                timestamp,
                'Disetujui'   AS status,
                FALSE         AS deletable
            FROM CLAIM_MISSING_MILES
            WHERE status_penerimaan = 'Disetujui'

        ) AS semua_transaksi
        {{where_sql}}
        ORDER BY timestamp DESC
    """
    final_query = union_query.format(where_sql=where_sql)

    with connection.cursor() as cur:
        cur.execute(final_query, params)
        rows = cur.fetchall()
        cols = [col[0] for col in cur.description]
        
        result = []
        for row in rows:
            d = dict(zip(cols, row))
            d['id'] = d.get('id_unik')
            d['email'] = d.get('email_member')
            result.append(d)
            
        return result

def _get_top5_member(cur) -> list:
    try:
        cur.execute("SELECT * FROM get_top5_member()")
        return _rows_to_dicts(cur)
    except Exception:
        cur.execute("""
            SELECT
                m.email                                    AS email_member,
                pg.salutation || ' ' || pg.first_mid_name || ' ' || pg.last_name AS nama_lengkap,
                m.total_miles,
                RANK() OVER (ORDER BY m.total_miles DESC)::int AS peringkat
            FROM MEMBER m
            JOIN PENGGUNA pg ON pg.email = m.email
            ORDER BY m.total_miles DESC
            LIMIT 5
        """)
        return _rows_to_dicts(cur)


def _hapus_transaksi(request, email_staf: str):
    transaksi_id = request.POST.get('transaksi_id', '').strip()
    if not transaksi_id:
        return redirect('rewards:laporan_transaksi')

    error_msg = None
    success_msg = None

    try:
        if transaksi_id.startswith('KM-'):
            raise ValueError(
                'Riwayat klaim missing miles yang sudah disetujui tidak dapat dihapus.'
            )

        with connection.cursor() as cur:
            if transaksi_id.startswith('TR-'):
                parts = transaksi_id.split('-', 3)  
                if len(parts) < 4:
                    raise ValueError('Format ID transaksi Transfer tidak valid.')
                epoch   = parts[3]
                email1  = parts[1]
                email2  = parts[2]
                cur.execute("""
                    DELETE FROM TRANSFER
                    WHERE email_member_1 = %s
                      AND email_member_2 = %s
                      AND EXTRACT(EPOCH FROM timestamp)::bigint = %s
                """, [email1, email2, int(epoch)])

            elif transaksi_id.startswith('RD-'):
                parts = transaksi_id.split('-', 3)
                if len(parts) < 4:
                    raise ValueError('Format ID transaksi Redeem tidak valid.')
                epoch      = parts[3]
                member_email = parts[1]
                kode_hadiah  = parts[2]
                cur.execute("""
                    DELETE FROM REDEEM
                    WHERE email_member = %s
                      AND kode_hadiah  = %s
                      AND EXTRACT(EPOCH FROM timestamp)::bigint = %s
                """, [member_email, kode_hadiah, int(epoch)])

            elif transaksi_id.startswith('PK-'):
                parts = transaksi_id.split('-', 3)
                if len(parts) < 4:
                    raise ValueError('Format ID transaksi Package tidak valid.')
                epoch      = parts[3]
                member_email = parts[1]
                pkg_id       = parts[2]
                cur.execute("""
                    DELETE FROM MEMBER_AWARD_MILES_PACKAGE
                    WHERE email_member           = %s
                      AND id_award_miles_package = %s
                      AND EXTRACT(EPOCH FROM timestamp)::bigint = %s
                """, [member_email, pkg_id, int(epoch)])

            else:
                raise ValueError(f'Tipe transaksi tidak dikenali: {transaksi_id}')

        success_msg = f'Transaksi {transaksi_id} berhasil dihapus.'

    except Exception as e:
        error_msg = str(e)
        if 'ERROR:' in error_msg:
            error_msg = error_msg.split('ERROR:')[-1].strip()

    context = _build_laporan_context(email_staf)
    if success_msg:
        context['success'] = success_msg
    if error_msg:
        context['error'] = error_msg
    return render(request, 'laporan_transaksi.html', context)


def _build_laporan_context(email_staf: str, extra_filter: dict = None) -> dict:
    extra_filter = extra_filter or {}
    with connection.cursor() as cur:
        cur.execute("SELECT COALESCE(SUM(total_miles), 0) FROM MEMBER")
        total_miles_beredar = cur.fetchone()[0]

        cur.execute("""
            SELECT COALESCE(SUM(h.miles), 0)
            FROM REDEEM r JOIN HADIAH h ON h.kode_hadiah = r.kode_hadiah
            WHERE DATE_TRUNC('month', r.timestamp) = DATE_TRUNC('month', NOW())
        """)
        total_redeem_bulan_ini = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM CLAIM_MISSING_MILES
            WHERE status_penerimaan = 'Disetujui'
        """)
        total_klaim_disetujui = cur.fetchone()[0]

        top5 = _get_top5_member(cur)

    transaksi = _get_riwayat_transaksi('', '', '', '')

    return {
        'total_miles_beredar':    total_miles_beredar,
        'total_redeem_bulan_ini': total_redeem_bulan_ini,
        'total_klaim_disetujui':  total_klaim_disetujui,
        'transaksi':              transaksi,
        'top5':                   top5,
        'filter_tipe':   '',
        'filter_dari':   '',
        'filter_sampai': '',
        'filter_member': '',
        'transaksi_json': json.dumps([
            {
                'id':        t['id_unik'],
                'noTrx':     t['no_trx'],
                'tipe':      t['tipe'],
                'email':     t['email_member'],
                'miles':     t['miles'],
                'tanggal':   t['timestamp'],
                'status':    t['status'],
                'deletable': t['deletable'],
            }
            for t in transaksi
        ], ensure_ascii=False, default=str),
    }

# ENDPOINT AJAX — JSON API untuk katalog dan riwayat (opsional / progressive)
@require_http_methods(["GET"])
def api_katalog_hadiah(request):
    email = _require_member(request)
    if not email:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    with connection.cursor() as cur:
        cur.execute("""
            SELECT h.kode_hadiah, h.nama, h.miles, h.deskripsi,
                   h.valid_start_date, h.program_end,
                   COALESCE(mk.nama_maskapai, mt.nama_mitra, 'Penyedia #' || h.id_penyedia) AS penyedia
            FROM HADIAH h
            LEFT JOIN MASKAPAI mk ON mk.id_penyedia = h.id_penyedia
            LEFT JOIN MITRA    mt ON mt.id_penyedia = h.id_penyedia
            WHERE h.program_end >= CURRENT_DATE
              AND h.valid_start_date <= CURRENT_DATE
            ORDER BY h.miles ASC
        """)
        katalog = _rows_to_dicts(cur)

    return JsonResponse({
        'katalog': [
            {
                'kode_hadiah':  item['kode_hadiah'],
                'nama_hadiah':  item['nama'],
                'harga_miles':  item['miles'],
                'penyedia':     item['penyedia'],
                'deskripsi':    item['deskripsi'] or '',
                'valid_start':  str(item['valid_start_date']),
                'program_end':  str(item['program_end']),
                'kategori':     _kategori_hadiah(item['nama']),
            }
            for item in katalog
        ]
    }, safe=False)


@require_http_methods(["GET"])
def api_riwayat_redeem(request):
    email = _require_member(request)
    if not email:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    with connection.cursor() as cur:
        cur.execute("""
            SELECT r.kode_hadiah, r.timestamp, h.nama AS nama_hadiah,
                   h.miles AS miles_digunakan,
                   COALESCE(mk.nama_maskapai, mt.nama_mitra, 'Penyedia #' || h.id_penyedia) AS penyedia
            FROM REDEEM r
            JOIN HADIAH h ON h.kode_hadiah = r.kode_hadiah
            LEFT JOIN MASKAPAI mk ON mk.id_penyedia = h.id_penyedia
            LEFT JOIN MITRA    mt ON mt.id_penyedia = h.id_penyedia
            WHERE r.email_member = %s
            ORDER BY r.timestamp DESC
        """, [email])
        riwayat = _rows_to_dicts(cur)

    return JsonResponse({
        'riwayat': [
            {
                'kode_hadiah':     r['kode_hadiah'],
                'nama_hadiah':     r['nama_hadiah'],
                'miles_digunakan': r['miles_digunakan'],
                'penyedia':        r['penyedia'],
                'waktu':           r['timestamp'].isoformat() if r['timestamp'] else '',
                'status':          'Berhasil',
            }
            for r in riwayat
        ]
    }, safe=False)


@require_http_methods(["GET"])
def api_laporan_transaksi(request):
    email_staf = _require_staf(request)
    if not email_staf:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    filter_tipe   = request.GET.get('tipe',    '').strip()
    filter_dari   = request.GET.get('dari',    '').strip()
    filter_sampai = request.GET.get('sampai',  '').strip()
    filter_member = request.GET.get('member',  '').strip()

    transaksi = _get_riwayat_transaksi(filter_tipe, filter_dari, filter_sampai, filter_member)

    return JsonResponse({
        'transaksi': [
            {
                'id':        t['id_unik'],
                'noTrx':     t['no_trx'],
                'tipe':      t['tipe'],
                'email':     t['email_member'],
                'miles':     t['miles'],
                'tanggal':   str(t['timestamp']),
                'status':    t['status'],
                'deletable': t['deletable'],
            }
            for t in transaksi
        ]
    }, safe=False)
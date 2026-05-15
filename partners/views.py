import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import connection

# Hadiah
@csrf_exempt
@require_http_methods(["POST"])
def create_hadiah(request):
    try:
        data = json.loads(request.body)
        with connection.cursor() as cur:
            cur.execute("""
                INSERT INTO HADIAH (nama, miles, deskripsi, valid_start_date, program_end, id_penyedia)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING kode_hadiah
            """, [
                data['nama'],
                data['miles'],
                data.get('deskripsi', ''),
                data['valid_start_date'],
                data['program_end'],
                data['id_penyedia']
            ])
            kode = cur.fetchone()[0]
        return JsonResponse({'status': 'ok', 'kode_hadiah': kode})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def update_hadiah(request, kode_hadiah):
    try:
        data = json.loads(request.body)
        with connection.cursor() as cur:
            cur.execute("""
                UPDATE HADIAH
                SET nama = %s,
                    miles = %s,
                    deskripsi = %s,
                    valid_start_date = %s,
                    program_end = %s
                WHERE kode_hadiah = %s
            """, [
                data['nama'],
                data['miles'],
                data.get('deskripsi', ''),
                data['valid_start_date'],
                data['program_end'],
                kode_hadiah
            ])
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_hadiah(request, kode_hadiah):
    try:
        with connection.cursor() as cur:
            # Cek apakah periode sudah selesai
            cur.execute("""
                SELECT program_end FROM HADIAH WHERE kode_hadiah = %s
            """, [kode_hadiah])
            row = cur.fetchone()
            if not row:
                return JsonResponse({'status': 'error', 'message': 'Hadiah tidak ditemukan'}, status=404)
            if row[0] >= __import__('datetime').date.today():
                return JsonResponse({'status': 'error', 'message': 'Hadiah masih aktif, tidak bisa dihapus'}, status=400)
            cur.execute("DELETE FROM HADIAH WHERE kode_hadiah = %s", [kode_hadiah])
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
# Mitra
@csrf_exempt
@require_http_methods(["POST"])
def create_mitra(request):
    try:
        data = json.loads(request.body)
        with connection.cursor() as cur:
            # Insert PENYEDIA dulu (id auto dari sequence)
            cur.execute("INSERT INTO PENYEDIA DEFAULT VALUES RETURNING id")
            id_penyedia = cur.fetchone()[0]
            # Insert MITRA
            cur.execute("""
                INSERT INTO MITRA (email_mitra, id_penyedia, nama_mitra, tanggal_kerja_sama)
                VALUES (%s, %s, %s, %s)
            """, [
                data['email_mitra'],
                id_penyedia,
                data['nama_mitra'],
                data['tanggal_kerja_sama']
            ])
        return JsonResponse({'status': 'ok', 'id_penyedia': id_penyedia})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def update_mitra(request, email_mitra):
    try:
        data = json.loads(request.body)
        with connection.cursor() as cur:
            cur.execute("""
                UPDATE MITRA
                SET nama_mitra = %s,
                    tanggal_kerja_sama = %s
                WHERE email_mitra = %s
            """, [
                data['nama_mitra'],
                data['tanggal_kerja_sama'],
                email_mitra
            ])
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_mitra(request, email_mitra):
    try:
        with connection.cursor() as cur:
            # Ambil id_penyedia dulu
            cur.execute("SELECT id_penyedia FROM MITRA WHERE email_mitra = %s", [email_mitra])
            row = cur.fetchone()
            if not row:
                return JsonResponse({'status': 'error', 'message': 'Mitra tidak ditemukan'}, status=404)
            id_penyedia = row[0]
            # Hapus MITRA dulu, lalu PENYEDIA (cascade ke HADIAH)
            cur.execute("DELETE FROM MITRA WHERE email_mitra = %s", [email_mitra])
            cur.execute("DELETE FROM PENYEDIA WHERE id = %s", [id_penyedia])
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

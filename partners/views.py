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

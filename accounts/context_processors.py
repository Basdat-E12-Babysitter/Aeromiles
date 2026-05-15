from django.db import connection

def staf_context(request):
    if request.session.get("user_role") != "staf":
        return {}
    
    email = request.session.get("user_email")
    if not email:
        return {}
    
    try:
        with connection.cursor() as cur:
            cur.execute("""
                SELECT
                    pg.salutation, pg.first_mid_name, pg.last_name, pg.email,
                    pg.country_code, pg.mobile_number, pg.tanggal_lahir, pg.kewarganegaraan,
                    s.id_staf, mk.nama_maskapai, mk.kode_maskapai
                FROM PENGGUNA pg
                JOIN STAF s ON s.email = pg.email
                JOIN MASKAPAI mk ON mk.kode_maskapai = s.kode_maskapai
                WHERE pg.email = %s
            """, [email])
            row = cur.fetchone()
            cols = [col[0] for col in cur.description]
            return {'staf': dict(zip(cols, row))}
    except:
        return {}
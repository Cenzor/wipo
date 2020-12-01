from contextlib import closing
import pymysql
from pymysql.cursors import DictCursor


sql_query = {
    'stat': """INSERT INTO test_statistics (search_query, total,
            AE, AL, AU, BH, BN, BT, BW, CA, CH, CL, CR, DE, DK, DZ, EE, EG,
            EM, ES, FR, GE, GH, GM, ID, IL, `IN`, `IS`, IT, JO, JP, KE, KH,
            KR, KW, KZ, LA, MA, MD, MG, MK, MN, MW, MX, MY, MZ, NA, NZ, OM,
            PG, PH, RS, SD, SG, SM, SZ, TH, TN, `TO`, UA, US, UY, VN, WS,
            ZW, `WO AO`, WO, `WO 6TER`, `WHO INN`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
    'brand': """INSERT INTO test_brand (domain, search_query, brand, source,
             status, relevance, origin, holder, holder_country, number,
             app_data, image_class, nice_cl, image)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
}


# TODO: отрефакторить
def insert_db(data, data_type):
    with closing(pymysql.connect(
        host='localhost',
        user='wipo2',
        password='wipo2pass',
        db='wipo2',
        charset='utf8',
        cursorclass=DictCursor
    )) as connection:
        with connection.cursor() as cursor:
            if data_type == 'brand':
                try:
                    cursor.executemany(sql_query.get(data_type), data)
                except Exception:
                    connection.rollback()
                    cursor.executemany(sql_query.get(data_type), data)
                finally:
                    connection.commit()
            elif data_type == 'stat':
                values = tuple(data.values())
                try:
                    cursor.execute(sql_query.get(data_type), values)
                except Exception:
                    connection.rollback()
                    cursor.execute(sql_query.get(data_type), values)
                finally:
                    connection.commit()

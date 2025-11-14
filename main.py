import psycopg2

conn = psycopg2.connect(host='localhost',database='test',user='postgres',password = 'sudeki270385')
try:
    with conn:
        with conn.cursor() as cur:

            cur.execute("INSERT INTO user_account VALUES (%s, %s)", (6, 'Mary'))
            cur.execute("select * from user_account")

            rows = cur.fetchall()
            for row in rows:
                print(row)
finally:
    conn.close()

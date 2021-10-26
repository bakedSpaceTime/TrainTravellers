import mysql.connector
import yaml

with open('../app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())


db_conn = mysql.connector.connect(host=app_config["datastore"]["hostname"],
                                  user=app_config["datastore"]["user"],
                                  password=app_config["datastore"]["password"],
                                  database=app_config["datastore"]["db"],
                                  port=app_config["datastore"]["port"],
                                  )


db_cursor = db_conn.cursor()
db_cursor.execute('''
        SELECT * FROM train_route
    ''')

res = db_cursor.fetchall()
print([r for r in res])
print(len(res))


db_cursor.execute('''
        SELECT * FROM ticket_booking
    ''')

res = db_cursor.fetchall()
print([r for r in res])
print(len(res))


db_cursor.execute('''
      select value from (select count(ticket_id) as value from ticket_booking group by ticket_id) t1 where value > 1;
    ''')

res = db_cursor.fetchall()
print([r for r in res])
print(len(res))

db_cursor.execute('''
      select count(ticket_id) as value from ticket_booking group by ticket_id;
    ''')

res = db_cursor.fetchall()
print([r for r in res])
print(len(res))

db_conn.close()

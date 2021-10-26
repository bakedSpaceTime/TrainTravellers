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
        CREATE TABLE train_route
        (id INT NOT NULL AUTO_INCREMENT,
        route_id INTEGER NOT NULL,
        train_line VARCHAR(100) NOT NULL,
        route_origin VARCHAR(100) NOT NULL,
        route_destination VARCHAR(100) NOT NULL,
        route_departure_time VARCHAR(100) NOT NULL,
        estimated_travel_time INTEGER NOT NULL,
        date_created VARCHAR(100) NOT NULL,
        CONSTRAINT train_route_pk PRIMARY KEY (id))
    ''')

db_cursor.execute('''
    CREATE TABLE ticket_booking
        (id INT NOT NULL AUTO_INCREMENT,
        ticket_id INTEGER NOT NULL ,
        cabin_class VARCHAR(5) NOT NULL,
        customer_name VARCHAR(100) NOT NULL,
        customer_email VARCHAR(100) NOT NULL,
        route_id INTEGER NOT NULL,
        date_created VARCHAR(100) NOT NULL,
        CONSTRAINT ticket_booking_pk PRIMARY KEY (id))
    ''')

db_conn.commit()
db_conn.close()

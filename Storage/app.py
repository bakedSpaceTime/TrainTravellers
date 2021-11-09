import connexion
from connexion import NoContent
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from base import Base
from train_route import TrainRoute
from ticket_booking import TicketBooking
from datetime import datetime
import logging.config
import yaml
from threading import Thread
from pykafka import KafkaClient
from pykafka.common import OffsetType
import json


def add_train_route(body):
    """ Receives a train route schedule """

    est_dept_tm_obj = datetime.strptime(body['route_departure_time'], "%Y-%m-%dT%H:%M:%S.%fZ")

    tr = TrainRoute(body['route_id'],
                    body['train_line'],
                    body['route_origin'],
                    body['route_destination'],
                    est_dept_tm_obj,
                    body['estimated_travel_time'], )

    with DB_SESSION() as session:
        session.add(tr)
        session.commit()

    logger.debug(f"Stored event /route/schedule request with a unique id of {body['route_id']}")

    # return NoContent, 201


def add_ticket_booking(body):
    """ Receives a ticket booking """

    tb = TicketBooking(body['ticket_id'],
                       body['cabin_class'],
                       body['customer_name'],
                       body['customer_email'],
                       body['route_id'])

    with DB_SESSION() as session:
        session.add(tb)
        session.commit()

    logger.debug(f"Stored event /route/book request with a unique id of {body['ticket_id']}")

    # return NoContent, 201


def get_ticket_booking(start_timestamp, end_timestamp):

    start_timestamp_dt = datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    end_timestamp_dt = datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")

    with DB_SESSION() as session:
        tickets = session.query(TicketBooking).filter(
            and_(
                TicketBooking.date_created >= start_timestamp_dt,
                TicketBooking.date_created < end_timestamp
            )
        )

    return [tkt.to_dict() for tkt in tickets], 200


def get_train_route(start_timestamp, end_timestamp):

    start_timestamp_dt = datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    end_timestamp_dt = datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")

    with DB_SESSION() as session:
        routes = session.query(TrainRoute).filter(
            and_(
                TrainRoute.date_created >= start_timestamp_dt,
                TrainRoute.date_created < end_timestamp
            )
        )

    return [rt.to_dict() for rt in routes], 200


def process_messages():
    """ Process event messages """

    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"

    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    # Create a consume on a consumer group, that only reads new messages
    # (uncommitted messages) when the service re-starts (i.e., it doesn't
    # read all the old messages from the history in the message queue).
    consumer = topic.get_simple_consumer(consumer_group=b'event',
                                         reset_offset_on_start=False,
                                         auto_offset_reset=OffsetType.LATEST
                                         )

    # This is blocking - it will wait for a new message
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info(f"Message:{msg}")
        payload = msg["payload"]

        if msg["type"] == "train_route":
            add_train_route(payload)

        elif msg["type"] == "ticket_booking":
            add_ticket_booking(payload)

        # Commit the new message as being read
        consumer.commit_offsets()

# def init_app():
#     global app_config, log_config, logger, DB_ENGINE


with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)
logger = logging.getLogger('basicLogger')

db_string = (f'mysql+pymysql://{app_config["datastore"]["user"]}:{app_config["datastore"]["password"]}@'
             f'{app_config["datastore"]["hostname"]}:{app_config["datastore"]["port"]}/{app_config["datastore"]["db"]}')

DB_ENGINE = create_engine(db_string, pool_size=10, max_overflow=20)
DB_SESSION = sessionmaker(bind=DB_ENGINE)

Base.metadata.bind = DB_ENGINE
logger.info(f"Connecting to DB. Hostname: {app_config['datastore']['hostname']}, "
            f"Port: {app_config['datastore']['port']}")


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    # init_app()

    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()

    app.run(port=8090, debug=False, use_reloader=False)

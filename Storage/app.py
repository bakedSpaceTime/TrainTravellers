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
from pykafka.exceptions import NoBrokersAvailableError
import json
from time import sleep
import os


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

    logger.info(
        f"Request for Ticket Bookings between {start_timestamp_dt} and {end_timestamp_dt} received"
    )
    with DB_SESSION() as session:
        tickets = session.query(TicketBooking).filter(
            and_(
                TicketBooking.date_created >= start_timestamp_dt,
                TicketBooking.date_created < end_timestamp_dt
            )
        )
    logger.info(
        f"Request for Ticket Bookings between {start_timestamp_dt} and {end_timestamp_dt} returned "
        # f"{len(tickets)} results"
    )
    return [tkt.to_dict() for tkt in tickets], 200


def get_train_route(start_timestamp, end_timestamp):

    start_timestamp_dt = datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    end_timestamp_dt = datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")

    logger.info(
        f"Request for Train Routes between {start_timestamp_dt} and {end_timestamp_dt} received"
    )
    with DB_SESSION() as session:
        routes = session.query(TrainRoute).filter(
            and_(
                TrainRoute.date_created >= start_timestamp_dt,
                TrainRoute.date_created < end_timestamp_dt
            )
        )

    logger.info(
        f"Request for Train Routes between {start_timestamp_dt} and {end_timestamp_dt} returned"
        # f"{len(tickets)} results"
    )

    return [rt.to_dict() for rt in routes], 200


def connect_to_kafka():

    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"

    max_retries = app_config['events']['max_retries']
    retry_sleep = app_config['events']['retry_sleep']
    retries = 0
    connected = False

    while retries < max_retries and not connected:
        try:
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(app_config["events"]["topic"])]
        except NoBrokersAvailableError as err:
            retries = retries + 1
            logger.error(
                f"Failed to connect to Kafka broker at {app_config['events']['hostname']}. "
                f"Broker not found"
            )
        except Exception as err:
            retries = retries + 1
            logger.error(
                f"Failed to connect to Kafka broker at {app_config['events']['hostname']}. "
                f"Unknown error"
            )

        else:
            connected = True
            logger.info(f"Connected to Kafka broker at {app_config['events']['hostname']}")

        sleep(retry_sleep)

    if not connected:
        logger.error(
            f"Max retries reached({max_retries}) for connecting to Kafka broker at "
            f"{app_config['events']['hostname']}. Exiting application."
        )
        exit()
    else:
        return topic


def process_messages():
    """ Process event messages """

    topic = connect_to_kafka()

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


if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    APP_CONF_FILE = "/config/app_conf.yml"
    LOG_CONF_FILE = "/config/log_conf.yml"
else:
    APP_CONF_FILE = "app_conf.yml"
    LOG_CONF_FILE = "log_conf.yml"

with open(APP_CONF_FILE, 'r') as f:
    app_config = yaml.safe_load(f.read())

with open(LOG_CONF_FILE, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info(f"App Conf File: {APP_CONF_FILE}")
logger.info(f"Log Conf File: {LOG_CONF_FILE}")

db_string = (
    f'mysql+pymysql://{app_config["datastore"]["user"]}:{app_config["datastore"]["password"]}@'
    f'{app_config["datastore"]["hostname"]}:{app_config["datastore"]["port"]}/"
    f"{app_config["datastore"]["db"]}'
)

DB_ENGINE = create_engine(db_string, pool_size=10, max_overflow=20)
DB_SESSION = sessionmaker(bind=DB_ENGINE)

Base.metadata.bind = DB_ENGINE
logger.info(f"Connecting to DB. Hostname: {app_config['datastore']['hostname']}, "
            f"Port: {app_config['datastore']['port']}")

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", base_path="/storage", strict_validation=True, validate_responses=True)


if __name__ == "__main__":

    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()

    app.run(port=8090, debug=False, use_reloader=False)

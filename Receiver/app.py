import json
from pathlib import Path
import yaml
import logging
import logging.config
from pykafka import KafkaClient
from pykafka.exceptions import NoBrokersAvailableError
from datetime import datetime
from time import sleep
import os
import requests
import connexion
from connexion import NoContent

#test comment

def add_train_route(body):
    """ Receives a new train route event """

    logger.info(f"Received event /route/schedule request with a unique id of {body['route_id']}")

    send_kafka_msg("train_route", body)

    logger.info(f"Returned event /route/schedule request with a unique id of {body['route_id']}")

    return NoContent, 201


def add_ticket_booking(body):
    """ Receives a new ticket booking event event """

    logger.info(f"Received event /route/ticket request with a unique id of {body['ticket_id']}")

    send_kafka_msg("ticket_booking", body)

    logger.info(f"Returned event /route/ticket request with a unique id of {body['ticket_id']}")

    return NoContent, 201

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
            producer = topic.get_sync_producer()
        except NoBrokersAvailableError as err:
            retries = retries + 1
            logger.error(
                f"Failed to connect to Kafka broker at {app_config['events']['hostname']}."
                f" Broker not found"
            )
        except Exception as err:
            retries = retries + 1
            logger.error(
                f"Failed to connect to Kafka broker at {app_config['events']['hostname']}."
                f" Unknown error"
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
        return producer


def send_kafka_msg(payload_type: str, payload):
    """ Sends message to kafka broker """

    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"

    msg = {
        "type": payload_type,
        "datetime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "payload": payload
    }

    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))


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

logger.info(f"App Conf File: {app_conf_file}")
logger.info(f"Log Conf File: {log_conf_file}")

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", base_path="/receiver", strict_validation=True, validate_responses=True)

producer = connect_to_kafka()


if __name__ == '__main__':
    app.run(port=8080, debug=True)

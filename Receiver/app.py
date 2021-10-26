import connexion
import requests
from connexion import NoContent
import json
from pathlib import Path
import yaml
import logging
import logging.config
from pykafka import KafkaClient
from datetime import datetime

MAX_EVENTS = 12
EVENT_FILE = 'events.json'


def add_train_route(body):
    """ Receives a new train route event """

    logger.info(f"Received event /route/schedule request with a unique id of {body['route_id']}")

    # res = requests.post(app_config['route_schedule']['url'], json=body, headers={"content-type": "application/json"})
    send_kafka_msg("train_route", body)

    logger.info(f"Returned event /route/schedule request with a unique id of {body['route_id']}")

    return NoContent, 201


def add_ticket_booking(body):
    """ Receives a new ticket booking event event """

    logger.info(f"Received event /route/ticket request with a unique id of {body['ticket_id']}")

    # res = requests.post(app_config['route_ticket']['url'], json=body, headers={"content-type": "application/json"})
    send_kafka_msg("ticket_booking", body)

    logger.info(f"Returned event /route/ticket request with a unique id of {body['ticket_id']}")

    return NoContent, 201


def send_kafka_msg(payload_type: str, payload):
    """ Sends message to kafka broker """

    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"

    client = KafkaClient(hosts=hostname)

    topic = client.topics[str.encode(app_config['events']['topic'])]

    producer = topic.get_sync_producer()

    msg = {
        "type": payload_type,
        "datetime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "payload": payload
    }

    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))


with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)


if __name__ == '__main__':
    app.run(port=8080, debug=True)

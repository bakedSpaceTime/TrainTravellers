import connexion
import logging.config
import yaml
from pykafka import KafkaClient
from pykafka.common import OffsetType
import json
from flask_cors import CORS, cross_origin
import os


def get_train_route_reading(index):
    """ Get Train Route schedule in History """

    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"

    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    # Here we reset the offset on start so that we retrieve
    # messages at the beginning of the message queue.
    # To prevent the for loop from blocking, we set the timeout to
    # 100ms. There is a risk that this loop never stops if the
    # index is large and messages are constantly being received!
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    logger.info(f"Retrieving train route at index:{index}")
    try:
        event = get_message(consumer, index, "train_route")
        if event:
            return event, 200

    except:
        logger.error("No more messages found")

    logger.error("Could not find train route at index %d" % index)
    return {"message": "Not Found"}, 404


def get_ticket_booking_reading(index):
    """ Get Ticket booking in History """

    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"

    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    logger.info(f"Retrieving ticket booking at index:{index}")

    try:
        event = get_message(consumer, index, "ticket_booking")
        logger.debug(f"events: {event}")
        if event:
            return event, 200

    except:
        logger.error("No more messages found")

    logger.error("Could not find ticket booking at index %d" % index)
    return {"message": "Not Found"}, 404


def get_message(consumer, index, payload_type):
    ret = None
    i = 0
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)

        if msg['type'] == payload_type and i == index:
            ret = msg['payload']
            break
        if msg['type'] == payload_type:
            i = i + 1

    return ret


if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
  app_conf_file = "/config/app_conf.yml"
  log_conf_file = "/config/log_conf.yml"
else:
  app_conf_file = "app_conf.yml"
  log_conf_file = "log_conf.yml"

with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())

with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info(f"App Conf File: {app_conf_file}")
logger.info(f"Log Conf File: {log_conf_file}")

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'

if __name__ == "__main__":
    app.run(port=8110, debug=False)

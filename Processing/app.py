import connexion
import logging.config
import yaml
from apscheduler.schedulers.background import BackgroundScheduler
import json_store
import requests
from datetime import datetime
import pandas as pd
from flask_cors import CORS, cross_origin

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')


def populate_stats():
    """ Periodically update stats """

    cur_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    logger.info("Periodic Processing has Started")

    fname = app_config['datastore']['filename']

    prev_entry = json_store.get_entry(fname)

    if not prev_entry:
        logger.info("Using default datetime value for periodic stats query")
        prev_entry = {
            'count_routes': 0,
            'count_tickets': 0,
            'max_route_length': 0,
            'max_tickets_bought': 0,
            'date_created': '2016-08-29T09:12:33.001Z'
        }

    prev_timestamp = prev_entry['date_created']

    responses = {
        "Route Schedules": requests.get(f"{app_config['eventstore']['url']}{app_config['route_schedule']['path']}",
                                        params={'timestamp': prev_timestamp},
                                        headers={"content-type": "application/json"}),
        "Ticket Booking": requests.get(f"{app_config['eventstore']['url']}{app_config['route_ticket']['path']}",
                                       params={'timestamp': prev_timestamp},
                                       headers={"content-type": "application/json"}),
    }

    response_has_data = True
    for res_type, res_data in responses.items():
        if not res_data.status_code == 200:
            logger.error(f"Failed to retrieve {res_type} created after the time: {prev_timestamp}. "
                         f"Status code: {res_data.status_code}")
        else:
            logger.info(f"Received {len(res_data.json())} {res_type}from Storage Service")
            response_has_data = response_has_data and len(res_data.json()) != 0

    if response_has_data:
        stats = calc_route_stats(responses["Route Schedules"].json(), responses["Ticket Booking"].json(), prev_entry)
        stats["date_created"] = str(cur_timestamp)
    else:
        logger.info("No data retrieved from Storage service. Using previous stats entry")
        stats = prev_entry

    logger.info(f"Calculated Stats: {stats}")

    json_store.store_entry(stats, fname)


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats,
                  'interval',
                  seconds=app_config['scheduler']['period_sec'])
    sched.start()
    logger.info("Periodic Processing Started")


def calc_route_stats(route_data, ticket_data, prev_stats):
    rt_df = pd.DataFrame(route_data)
    tk_df = pd.DataFrame(ticket_data)

    stats = {
        "count_routes": len(route_data) + prev_stats["count_routes"],
        "count_tickets": len(route_data) + prev_stats["count_tickets"],
        "max_route_length": int(rt_df['estimated_travel_time'].max()),
        "max_tickets_bought": int(tk_df['customer_name'].value_counts().max()),
    }

    return stats


def get_stats():
    fname = app_config['datastore']['filename']
    stats = json_store.get_entry(fname)

    if stats:
        return stats, 200
    else:
        return {'message': "Statistics do not exist."}, 400


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)
app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)app.app.config['CORS_HEADERS'] = 'Content-Type'

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100, debug=False)

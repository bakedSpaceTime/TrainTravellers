import requests

x={
    "route_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "train_line": "CNRail",
    "route_origin": "Rotterdam",
    "route_destination": "Paris",
    "route_departure_time": "2016-08-29T09:12:33.001Z",
    "estimated_travel_time": 2
}

res = requests.post('http://localhost:8090/route/book', data=x)
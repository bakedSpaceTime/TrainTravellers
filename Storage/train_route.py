from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from base import Base
import datetime


class TrainRoute(Base):
    """ Train Route """

    __tablename__ = "train_route"

    id = Column(Integer, primary_key=True)
    route_id = Column(Integer, nullable=False)
    train_line = Column(String(100), nullable=False)
    route_origin = Column(String(100), nullable=False)
    route_destination = Column(String(100), nullable=False)
    route_departure_time = Column(DateTime, nullable=False)
    estimated_travel_time = Column(Integer, nullable=False)
    date_created = Column(DateTime, nullable=False)
    # booked_tickets = relationship("TicketBooking")

    def __init__(self,route_id, train_line, route_origin, route_destination, route_departure_time, estimated_travel_time):
        """ Initializes a train route entry """

        self.route_id = route_id
        self.train_line = train_line
        self.route_origin = route_origin
        self.route_destination = route_destination
        self.route_departure_time = route_departure_time
        self.estimated_travel_time = estimated_travel_time
        self.date_created = datetime.datetime.now()  # Sets the date/time record is created

    def to_dict(self):
        """ Dictionary Representation of a train route entry """

        self_d = {'route_id': self.route_id, 'train_line': self.train_line, 'route_origin': self.route_origin,
                  'route_destination': self.route_destination, 'route_departure_time': self.route_departure_time,
                  'estimated_travel_time': self.estimated_travel_time, 'date_created': self.date_created}

        return self_d

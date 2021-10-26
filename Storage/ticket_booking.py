from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime


class TicketBooking(Base):
    """ Train Route """

    __tablename__ = "ticket_booking"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, nullable=False)
    cabin_class = Column(String(5), nullable=False)
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(100), nullable=False)
    route_id = Column(String(100), nullable=False)
    date_created = Column(DateTime, nullable=False)

    def __init__(self, ticket_id, cabin_class, customer_name, customer_email, route_id):
        """ Initializes a train route entry """

        self.ticket_id = ticket_id
        self.cabin_class = cabin_class
        self.customer_name = customer_name
        self.customer_email = customer_email
        self.route_id = route_id
        self.date_created = datetime.datetime.now()  # Sets the date/time record is created

    def to_dict(self):
        """ Dictionary Representation of a train route entry """

        self_d = {'ticket_id': self.ticket_id, 'cabin_class': self.cabin_class, 'customer_name': self.customer_name,
                  'customer_email': self.customer_email, 'route_id': self.route_id, 'date_created': self.date_created}

        return self_d

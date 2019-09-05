from typing import List

from db import db
from models.ticket import TicketModel
from utils.conts import ticket_types


class EventModel(db.Model):
    """An event that should include its date and time"""

    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    tickets = db.relationship("TicketModel", back_populates="event")
    reservations = db.relationship(
        "ReservationModel", lazy="dynamic", cascade="all, delete-orphan"
    )

    # Adding one ticket model for each category (in this case VIP, Premium and Regular)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for ticket_type in ticket_types:
            self.tickets.append(TicketModel(ticket_type=ticket_type))

    @classmethod
    def find_by_id(cls, _id: int) -> "EventModel":
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_by_name(cls, name: str) -> "EventModel":
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_all(cls) -> List["EventModel"]:
        return cls.query.all()

    def find_by_ticket_type(self, ticket_type: str) -> "TicketModel":
        for ticket in self.tickets:
            if ticket.ticket_type == ticket_type:
                return ticket

    def check_availability(self, ticket_type: str) -> int:
        ticket = self.find_by_ticket_type(ticket_type)
        return ticket.number_available

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()

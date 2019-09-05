from datetime import datetime, timedelta
from uuid import uuid4

from db import db
from models.event import EventModel


class ReservationModel(db.Model):
    """A reservation should include which ticket type is intended and for what event, user has to be logged in to
    make a reservation. Each reservation has a unique identifier."""

    __tablename__ = "reservations"

    id = db.Column(db.String(50), primary_key=True)
    ticket_type = db.Column(db.String(10))
    expire_at = db.Column(db.DateTime, nullable=True)
    paid = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("UserModel")
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"))
    event = db.relationship("EventModel", lazy='subquery')
    remaining_time = db.Column(db.String(9))

    def __init__(self, user_id: int, event_id: int, ticket_type: str, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.event_id = event_id
        self.ticket_type = ticket_type
        self.id = uuid4().hex
        self.expire_at = datetime.now() + timedelta(minutes=15)
        self.paid = False
        self.remaining_time = '00:15:00'

    # Reservation expired, it is needed to restore the ticket to be available to be bought
    def update_event(self):
        event = EventModel.find_by_id(self.event_id)
        ticket = event.find_by_ticket_type(self.ticket_type)
        ticket.number_available -= 1
        self.save_to_db()

    @classmethod
    def find_by_id(cls, _id: str) -> "ReservationModel":
        return cls.query.filter_by(id=_id).first()

    @property
    def expired(self) -> bool:
        return datetime.now() > self.expire_at

    def update_expiration_time(self):
        if self.expired and not self.paid:
            self.remaining_time = "Expired"
        elif not self.expired and not self.paid:
            temp_date = self.expire_at - datetime.now()
            result = divmod(temp_date.days * 86400 + temp_date.seconds, 60)
            self.remaining_time = "00:{:02d}:{:02d}".format(*result)
        self.save_to_db()

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()

    def update_ticket_amount(self) -> None:
        db.session.add(self)
        if self.remaining_time != "Expired":
            self.event.find_by_ticket_type(self.ticket_type).number_available += 1
            self.remaining_time = "Expired"
        db.session.commit()

from db import db
from utils.conts import ticket_numbers


class TicketModel(db.Model):

    __tablename__ = "tickets"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ticket_type = db.Column(db.String(10))
    number_available = db.Column(db.Integer)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"))
    event = db.relationship('EventModel', back_populates="tickets")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ticket_type = kwargs["ticket_type"]
        self.number_available = ticket_numbers[self.ticket_type]

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()

from ma import ma
from models.event import EventModel
from schemas.reservation import ReservationSchema
from schemas.ticket import TicketSchema


class EventSchema(ma.ModelSchema):
    class Meta:
        model = EventModel
        exclude = ("reservations",)
    tickets = ma.Nested(TicketSchema, many=True)
    reservations = ma.Nested(ReservationSchema, many=True)




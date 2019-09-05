from ma import ma
from models.ticket import TicketModel


class TicketSchema(ma.ModelSchema):
    class Meta:
        model = TicketModel
        exclude = ("id", "event",)


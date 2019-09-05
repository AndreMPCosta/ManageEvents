from ma import ma
from models.reservation import ReservationModel
# from schemas.event import EventSchema


class ReservationSchema(ma.ModelSchema):
    class Meta:
        model = ReservationModel
        exclude = ("expire_at",)

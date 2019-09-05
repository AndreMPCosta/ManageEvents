from db import db
from models.reservation import ReservationModel


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), nullable=True, unique=True)
    password = db.Column(db.String(200), nullable=True)
    reservation = db.relationship(
        "ReservationModel", lazy="dynamic", cascade="all, delete-orphan"
    )

    # Internal, not used on the API
    @property
    def most_recent_reservation(self) -> "ReservationModel":
        # ordered by expiration time (in descending order)
        return self.confirmation.order_by(db.desc(ReservationModel.expire_at)).first()

    @classmethod
    def find_by_username(cls, username: str) -> "UserModel":
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_id(cls, _id: int) -> "UserModel":
        return cls.query.filter_by(id=_id).first()

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()

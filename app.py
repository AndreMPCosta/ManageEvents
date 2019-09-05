from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_restful import Api
from marshmallow import ValidationError

from blacklist import BLACKLIST
from db import db
from ma import ma
from models.event import EventModel
from models.reservation import ReservationModel
from resources.event import Event, EventList
from resources.reservation import Reservation
from resources.statistics import Statistics
from resources.user import UserRegister, User, UserLogin, UserLogout
from utils.conts import ticket_numbers

load_dotenv(".env", verbose=True)


app = Flask(__name__)
app.config.from_object("config")  # load default configs from config.py
app.config.from_envvar(
    "APPLICATION_SETTINGS"
)  # override with config.py (APPLICATION_SETTINGS points to config.py)
api = Api(app)


@app.before_first_request
def create_tables():
    db.create_all()
    check_startup_expired()
    fix_ticket_availability()


# If the app crashes, there is a need to update fields related to the expiration of the reservations
# Not the perfect solution using in the decorator before first request, needs better implementation
def check_startup_expired():
    expired_reservations = list(filter(lambda x: x.expired
                                       and x.remaining_time != "Expired"
                                       and not x.paid,
                                       ReservationModel.query.all()))
    list(map(lambda x: setattr(x, 'remaining_time', "Expired"),
             expired_reservations))

    def save_to_db(reservation):
        db.session.add(reservation)
        db.session.commit()

    list(map(lambda x: save_to_db(x),
             expired_reservations))


# Fixing availability of the tickets here
def fix_ticket_availability():
    events = EventModel.query.all()
    for event in events:
        for ticket_model in event.tickets:
            ticket_model.number_available = ticket_numbers[ticket_model.ticket_type]
    reservations = ReservationModel.query.all()
    for reservation in reservations:
        if reservation.paid or not reservation.expired:
            reservation.update_event()


@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return jsonify(err.messages), 400


# New JWT manager, for authentication purposes
jwt = JWTManager(app)


# This method will check if a token is blacklisted, and will be called automatically when blacklist is enabled
@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    return decrypted_token["jti"] in BLACKLIST


api.add_resource(Reservation, "/reservation", "/reservation/<string:reservation_id>")
api.add_resource(EventList, "/events")
api.add_resource(Event, "/event", "/event/id/<int:_id>", "/event/name/<string:name>")
api.add_resource(UserRegister, "/register")
api.add_resource(User, "/user/<int:user_id>")
api.add_resource(UserLogin, "/login")
api.add_resource(UserLogout, "/logout")
api.add_resource(Statistics, "/statistics/event/<int:event_id>", "/statistics/tickets/<string:ticket_type>",
                 "/statistics/events", "/statistics/tickets/<string:ticket_type>")


if __name__ == "__main__":
    db.init_app(app)
    db.app = app
    ma.init_app(app)
    # Start Flask APP
    app.run(host='0.0.0.0', port=5000, use_reloader=False)

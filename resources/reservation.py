from collections import namedtuple

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from models.event import EventModel
from models.reservation import ReservationModel
from schemas.reservation import ReservationSchema
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from utils.conts import ticket_types
from utils.validator import validate_request
from utils.verify_ticket_type import valid_ticket_type, convert_ticket_type

load_dotenv(".env", verbose=True)
from config import SQLALCHEMY_DATABASE_URI

reservation_schema = ReservationSchema()

# Configuring the scheduler

scheduler = BackgroundScheduler({
    'apscheduler.jobstores.default': {
        'type': 'sqlalchemy',
        'url': SQLALCHEMY_DATABASE_URI,
        'tablename': 'jobs'
    },
    'apscheduler.executors.default': {
        'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
        'max_workers': '100'
    },
    'apscheduler.executors.processpool': {
        'type': 'processpool',
        'max_workers': '5'
    },
    'apscheduler.job_defaults.coalesce': 'false',
    'apscheduler.job_defaults.max_instances': '3',
    'apscheduler.timezone': 'Europe/London',
})

# Starting the scheduler
if not scheduler.running:
    scheduler.start()


class CardError(Exception):
    pass


class PaymentError(Exception):
    pass


class CurrencyError(Exception):
    pass


PaymentResult = namedtuple('PaymentResult', ('amount', 'currency'))


class PaymentGateway:
    supported_currencies = ('EUR', 'PLN',)

    def charge(self, amount: int, token: str, currency: str = 'EUR'):
        if token == 'card_error':
            raise CardError("Your card has been declined")
        elif token == 'payment_error':
            raise PaymentError("Something went wrong with your transaction")
        elif currency not in self.supported_currencies:
            raise CurrencyError(f"Currency {currency} not supported")
        else:
            return {'PaymentResult': PaymentResult(amount, currency)._asdict()}, 200


class Reservation(Resource):
    # Retrieve a reservation by ID, and update the expiration time to show to the end user
    @classmethod
    def get(cls, reservation_id: str):
        reservation = ReservationModel.find_by_id(reservation_id)
        if not reservation:
            return {"message": "That reservation was not found on the system."}, 404
        reservation.update_expiration_time()
        return reservation_schema.dump(reservation), 200

    # User needs to be logged in to do a reservation, hence the jwt_required decorator
    @jwt_required
    def post(self, **kwargs):
        reservation_json = request.get_json()
        if 'reservation_id' not in kwargs:
            if not valid_ticket_type(reservation_json['ticket_type']):
                return {'message': 'That is not a valid ticket type. '
                                   'Please choose between {}, {} or {}.'.format(*ticket_types)}, 400
            reservation_json['ticket_type'] = convert_ticket_type(reservation_json['ticket_type'])
            user_id = get_jwt_identity()
            reservation_json['user_id'] = user_id
            event = EventModel.find_by_id(reservation_json['event_id'])
            if event:
                if not event.check_availability(reservation_json['ticket_type']):
                    return {'message': 'We are sorry to inform that {} '
                            'tickets are sold out.'.format(reservation_json['ticket_type'])}, 200
            else:
                return {'message': 'That is not a valid event'}, 404
            if not validate_request(reservation_json, ReservationModel):
                return {'message': 'Request invalid, please re-check your parameters.'}, 400
            # Unpack the request into a new reservation model
            reservation = ReservationModel(**reservation_json)
            # It is needed to remove one available ticket, since now it is reserved
            reservation.update_event()
            reservation.save_to_db()
            scheduler.add_job(reservation.update_ticket_amount,
                              'date', id=reservation.id, run_date=reservation.expire_at)
            return {"message": "Your reservation was successful."}, 201
        else:
            # Here the user is trying to pay for a reservation, since an ID was passed in the request
            reservation_json['reservation_id'] = kwargs['reservation_id']
            reservation = ReservationModel.find_by_id(kwargs['reservation_id'])
            if reservation:
                if reservation.expired:
                    return {'message': 'Sorry, that reservation is already expired. Please make a new reservation and '
                                       'pay after.'}, 400
                reservation_json['reservation'] = reservation
                # Popping keys from the dictionary, since this dict will be passed on later to our payment gateway
                reservation_json.pop('reservation_id', None)
                return self.pay(**reservation_json)
            else:
                return {"message": "That reservation was not found on the system."}, 404

    @staticmethod
    def pay(**kwargs):
        reservation = kwargs['reservation']
        kwargs.pop('reservation', None)
        payment_gateway = PaymentGateway()
        try:
            result = payment_gateway.charge(**kwargs)
            if result[1] == 200:
                reservation.paid = True
                reservation.remaining_time = "N/A"
                reservation.save_to_db()
            return result
        except CardError as e:
            return {"message": str(e)}, 400
        except PaymentError as e:
            return {"message": str(e)}, 400
        except CurrencyError as e:
            return {"message": str(e)}, 400
        except:
            return {"message": "Internal server error. Failed to process payment. "}, 500



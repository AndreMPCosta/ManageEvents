from flask_restful import Resource

from models.event import EventModel
from models.reservation import ReservationModel
from schemas.reservation import ReservationSchema

from utils.conts import ticket_types
from utils.verify_ticket_type import valid_ticket_type, convert_ticket_type

reservation_list_schema = ReservationSchema(many=True)


class Statistics(Resource):
    @classmethod
    def get(cls, **kwargs):
        # Statistics for a specific event
        if 'event_id' in kwargs:
            event = EventModel.find_by_id(kwargs['event_id'])
            if not event:
                return {"message": "Event not found."}, 404
            else:
                return cls.build_event_response(event), 200
        # Statistics for a specific ticket type
        elif 'ticket_type' in kwargs:
            if not valid_ticket_type(kwargs['ticket_type']):
                return {'message': 'That is not a valid ticket type. '
                                   'Please choose between {}, {} or {}.'.format(*ticket_types)}, 400
            kwargs['ticket_type'] = convert_ticket_type(kwargs['ticket_type'])
            return cls.build_ticket_response(kwargs['ticket_type'])
        else:
            # Statistics for every event in the database
            response = {'events': []}
            for event in EventModel.query.all():
                response['events'].append({event.name: {'id': event.id, **cls.build_event_response(event)}})
            return response

    @staticmethod
    def build_event_response(event):
        response = {'reservations': {'total': ReservationModel.query.filter_by(event_id=event.id).count()
                                     }}
        details = {}

        for ticket_type in ticket_types:
            total_reservations = ReservationModel.query.filter_by(ticket_type=ticket_type).\
                filter_by(event_id=event.id).count()
            paid_reservations = list(filter(lambda x: x.paid and getattr(x, 'ticket_type') == ticket_type
                                            and getattr(x, 'event_id') == event.id,
                                            ReservationModel.query.all()))
            not_paid_reservations = list(filter(lambda x: not x.paid and getattr(x, 'ticket_type') == ticket_type
                                                and getattr(x, 'event_id') == event.id,
                                                ReservationModel.query.all()))
            expired_reservations = list(filter(lambda x: getattr(x, 'remaining_time') == "Expired",
                                               not_paid_reservations))
            details[ticket_type] = {'total': total_reservations,
                                    'explicit':
                                        {
                                            'paid': len(paid_reservations),
                                            'not_paid':
                                                {
                                                 'expired': len(expired_reservations),
                                                 'not_expired': len(not_paid_reservations) - len(expired_reservations)
                                                 }
                                        }}
        response['reservations']['details'] = details
        return response

    @staticmethod
    def build_ticket_response(ticket_type):
        total_reservations = ReservationModel.query.filter_by(ticket_type=ticket_type).count()
        paid_reservations = list(filter(lambda x: x.paid and getattr(x, 'ticket_type') == ticket_type,
                                        ReservationModel.query.all()))
        not_paid_reservations = list(filter(lambda x: not x.paid and getattr(x, 'ticket_type') == ticket_type,
                                            ReservationModel.query.all()))
        expired_reservations = list(filter(lambda x: getattr(x, 'remaining_time') == "Expired",
                                           not_paid_reservations))
        details = {'total': total_reservations,
                                'explicit':
                                    {
                                        'paid': len(paid_reservations),
                                        'not_paid':
                                            {
                                                'expired': len(expired_reservations),
                                                'not_expired': len(not_paid_reservations) - len(expired_reservations)
                                            }
                                    }}
        return {ticket_type: details}

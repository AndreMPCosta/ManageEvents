from flask import request
from flask_restful import Resource

from models.event import EventModel
from schemas.event import EventSchema
from utils.validator import validate_request

event_schema = EventSchema()
event_list_schema = EventSchema(many=True)


class Event(Resource):
    @classmethod
    def get(cls, **kwargs):
        if '_id' in kwargs:
            # get occurrence by id
            event = EventModel.find_by_id(kwargs['_id'])
            if event:
                return event_schema.dump(event), 200
            else:
                return {"message": "Event not found."}, 404
        else:
            event = EventModel.find_by_name(kwargs['name'])
            if event:
                return event_schema.dump(event), 200
            else:
                return {"message": "Event not found."}, 404

    @classmethod
    def post(cls):
        # create an event with a date and a time
        event_json = request.get_json()
        if not validate_request(event_json, EventModel):
            return {'message': 'Request invalid, please re-check your parameters.'}, 400
        event = event_schema.load(event_json)
        try:
            event.save_to_db()
        except:
            return {"message": "Internal server error. Failed to create occurrence."}, 500
        return event_schema.dump(event), 201


class EventList(Resource):
    @classmethod
    def get(cls):
        return {"events": event_list_schema.dump(EventModel.find_all())}, 200

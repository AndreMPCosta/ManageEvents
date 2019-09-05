from sqlalchemy import inspect


def validate_request(request_json, model):
    mapper = inspect(model)
    # print([x.key for x in mapper.attrs])
    # print([key for key in request_json.keys()])
    # print(set([key for key in request_json.keys()]).issubset([x.key for x in mapper.attrs]))
    # print(type(request_json.keys()))

    if set([key for key in request_json.keys()]).issubset([x.key for x in mapper.attrs]):
        return True
    return False

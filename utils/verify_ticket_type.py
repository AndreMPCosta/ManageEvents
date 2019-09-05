from utils.conts import ticket_types


def valid_ticket_type(ticket_type):
    if ticket_type.lower() in list(map(lambda x: x.lower(), ticket_types)):
        return True
    return False


def convert_ticket_type(ticket_type):
    if ticket_type.lower() == 'vip':
        return "VIP"
    return ticket_type.lower().capitalize()

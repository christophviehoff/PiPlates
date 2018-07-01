import socket,threading
#Piplates classes
import piplates.RELAYplate as RELAY
import piplates.MOTORplate as MOTOR

VALID_PIPLATES_PIN_NUMBERS = [1,2,3,4,5,6,7,8,9,10,11,12,13,14] #relay module channels
VALID_HIGH_VALUES = [1, '1', 'HIGH','ON']
VALID_LOW_VALUES = [0, '0', 'LOW','OFF']
PIN_NAMES = {
    '1': 'Relay 1',
    '2': 'Relay 2',
    '3': 'Relay 3',
    '4': 'Relay 4',
    '5': 'Realy 5',
    '6': 'Relay 6',
    '7': 'Relay 7',
    '8': 'Relay 8',
    '9': 'Relay 9',
    '10': 'Relay 10',
    '11': 'Relay 11',
    '12': 'Relay 12',
    '13': 'Relay 13',
    '14': 'Relay 14'}

def is_relay_online(address):
    # match addresses to make sure the card is there
    if RELAY.getADDR(address) == address:
        return "online"
    else:
        return "offline"


def get_card_address():
    relays = []
    motors = []
    for address in range(0, 2):
        relays.append(RELAY.getADDR(address))

    for address in range(0, 8):
        motors.append(MOTOR.getADDR(address))

    # remove duplicates with set

    return {'Relays': list(set(relays)),
            'Steppers': list(set(motors))
            }

def pin_status(pin_number):
    if pin_number in VALID_PIPLATES_PIN_NUMBERS:

        value = _get_relaystate(pin_number)
        data = {'pin_number': pin_number,
                'pin_name': PIN_NAMES[str(pin_number)],
                'value': int(value),
                'address': 0 if pin_number<8 else 1,
                'status': (is_relay_online(0) if pin_number<8 else is_relay_online(1)),
                'error': None}
    else:
        data = {'status': 'ERROR',
                'error': 'Invalid pin number.'}

    return data


def pin_update(pin_number, value):
    if pin_number in VALID_PIPLATES_PIN_NUMBERS:

        if pin_number <8: #card 1
            if value:
                RELAY.relayON(0,pin_number)
            else:
                RELAY.relayOFF(0,pin_number)
        else: #card 2 valid pin numbers 1..7
            if value:
                RELAY.relayON(1,pin_number-7)
            else:
                RELAY.relayOFF(1,pin_number-7)

        new_value = _get_relaystate(pin_number)

        data = {'status': 'SUCCESS',
                'error': None,
                'pin_number': pin_number,
                'pin_name': PIN_NAMES[str(pin_number)],
                'new_value': int(new_value)}
    else:
        data = {'status': 'ERROR',
                'error': 'Invalid pin number or value.'}

    return data

#helper function
def _get_relaystate(pin_number):
    if pin_number == 1:
        value=bool(RELAY.relaySTATE(0) & 0x01)
    elif pin_number == 2:
        value=bool(RELAY.relaySTATE(0) & 0x02)
    elif pin_number == 3:
        value=bool(RELAY.relaySTATE(0) & 0x04)
    elif pin_number == 4:
        value = bool(RELAY.relaySTATE(0) & 0x08)
    elif pin_number == 5:
        value = bool(RELAY.relaySTATE(0) & 0x10)
    elif pin_number == 6:
        value = bool(RELAY.relaySTATE(0) & 0x20)
    elif pin_number == 7:
        value = bool(RELAY.relaySTATE(0) & 0x40)
    #next card
    elif pin_number == 8:
        value = bool(RELAY.relaySTATE(1) & 0x01)
    elif pin_number == 9:
        value = bool(RELAY.relaySTATE(1) & 0x02)
    elif pin_number == 10:
        value = bool(RELAY.relaySTATE(1) & 0x04)
    elif pin_number == 11:
        value = bool(RELAY.relaySTATE(1) & 0x08)
    elif pin_number == 12:
        value = bool(RELAY.relaySTATE(1) & 0x10)
    elif pin_number == 13:
        value = bool(RELAY.relaySTATE(1) & 0x20)
    elif pin_number == 14:
        value = bool(RELAY.relaySTATE(1) & 0x40)


    return value
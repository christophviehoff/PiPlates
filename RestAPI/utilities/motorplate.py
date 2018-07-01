import piplates.MOTORplate as MOTOR


VALID_PIPLATES_MOTOR_NUMBERS = [1,2,3,4,5,6,7,8] #motor ports
#VALID_HIGH_VALUES = [1, '1', 'HIGH']
#VALID_LOW_VALUES = [0, '0', 'LOW']
MOTOR_NAMES = {
    '1': 'PiPlates Motor 1',
    '2': 'PiPlates Motor 2',
    '3': 'PiPlates Motor 3',
    '4': 'PiPlates Motor 4',
    '5': 'PiPlates Motor 5',
    '6': 'PiPlates Motor 6',
    '7': 'PiPlates Motor 7',
    '8': 'PiPlates Motor 8'
}

def is_stepper_online(mtr_number):
    address=0
    if mtr_number in (3,4): address = 1
    elif mtr_number in (5,6): address = 2
    elif mtr_number in (7,8): address = 3

    if MOTOR.getADDR(address) == address:
        return {"address":address,
                "state":"online"}
    else:
        return {"address":address,
                "state":"offline"}

def mtr_status(mtr_number):
    if mtr_number in VALID_PIPLATES_MOTOR_NUMBERS:
        value = _get_motorstate(mtr_number)
        data = {'mtr_number': mtr_number,
                'mtr_name': MOTOR_NAMES[str(mtr_number)],
                'value': value,
                'status': is_stepper_online(mtr_number),
                'error': None}
    else:
        data = {'status': 'ERROR',
                'error': 'Invalid mtr number.'}
    return data

#helper function
def _get_motorstate(mtr_number):

    value1,value2 = None,None
    if mtr_number == 1:
        value1 = bool(MOTOR.getSENSORS(0) & 0x01)
        value2 = bool(MOTOR.getSENSORS(0) & 0x02)
    elif mtr_number == 2:
        value1 = bool(MOTOR.getSENSORS(0) & 0x04)
        value2 = bool(MOTOR.getSENSORS(0) & 0x08)
    elif mtr_number == 3:
        value1 = bool(MOTOR.getSENSORS(1) & 0x01)
        value2 = bool(MOTOR.getSENSORS(1) & 0x02)
    elif mtr_number == 4:
        value1 = bool(MOTOR.getSENSORS(1) & 0x04)
        value2 = bool(MOTOR.getSENSORS(1) & 0x08)
    elif mtr_number == 5:
        value1 = bool(MOTOR.getSENSORS(2) & 0x01)
        value2 = bool(MOTOR.getSENSORS(2) & 0x02)
    elif mtr_number == 6:
        value1 = bool(MOTOR.getSENSORS(2) & 0x04)
        value2 = bool(MOTOR.getSENSORS(2) & 0x08)
    elif mtr_number == 7:
        value1 = bool(MOTOR.getSENSORS(3) & 0x01)
        value2 = bool(MOTOR.getSENSORS(3) & 0x02)
    elif mtr_number == 8:
        value1 = bool(MOTOR.getSENSORS(3) & 0x04)
        value2 = bool(MOTOR.getSENSORS(3) & 0x08)

    return {"Sensor1":value1,
            "Sensor2":value2}
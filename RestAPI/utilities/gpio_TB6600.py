import RPi.GPIO as GPIO
from time import sleep

VALID_BCM_PIN_NUMBERS = [22,23,24] #relay module
VALID_MOVE_DIR=['CW','CCW']
VALID_HIGH_VALUES = [1, '1', 'HIGH']
VALID_LOW_VALUES = [0, '0', 'LOW']
PIN_NAMES = {'22': 'GPIO22-enable',
             '23': 'GPIO23-direction',
             '24': 'GPIO24-pulse'
              }

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in VALID_BCM_PIN_NUMBERS:
    GPIO.setup(pin, GPIO.OUT)


def pin_status(pin_number):
    if pin_number in VALID_BCM_PIN_NUMBERS:
        value = GPIO.input(pin_number)

        data = {'pin_number': pin_number,
                'pin_name': PIN_NAMES[str(pin_number)],
                'value': value,
                'status': 'SUCCESS',
                'error': None}
    else:
        data = {'status': 'ERROR',
                'error': 'Invalid pin number.'}

    return data


def pin_update(pin_number, value):
    if pin_number in VALID_BCM_PIN_NUMBERS:
        GPIO.output(pin_number, value)
        new_value = GPIO.input(pin_number)
        data = {'status': 'SUCCESS',
                'error': None,
                'pin_number': pin_number,
                'pin_name': PIN_NAMES[str(pin_number)],
                'new_value': new_value}
    else:
        data = {'status': 'ERROR',
                'error': 'Invalid pin number or value.'}

    return data

from stepper import Stepper


def stepper_test():
    #stepper variables
    # [stepPin, directionPin, enablePin]

    testStepper = Stepper([24, 22, 23])

    #test stepper
    testStepper.step(20000, "CW"); #steps, dir, speed, stayOn

    sleep(2)
    # test stepper
    testStepper.step(64000, "CCW");  # steps, dir, speed, stayOn

    return {"Stepper test": "done"}


def stepper_move(steps,dir,speed):
    #stepper variables
    # [stepPin, directionPin, enablePin]
    #print steps
    testStepper = Stepper([24, 22, 23])
    if dir in VALID_MOVE_DIR:
        #test stepper
        testStepper.step(steps, dir,speed) #steps, dir, speed, stayOn
        data={"Stepper move": "done",
         "dir": dir,
         "steps": steps,
         "speed": speed
         }
    else:
        data={'Move': 'ERROR',
            'error': 'Invalid direction.'}

    return data


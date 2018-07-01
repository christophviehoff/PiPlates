import RPi.GPIO as GPIO

#import wiringpi
import time

VALID_BCM_PIN_NUMBERS_OUT = [4,13,26,27] #outputs
VALID_BCM_PIN_NUMBERS_IN = [16] #inputs

VALID_BCM_PIN_NUMBERS=[4,13,26,27,16]

VALID_HIGH_VALUES = [1, '1', 'HIGH']
VALID_LOW_VALUES = [0, '0', 'LOW']
PIN_NAMES = {'13': 'GPIO13-spare',
             '26': 'GPIO26-spare',
             '27': 'GPIO27-rev',
              '4': 'GPIO04-fwd',
              '16': 'GPIO5-breakbeam'}

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
#wiringpi.wiringPiSetupGpio()

break_beam_index=0
index_time=0

for pin in VALID_BCM_PIN_NUMBERS_IN:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    #wiringpi.pinMode(pin,0)


for pin in VALID_BCM_PIN_NUMBERS_OUT:
    GPIO.setup(pin, GPIO.OUT)
    #wiringpi.pinMode(pin,1)


def my_callback(channel):
    global break_beam_index,index_time
    print "falling edge detected on 16", break_beam_index
    break_beam_index +=1
    index_time=time.time()


#print"event ADDED"
# when a falling edge is detected on gpio 5 break beam sensor, regardless of whatever
# else is happening in the program, the function my_callback will be run
#GPIO.add_event_detect(16, GPIO.FALLING, callback=my_callback,bouncetime=300)


def pin_status(pin_number):
    global break_beam_index,index_time
    if pin_number in VALID_BCM_PIN_NUMBERS:
        value = GPIO.input(pin_number)
        #value=wiringpi.digitalRead(pin_number)
        data = {'pin_number': pin_number,
                'pin_name': PIN_NAMES[str(pin_number)],
                'value': value,
                #'index count':break_beam_index,# if pin_number==5 else 'N/A'),
                'status': 'SUCCESS',
                'error': None}
    else:
        data = {'status': 'ERROR',
                'error': 'Invalid pin number.'}

    return data


def pin_update(pin_number, value):
    if pin_number in VALID_BCM_PIN_NUMBERS:
        GPIO.output(pin_number, value)
        #wiringpi.digitalWrite(pin_number, value)
        new_value = GPIO.input(pin_number)
        #new_value=wiringpi.digitalRead(pin_number)
        data = {'status': 'SUCCESS',
                'error': None,
                'pin_number': pin_number,
                'pin_name': PIN_NAMES[str(pin_number)],
                'new_value': new_value}
    else:
        data = {'status': 'ERROR',
                'error': 'Invalid pin number or value.'}

    return data


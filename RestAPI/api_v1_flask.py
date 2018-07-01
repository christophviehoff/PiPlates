from flask import Flask,jsonify,request
from utilities import gpio,i2c,relayplate,motorplate,gpio_TB6600,PiPlates
from flask_restful import Resource,Api
from waitress import serve
import piplates.RELAYplate as RELAY
import datetime
import socket
from transitions import Machine
from itertools import cycle

import RPi.GPIO as GPIO
from time import sleep


### global variables
mode = {"fsm":"disable",
        "motion":"enable"}



status = {"state": None,
          "count":0,
          "queue":None}


PORT=5000
HOSTNAME=socket.gethostname()+".local"

app =Flask(__name__)
api=Api(app)


#TODO create conveyor class


class Mcard:
    def __init__(self, name):
        self.name = None

    def set_name(self, name):
        self.name= name

    def get_name(self):
        return self.name

class Queue:
    def __init__(self,length):
        self.length=length
        #prepopulate the list with None
        self.items = [None] *self.length

    def __getitem__(self, pos):
        return self.items[pos]

    def show(self):
        return list(self.items)

    def isEmpty(self):
        return self.items == []

    def enqueue(self, item):
        self.items.insert(0,item)


    def enqueue9(self,item):
        for card in range(9):  #9 cards index 0..8
            self.items.insert(card,item)


    def dequeue(self):
        return self.items.pop()

    def index(self,name):
        #dismiss last item
        self.enqueue(name)
        self.dequeue()

    def update(self,pos,item):
        self.items[pos]=item

    def get_name(self,pos):
        return self.items[pos]


    def size(self):
        return len(self.items)

class Robot_cmd():
    def __init__(self):

        self.steps=0
        self.dir="CW"
        self.speed=1.0
        self.home_pos=0


    def pick(self,steps, dir,speed):

        self.steps=steps
        self.dir=dir
        self.speed=speed
        gpio_TB6600.stepper_move(self.steps, self.dir,self.speed)


    def place(self,steps,dir,speed):
        self.steps = steps
        self.dir = dir
        self.speed = speed
        gpio_TB6600.stepper_move(self.steps,self.dir,self.speed)


    def home(self):
        pass

class Conveyor_cmd():

    def __init__(self):
        RELAY.relayOFF(0, 1)

    def fwd(self):
        RELAY.relayON(0, 1)

    def rev(self):
        pass

    def stop(self):
        RELAY.relayOFF(0, 1)

    def reset(self):
        pass

class Conveyor_FSM(Machine):

    # states and transitions
    def __init__(self):
        self.running=True

        states = ['init','ready','start', 'stop', 'pickplace', 'eject']
        Machine.__init__(self, states=states, initial='init')

        self.add_transition('trigger', 'init', 'ready')
        self.add_transition('trigger', 'ready', 'start', conditions='is_enabled')
        self.add_transition('trigger', 'start', 'stop', conditions='is_beam_broken')
        self.add_transition('trigger', 'stop','pickplace',conditions='is_pickplace_ready')
        self.add_transition('trigger', 'pickplace', 'eject')
        self.add_transition('trigger', 'eject', 'ready')

        self.state = states[0]
        self.iterator = cycle([1,0,0,0,0,0,0,0,0])

        self.count=0  #trigger counter

    # define hardware objects at start
        self.conveyor=Conveyor_cmd()
        self.robot=Robot_cmd()

        # setup break beam sensor
        GPIO.setmode(GPIO.BCM)
        # GPIO 16 set up as input, pulled up to avoid false detection.
        GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)


    def on_enter_init(self):
        sleep(2)

    def on_enter_ready(self):
        sleep(2)

    def on_enter_start(self):
        self.conveyor.fwd()

    def on_enter_stop(self):
        self.conveyor.stop()
        q.index("None")  # mcard would be passing a obj

    def on_enter_pickplace(self):

        #TODO pickplace robot places 9 cards at once in queue
        #q.index("card")

        for pos in range(9):
            q.update(pos, "card")

        self.robot.pick(15000, "CW",1.0)
        sleep(1.0)
        self.robot.place(15000, "CCW", 1.0)

    def on_enter_eject(self):

        #position 13 eject test
        if q.get_name(13) is None:
            pass

        elif q.get_name(13) == "card":
            print ("ejecting...")
            q.update(13,None)
            sleep(1)
        else:
            #TODO
            pass

            #transition conditions


    def is_enabled(self):
        if mode["fsm"] == "enable":
            return True
        else:
            return False

    def is_beam_broken(self):
        global status
        print "Waiting for falling edge on port 16"
        GPIO.wait_for_edge(16, GPIO.FALLING)

        self.count += 1

        return True


    def is_pickplace_ready(self):
        # self.iterator = cycle([1,0,0,0,0]) defined in __init__
        if next(self.iterator):  # 1
            return True
        else:  # 0
            self.to_eject()
            return False


    # help functions
    def get_status(self):
        return self.state

    def get_index(self):
        return self.break_beam_index

    def run(self):
        global status
        global mode
        while self.running:

            if mode["motion"] == "enable":
                self.trigger()
                status = {"state":self.state,
                          "count":self.count,
                          "queue": q.show()}
                print (status)

            # normal exit condition
            if mode["fsm"] == "shutdown":
                self.running = False

            sleep(0.1)



class Conveyor(Resource):

    def post(self):
        self.conveyor = Conveyor_FSM()
        self.conveyor.run()
        return {"fsm": "shutdown"}

    def get(self):
        global status
        return status

class Mode(Resource):
    def post(self):
        global mode
        mode = request.get_json()
        return {"ack":True}

class Root(Resource):
    def get(self):
        return "<h1> Hello to my API</h1>"

class About(Resource):
    def get(self):
        about_me = [{
            "API": "api/v1",
            "Description": "PiPlates and I2C resources",
            "Hostname": (HOSTNAME,PORT),
            "Ip address":PiPlates.get_local_ip_address(),
            "Timestamp": str(datetime.datetime.today()),
            "Status": "online",
            "I2C": i2c.list_of_i2c_io(),
            "PiPlates":PiPlates.get_card_address()
        }]
        return {"AboutMe": about_me}

class Ping(Resource):
    def get(self):
        data = {"api_name": "Restful API",
                "version": "1.1",
                "status": "SUCCESS",
                "response": "pong"}
        return data

class Gpio(Resource):
    def get(self,pin):
        data = gpio.pin_status(pin)
        return data
    def post(self,pin):
        data = request.get_json()
        value = data["value"]
        if value in gpio.VALID_HIGH_VALUES:
            data = gpio.pin_update(pin, 1)
        elif value in gpio.VALID_LOW_VALUES:
            data = gpio.pin_update(pin, 0)
        else:
            data = {"status": "ERROR",
                    "error": "Invalid value."}
        return data

class GpioStatus(Resource):
    def get(self):
        data_list = []
        for pin in gpio.VALID_BCM_PIN_NUMBERS:
            data_list.append(gpio.pin_status(pin))
        return {'gpio data': data_list}

class GpioAllHigh(Resource):
    def post(self):
        data_list = []
        for pin in gpio.VALID_BCM_PIN_NUMBERS:
            data_list.append(gpio.pin_update(pin, 1))

        return {"gpio data": data_list}

class GpioAllLow(Resource):
    def post(self):
        data_list = []
        for pin in gpio.VALID_BCM_PIN_NUMBERS:
            data_list.append(gpio.pin_update(pin, 0))
        return {"gpio data": data_list}

class PiStack(Resource):
    def get(self):
        return PiPlates.get_card_address()

class Relay(Resource):
    def get(self,pin):
        data = relayplate.pin_status(pin)
        return data
    def post(self,pin):
        data = request.get_json()
        #assert (pin>0 and pin <15)
        if pin in relayplate.VALID_PIPLATES_PIN_NUMBERS:
            value = data["value"]
            if value in relayplate.VALID_HIGH_VALUES:
                data = relayplate.pin_update(pin, 1)
            elif value in relayplate.VALID_LOW_VALUES:
                data = relayplate.pin_update(pin, 0)
            else:
                data = {"status": "ERROR",
                    "error": "Invalid value."}
        else:
            data = {"status": "ERROR",
                    "error": "Invalid pin number."}
        return data

class RelayStatus(Resource):
    def get(self):
        data_list = []
        for pin in relayplate.VALID_PIPLATES_PIN_NUMBERS:
            data_list.append(relayplate.pin_status(pin))
        return {'PiPlates relay data': data_list}

class RelayAllHigh(Resource):
    def post(self):
        data_list = []
        for pin in relayplate.VALID_PIPLATES_PIN_NUMBERS:
            data_list.append(relayplate.pin_update(pin, 1))

        return {"PiPlates relay data": data_list}

class RelayAllLow(Resource):
    def post(self):
        data_list = []
        for pin in relayplate.VALID_PIPLATES_PIN_NUMBERS:
            data_list.append(relayplate.pin_update(pin, 0))

        return {"PiPlates relay data": data_list}

class StepperStatus(Resource):
    def get(self):
        data_list = []
        for mtr in motorplate.VALID_PIPLATES_MOTOR_NUMBERS:
            data_list.append(motorplate.mtr_status(mtr))
        return {'PiPlates stepper data': data_list}

class I2cStatus(Resource):
    def get(self):
        data_list = []
        for pin in i2c.VALID_I2C_PIN_NUMBERS:
            data_list.append(i2c.pin_status(pin))

        return {"i2c data": data_list}

class I2c(Resource):
    def get(self,pin):
        return i2c.pin_status(pin)

class GpioTB6600Status(Resource):
    def get(self):
        data_list = []
        for pin in gpio_TB6600.VALID_BCM_PIN_NUMBERS:
            data_list.append(gpio_TB6600.pin_status(pin))
        return {'gpio TB6600 data': data_list}

class StepperMove(Resource):

    def get(self):
        # TODO need to tread this motor test
        #t = threading.Thread(name='tb6600_test', target=gpio_TB6600.stepper_test)
        #t.start()
        #return {"Stepper test": "starting..."}  #done with the request
        result=gpio_TB6600.stepper_test()
        return result

    def post(self):
        data = request.get_json()
        steps = data["steps"]
        dir= data["dir"]
        speed=data["speed"]
        # TODO need to tread this motor move
        #t = threading.Thread(name='tb6600_test', target=gpio_TB6600.stepper_move,args=(steps,dir,speed))
        #t.start()
        #return {"Stepper move": "executed"}  # done with the request
        result=gpio_TB6600.stepper_move(steps,dir,speed)
        return result

api.add_resource(Root,'/')
api.add_resource(About,'/api/v1/about')
api.add_resource(Ping,'/api/v1/ping')


#Raspberry GPIO
api.add_resource(Gpio,'/api/v1/gpio/<int:pin>')
api.add_resource(GpioStatus,'/api/v1/gpio/status/')
api.add_resource(GpioAllHigh,'/api/v1/gpio/all-high')
api.add_resource(GpioAllLow,'/api/v1/gpio/all-low')


#Piplate relays
api.add_resource(Relay,'/api/v1/relay/<int:pin>')
api.add_resource(RelayStatus,'/api/v1/relay/status/')
api.add_resource(RelayAllHigh,'/api/v1/relay/all-high')
api.add_resource(RelayAllLow,'/api/v1/relay/all-low')


#Piplate steppers
api.add_resource(StepperStatus,'/api/v1/stepper/status/')


api.add_resource(I2cStatus,'/api/v1/i2c/status/')
api.add_resource(I2c,'/api/v1/i2c/<int:pin>')

api.add_resource(GpioTB6600Status,'/api/v1/gpio/TB6600/status/')
api.add_resource(StepperMove,'/api/v1/gpio/TB6600/test')


api.add_resource(PiStack,'/api/v1/piplates/status')


#FSM
api.add_resource(Conveyor, '/api/v1/conv')
api.add_resource(Mode, '/api/v1/conv/mode')


#app.run(host=HOSTNAME,port=PORT,debug=True,threaded=True)


#creeate queue object
q =Queue(27)


# production server not flask development server
serve(app,host=HOSTNAME,port=PORT)




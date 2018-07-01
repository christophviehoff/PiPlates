import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

import atexit,time
import json
import threading
from time import sleep
import datetime
import socket

from utilities import utils   # from: that's the folder name
from utilities import i2c_utils

#Piplates classes
import piplates.RELAYplate as RELAY
import piplates.MOTORplate as MOTOR
import piplates.DAQCplate as DAQC

#adafruit servo  module
import Adafruit_PCA9685

#state machine FS
from transitions import Machine

#Global parameters
broker="iot.eclipse.org"
#broker="192.168.1.8"
port=1883
keepalive=60
hostname=utils.get_hostname()

toggle = False

## help functions
def on_terminate():
    RELAY.RESET(0)
    RELAY.RESET(1)
    MOTOR.RESET(0)
    MOTOR.RESET(1)

    print ("All relays and Motors are off.")
    print ("Program has been terminated!")

# class definitions

class GenericFSM(Machine):

    # states and transitions
    def __init__(self):
        self.running=True
        self.isEnabled = False

        # define hardware objects at start

        #define FSM states with a state timeout, go to next state when timeout is reached
        states = ['dummy','init','ready','start','stop']

        Machine.__init__(self, states=states, initial='dummy')

        self.add_transition('trigger', 'dummy', 'init') #dummy on-enter callback will not fire when a Machine is first initialized.
        self.add_transition('trigger', 'init', 'ready',  conditions='always_on')
        self.add_transition('trigger', 'ready', 'start', conditions='always_on')
        self.add_transition('trigger', 'start', 'stop',  conditions='always_on')
        self.add_transition('trigger', 'stop', 'ready',  conditions='alwyas_on')

    # external transition control

    def shutdown(self):
        self.running=False

    def enable(self):
        self.isEnabled = True

    def disable(self):
        self.isEnabled = False

    #what to do when you enter a state

    def on_enter_init(self):
        print "entering state init"

    def on_enter_ready(self):
        print " entering state ready"
        time.sleep(2)

    def on_enter_start(self):
        print " entering state start"
        time.sleep(2)

    def on_enter_stop(self):
        print " entering state stop"
        time.sleep(2)

    #transition conditions

    def is_enabled(self):
        return self.isEnabled

    def always_on(self):
        return True

    def always_off(self):
        return False

class StandardPolling(threading.Thread):

    def __init__(self,interval,name):
        super(StandardPolling, self).__init__()
        self.name =name
        self.interval=interval
        self.setDaemon(True)
        self.running=True

# action
    def heartbeat(self):
        global toggle
        toggle ^= True
        if toggle:
            publish.single("sys/watchdog", "tick", hostname=broker)
        else:
            publish.single("sys/watchdog", "tock", hostname=broker)

    def run(self):
        while self.running:
            self.heartbeat()
            sleep(self.interval)

class SensorPolling(threading.Thread):

    def __init__(self,client,fsm,address,channel,name,interval,verbose=True):
        super(SensorPolling, self).__init__()

        self.mqttc = client
        self.fsm = fsm
        self.address=address
        self.channel=channel
        self.name=name
        self.interval=interval
        self.verbose = verbose
        self.setDaemon(True)
        self.running = False
        self.isEnabled = True

    def shutdown(self):
        self.running=False

    def enable(self):
        self.isEnabled=True

    def disable(self):
        self.isEnabled=False

# actions

    def send_data(self):
        # create the sensor data message
        if self.verbose:
            #convert to string and keep order by naming keys
            data = json.dumps({"00-Board address": self.address,
                               "01-Input Channel": self.channel,
                               "02-Description": self.name,
                               "03-Readout": DAQC.getTEMP(self.address, self.channel, "f"),
                               "04-Unit": "F",
                               "05-Switch status":  bool(DAQC.getSWstate(0)),
                               "06-Sensor1 status": bool(MOTOR.getSENSORS(0) & 0x01) ,
                               "07-Sensor2 status": bool(MOTOR.getSENSORS(0) & 0x02),
                               "08-Sensor3 status": bool(MOTOR.getSENSORS(0) & 0x04),
                               "09-Sensor4 status": bool(MOTOR.getSENSORS(0) & 0x08),
                               "10-Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                               },sort_keys=True)

            states = json.dumps({"00-FSM Name": 'test FSM',
                                 "01-FSM state": self.fsm.state,
                                 "02-Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                                 }, sort_keys=True)

            relay_state=json.dumps({
                "Relay 1": bool(RELAY.relaySTATE(0) & 0x01),   # just a int right now 1,2,4 etc
                "Relay 2": bool(RELAY.relaySTATE(0) & 0x02),
                "Relay 3": bool(RELAY.relaySTATE(0) & 0x04),
                "Relay 4": bool(RELAY.relaySTATE(0) & 0x08),
                "Relay 5": bool(RELAY.relaySTATE(0) & 0x10),
                "Relay 6": bool(RELAY.relaySTATE(0) & 0x20),
                "Relay 7": bool(RELAY.relaySTATE(0) & 0x40),

                "Relay 8": bool(RELAY.relaySTATE(1) & 0x01),
                "Relay 9": bool(RELAY.relaySTATE(1) & 0x02),
                "Relay 10":bool(RELAY.relaySTATE(1) & 0x04),
                "Relay 11":bool(RELAY.relaySTATE(1) & 0x08),
                "Relay 12":bool(RELAY.relaySTATE(1) & 0x10),
                "Relay 13":bool(RELAY.relaySTATE(1) & 0x20),
                "Relay 14":bool(RELAY.relaySTATE(1) & 0x40)
                },sort_keys=True)

        else:
            #short version
            # takes a while to get the sensor reading
            data= DAQC.getTEMP(self.address, self.channel, "f")
            states=self.fsm.state



        #TODO big combersome testing led message
        '''
        dict=json.loads(data)
        if dict['Switch status']:
            DAQC.setDOUTbit(0, 0)
        else :
            DAQC.clrDOUTbit(0, 0)
        '''

        #publish.single("sensors/data", data, hostname=broker)
        self.mqttc.publish(hostname+ "/sensors/data", data, 0)  # publish

        #report state
        self.mqttc.publish("sys/state", states, 0)  # publish

        # report relay state
        self.mqttc.publish(topic=hostname+"/relays/state", payload=relay_state,qos= 0,retain=True)  # publish


    def run(self):

        #started by thread.start() method

        #print("{} thread started!".format(self.getName()))              # "Thread-x started!"
        self.mqttc.publish(hostname+ "/messages",
                           "{} {} thread started!".format(time.strftime("%Y-%m-%d %H:%M:%S"), self.getName()), 0)  # publish

        self.running=True

        while self.running:

            if self.isEnabled:

                #start_time = timeit.default_timer()
                # code you want to evaluate
                self.send_data()   # takes a second due to the DAQC read commnad
                #elapsed = timeit.default_timer() - start_time
                #print elapsed
                sleep(self.interval)

class SwitchPolling(threading.Thread):

    def __init__(self,client,address,channel,name,interval,verbose=True):
        super(SwitchPolling, self).__init__()
        self.mqttc = client
        self.address=address
        self.channel=channel
        self.name=name
        self.interval=interval
        self.verbose = verbose
        self.setDaemon(True)
        self.running = False
        self.isEnabled = True

    def shutdown(self):
        self.running=False

    def enable(self):
        self.isEnabled=True

    def disable(self):
        self.isEnabled=False

# actions

    def send_data(self):
        # create the sensor data message
        if self.verbose:
            data = json.dumps({"00-Title": "Limit switch status",
                               "01-Sensor1 status": bool(MOTOR.getSENSORS(0) & 0x01),
                               "02-Sensor2 status": bool(MOTOR.getSENSORS(0) & 0x02),
                               "03-Sensor3 status": bool(MOTOR.getSENSORS(0) & 0x04),
                               "04-Sensor4 status": bool(MOTOR.getSENSORS(0) & 0x08),
                               "05-Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                                },sort_keys=True)
        else:
            #short version
            # takes a while to get the sensor reading
            data=bin(MOTOR.getSENSORS(0)& 0x0F)

        #publish.single("sensors/data", data, hostname=broker)
        self.mqttc.publish(hostname +"/sensors/switch", data, 0)  # publish

    def run(self):

        #started by thread.start() method

        #print("{} thread started!".format(self.getName()))              # "Thread-x started!"
        self.mqttc.publish(hostname + "/messages", "{} {} thread started!".format(time.strftime("%Y-%m-%d %H:%M:%S"), self.getName()), 0)

        self.running=True

        while self.running:
            if self.isEnabled:
                self.send_data()   # takes a second due to the DAQC read commnad
                sleep(self.interval)

#basic classes

class Servo:
    def __init__(self, name, address, port_number):
        self.running = False
        # object attributes
        self.name = name
        self.address = address
        self.port_number = port_number
        # setup pulses
        self.pwm = Adafruit_PCA9685.PCA9685(self.address)
        self.pwm.set_pwm_freq(60)
        #  Configure min and max servo pulse lengths
        # self.servo_min = servo_min # 150 self.servoStart.value()  # Min pulse length out of 4096
        # self.servo_max = servo_max # 600 self.servoStop.value()  # Max pulse length out of 4096

    # flow control

    def shutdown(self):
        self.running = False

    def enable(self):
        self.isEnabled = True

    def disable(self):
        self.isEnabled = False

    # actions

    def eject_test(self, servo_min, servo_max):

        self.servo_min = servo_min
        self.servo_max = servo_max

        # 16 max per object

        # sequence
        for port in range(0, 16):
            self.pwm.set_pwm(self.port_number + port, 0, self.servo_max)
            sleep(1)
            self.pwm.set_pwm(self.port_number + port, 0, self.servo_min)
            sleep(1)

            # same time
        for port in range(0, 16):
            self.pwm.set_pwm(self.port_number + port, 0, self.servo_max)
        sleep(1)
        for port in range(0, 16):
            self.pwm.set_pwm(self.port_number + port, 0, self.servo_min)
        sleep(1)

    def eject(self, servo_min, servo_max):

        #print "ejecting" + self.name
        self.servo_min = servo_min
        self.servo_max = servo_max

        self.pwm.set_pwm(self.port_number, 0, self.servo_max)
        sleep(1)
        self.pwm.set_pwm(self.port_number, 0, self.servo_min)
        sleep(1)

    def max(self, servo_min, servo_max):

        print "ejecting max" + self.name
        self.servo_min = servo_min
        self.servo_max = servo_max

        self.pwm.set_pwm(self.port_number, 0, self.servo_max)
        sleep(1)


    def min(self, servo_min, servo_max):

        print "ejecting min" + self.name
        self.servo_min = servo_min
        self.servo_max = servo_max

        self.pwm.set_pwm(self.port_number, 0, self.servo_min)
        sleep(1)


class Stepper:

    def __init__(self,motor,address, channel, name):
        #super(Stepper, self).__init__()
        self.address = address
        self.channel = channel
        self.name = name
        #self.setDaemon(True)
        self.running = True
        self.isEnabled = True
        self.motor=motor
        self.motor.RESET(address)

    def shutdown(self):
        self.running = False

    def enable(self):
        self.isEnabled = True

    def disable(self):
        self.isEnabled = False

    # actions

    def fwd(self):
        self.motor.stepperSTOP(self.address, self.channel)
        self.motor.stepperCONFIG(self.address, self.channel, 'cw', 'M4', 1000, 0)
        self.motor.stepperMOVE(self.address, self.channel, 800 )

    def rev(self):
        self.motor.stepperSTOP(self.address, self.channel)
        self.motor.stepperCONFIG(self.address, self.channel, 'ccw', 'M4', 1000, 0)
        self.motor.stepperMOVE(self.address, self.channel, 800)

    def off(self):
        self.motor.stepperSTOP(self.address, self.channel)
        self.motor.stepperOFF(self.address, self.channel)

    def up(self):
        self.motor.stepperSTOP(self.address, self.channel)
        self.motor.stepperCONFIG(self.address, self.channel, 'cw', 'M4', 100, 0)
        self.motor.stepperJOG(self.address, self.channel)

    def down(self):
        self.motor.stepperSTOP(self.address, self.channel)
        self.motor.stepperCONFIG(self.address, self.channel, 'ccw', 'M4', 100, 0)
        self.motor.stepperJOG(self.address, self.channel)

    def stop(self):
        self.motor.stepperSTOP(self.address, self.channel)

    def get_sensor_HL(self):
        if self.channel == 'a':
            # 500ms debounce
            return bool(self.motor.getSENSORS(self.address) & 0x1)  # read interrupt flagsX
        else: #'b'
            # 500ms debounce
            return bool(self.motor.getSENSORS(self.address) & 0x4)  # read interrupt flagsX

    def get_sensor_LL(self):
        if self.channel=='a':
            # 500ms debounce
            return bool(self.motor.getSENSORS(self.address) & 0x2)  # read interrupt flagsX
        else: #'b'
            # 500ms debounce
            return  bool(self.motor.getSENSORS(self.address) & 0x8)  # read interrupt flagsX

    def to_top(self):

        self.up()
        self.isEnabled = True
        while not self.get_sensor_HL() and self.isEnabled:
            time.sleep(.5)
        publish.single(hostname+ "/sensors/messages", self.name + " high limit reached!", hostname=broker)
        self.stop()

    def to_bottom(self):
        print "going down"
        self.down()
        self.isEnabled = True
        while not self.get_sensor_LL() and self.isEnabled:
            time.sleep(.5)
        publish.single(hostname + "/sensors/messages", self.name + " low limit reached!", hostname=broker)
        self.stop()

class Relay:
    def __init__(self, address, channel, name):
        self.address = address
        self.channel = channel
        self.name = name

    # actions
    def on(self):
        RELAY.relayON(self.address, self.channel)
        #print"{} is turned ON".format(self.name.upper())

    def off(self):
        RELAY.relayOFF(self.address, self.channel)
        #print"{} is turned OFF".format(self.name.upper())

    def toggle(self):
        RELAY.relayTOGGLE(self.address, self.channel)

    def all_on(self):
        #Bit 0 is relay 1, bit 1 is relay 2, and so on. To turn all the  relays on at once, use the number 127 for the value.
        RELAY.relayALL(self.address,127)

    def all_off(self):
        RELAY.relayALL(self.address, 0)

    def reset(self):
        RELAY.RESET(self.address)


    def get_state(self):
        '''
                Returns a 7-bit number with the current state of each relay.
                Bit 0 is relay 1, bit 1 is relay 2, and so on. A "1" in a bit position means that the
                relay is on and zero means that it's off.
        '''
        return json.dumps({
                "Relay card1":RELAY.relaySTATE(0),
                "Relay card2":RELAY.relaySTATE(1)
                })

#main class , uses composition
class MqttClient:

    def __init__(self,clientid):
        self.mqttc = mqtt.Client(clientid)
        self.mqttc.on_connect = self.mqttc_on_connect
        self.mqttc_on_disconnect = self.mqttc_on_disconnect

        # setup callbacks
        self.mqttc.message_callback_add(hostname + "/steppers/#", self.check_stepper_request)
        self.mqttc.message_callback_add(hostname+ "/relays/#", self.check_relay_request)
        self.mqttc.message_callback_add(hostname + "/servos/#", self.check_servo_request)
        self.mqttc.message_callback_add(hostname+ "/fsm", self.check_fsm_request)
        self.mqttc.message_callback_add("sys/#", self.check_system_request)

        #query i2c devices
        self.i2c_list=i2c_utils.list_of_i2c_servos()

        #create first Ejector object at 0x40
        self.ejector_0 = Servo("Bin-0", int(self.i2c_list[0], 16), 0)
        self.ejector_1 = Servo("Bin-1", int(self.i2c_list[0], 16), 1)
        self.ejector_2 = Servo("Bin-2", int(self.i2c_list[0], 16), 2)
        self.ejector_3 = Servo("Bin-3", int(self.i2c_list[0], 16), 3)
        self.ejector_4 = Servo("Bin-4", int(self.i2c_list[0], 16), 4)
        self.ejector_5 = Servo("Bin-5", int(self.i2c_list[0], 16), 5)
        self.ejector_6 = Servo("Bin-6", int(self.i2c_list[0], 16), 6)
        self.ejector_7 = Servo("Bin-7", int(self.i2c_list[0], 16), 7)
        self.ejector_8 = Servo("Bin-8", int(self.i2c_list[0], 16), 8)
        self.ejector_9 = Servo("Bin-9", int(self.i2c_list[0], 16), 9)
        self.ejector_10 = Servo("Bin-10", int(self.i2c_list[0], 16), 10)
        self.ejector_11 = Servo("Bin-11", int(self.i2c_list[0], 16), 11)
        self.ejector_12 = Servo("Bin-12", int(self.i2c_list[0], 16), 12)
        self.ejector_13 = Servo("Bin-13", int(self.i2c_list[0], 16), 13)
        self.ejector_14 = Servo("Bin-14", int(self.i2c_list[0], 16), 14)
        self.ejector_15 = Servo("Bin-15", int(self.i2c_list[0], 16), 15)

        # create stepper objects card 1
        self.stepper_0 = Stepper(motor=MOTOR, address=0, channel='a', name='Stepper0')
        self.stepper_1 = Stepper(motor=MOTOR, address=0, channel='b', name='Stepper1')

        # create stepper objects card 2
        #self.stepper_2 = Stepper(motor=MOTOR, address=1, channel='a', name='Stepper2)
        #self.stepper_3 = Stepper(motor=MOTOR, address=1, channel='b', name='Stepper3')

        # create relay objects card 1
        self.relay_1 =  Relay(address=0, channel=1, name='Relay1')
        self.relay_2 =  Relay(address=0, channel=2, name='Relay2')
        self.relay_3 =  Relay(address=0, channel=3, name='Relay3')
        self.relay_4 =  Relay(address=0, channel=4, name='Relay4')
        self.relay_5 =  Relay(address=0, channel=5, name='Relay5')
        self.relay_6 =  Relay(address=0, channel=6, name='Relay6')
        self.relay_7 =  Relay(address=0, channel=7, name='Relay7')
        # create relay objects card 2
        self.relay_8 =  Relay(address=1, channel=1, name='Relay8')
        self.relay_9 =  Relay(address=1, channel=2, name='Relay9')
        self.relay_10 = Relay(address=1, channel=3, name='Relay10')
        self.relay_11 = Relay(address=1, channel=4, name='Relay11')
        self.relay_12 = Relay(address=1, channel=5, name='Relay12')
        self.relay_13 = Relay(address=1, channel=6, name='Relay13')
        self.relay_14 = Relay(address=1, channel=7, name='Relay14')

        # create State Machine FSM
        self.test_FSM = GenericFSM()
        self.test_FSM.to_init() # bypass dummy
        self.running = True  # enable state machine
        self.fsm_is_enabled=False

    def mqttc_on_connect(self, mqttc, obj, flags, rc):
        print("Remote connection established ! ")
        self.mqttc.publish(hostname+ "/messages",
                           "{} Remote connection established ! ".format(format(time.strftime("%Y-%m-%d %H:%M:%S"))), 0)  # publish


    def mqttc_on_disconnect(self, mqttc, obj, flags, rc):
        print("Remote connection disconnected ! ")

    #flow conrol
    def shutdown(self):
        self.running = False

    #checking messages and responding, link message to action
    def check_stepper_request(self, mqttc, obj, msg):
        print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

        if (msg.topic ==hostname+ "/steppers/0"):

            self.stepper_0.disable()  # any new message exist the active thread

            if (msg.payload == "FWD"):
                self.stepper_0.fwd()
            elif (msg.payload == "REV"):
                self.stepper_0.rev()
            elif (msg.payload == "OFF"):
                self.stepper_0.off()
            elif (msg.payload == "UP"):
                self.stepper_0.up()
            elif (msg.payload == "DN"):
                self.stepper_0.down()
            elif (msg.payload == "STOP"):
                self.stepper_0.stop()
            elif (msg.payload == "TO TOP"):
                t0_totop = threading.Thread(name='totop', target=self.stepper_0.to_top)
                t0_totop.setDaemon(True)
                t0_totop.start()
            elif (msg.payload == "TO BOT"):
                t0_tobottom = threading.Thread(name='tobottom', target=self.stepper_0.to_bottom)
                t0_tobottom.setDaemon(True)
                t0_tobottom.start()
            else:
                self.stepper_0.off()

        if (msg.topic == hostname+ "/steppers/1"):

            self.stepper_1.disable()  # any new message exist the active thread

            if (msg.payload == "FWD"):
                self.stepper_1.fwd()
            elif (msg.payload == "REV"):
                self.stepper_1.rev()
            elif (msg.payload == "OFF"):
                self.stepper_1.off()
            elif (msg.payload == "UP"):
                self.stepper_1.up()
            elif (msg.payload == "DN"):
                self.stepper_1.down()
            elif (msg.payload == "STOP"):
                self.stepper_1.stop()
            elif (msg.payload == "TO TOP"):
                t1_totop = threading.Thread(name='totop', target=self.stepper_1.to_top)
                t1_totop.setDaemon(True)
                t1_totop.start()
            elif (msg.payload == "TO BOT"):
                t1_toBottom = threading.Thread(name='tobottom', target=self.stepper_1.to_bottom)
                t1_toBottom.setDaemon(True)
                t1_toBottom.start()
            else:
                self.stepper_1.off()

        #thread_list = threading.enumerate()
        #print (" {} treads running".format(len(thread_list)))
        #print thread_list

    def check_servo_request(self, mqttc, obj, msg):
        print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

        if (msg.topic ==hostname+ "/servos/0"):
            if (msg.payload == "EJECT"):
                self.ejector_0.eject(150,600)
            elif (msg.payload=="MAX"):
                self.ejector_0.max(150, 600)
            elif (msg.payload == "MIN"):
                self.ejector_1.min(150, 600)

        if (msg.topic ==hostname+ "/servos/1"):
            if (msg.payload == "EJECT"):
                self.ejector_1.eject(150,600)
            elif (msg.payload == "MAX"):
                self.ejector_0.max(150, 600)
            elif (msg.payload == "MIN"):
                self.ejector_1.min(150, 600)

        if (msg.topic == hostname + "/servos/all"):
            if (msg.payload == "TEST"):
                self.ejector_1.eject_test(150,600)

    def check_relay_request(self,mqttc, obj, msg):
        # first relay card
        #print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
        if (msg.topic == hostname+ "/relays/1"):
            if (msg.payload == "ON"):
                self.relay_1.on()
            elif (msg.payload == "OFF"):
                self.relay_1.off()
        elif (msg.topic == hostname+ "/relays/2"):
            if (msg.payload == "ON"):
                self.relay_2.on()
            elif (msg.payload == "OFF"):
                self.relay_2.off()
        elif (msg.topic == hostname+ "/relays/3"):
            if (msg.payload == "ON"):
                self.relay_3.on()
            elif (msg.payload == "OFF"):
                self.relay_3.off()
        elif (msg.topic == hostname+ "/relays/4"):
            if (msg.payload == "ON"):
                self.relay_4.on()
            elif (msg.payload == "OFF"):
                self.relay_4.off()
        elif (msg.topic ==hostname+ "/relays/5"):
            if (msg.payload == "ON"):
                self.relay_5.on()
            elif (msg.payload == "OFF"):
                self.relay_5.off()
        elif (msg.topic == hostname+ "/relays/6"):
            if (msg.payload == "ON"):
                self.relay_6.on()
            elif (msg.payload == "OFF"):
                self.relay_6.off()
        elif (msg.topic == hostname+ "/relays/7"):
            if (msg.payload == "ON"):
               self.relay_7.on()
            elif (msg.payload == "OFF"):
                self.relay_7.off()

        # second relay card
        if (msg.topic ==hostname+ "/relays/8"):
            if (msg.payload == "ON"):
                self.relay_8.on()
            elif (msg.payload == "OFF"):
                self.relay_8.off()
        elif (msg.topic == hostname+ "/relays/9"):
            if (msg.payload == "ON"):
                self.relay_9.on()
            elif (msg.payload == "OFF"):
                self.relay_9.off()
        elif (msg.topic ==hostname+ "/relays/10"):
            if (msg.payload == "ON"):
                self.relay_10.on()
            elif (msg.payload == "OFF"):
                self.relay_10.off()
        elif (msg.topic == hostname+ "/relays/11"):
            if (msg.payload == "ON"):
                self.relay_11.on()
            elif (msg.payload == "OFF"):
                self.relay_11.off()
        elif (msg.topic == hostname+ "/relays/12"):
            if (msg.payload == "ON"):
                self.relay_12.on()
            elif (msg.payload == "OFF"):
                self.relay_12.off()
        elif (msg.topic ==hostname+ "/relays/13"):
            if (msg.payload == "ON"):
                self.relay_13.on()
            elif (msg.payload == "OFF"):
                self.relay_13.off()
        elif (msg.topic == hostname+ "/relays/14"):
            if (msg.payload == "ON"):
               self.relay_14.on()
            elif (msg.payload == "OFF"):
                self.relay_14.off()

        elif (msg.topic ==hostname+ "/relays/all"):
            if (msg.payload == "ON"):
                self.relay_1.all_on()  #card 1
                self.relay_8.all_on()  #card2
            else:  # anything but ON turns it off
                self.relay_1.all_off()
                self.relay_8.all_off()
        else:
            pass

    def check_system_request(self,mqttc, obj, msg):
        # request-response setup
        #print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

        if (msg.topic == "sys/get"):

            if (msg.payload == "INFO"):
                data = json.dumps({"00-Timestamp      ": time.strftime("%Y-%m-%d %H:%M:%S"),
                                   "01-Hostname :     ": socket.gethostname(),
                                   "02-IP address     ": utils.get_local_ip_address(),
                                   "03-Broker         ": (broker,port),
                                   "04-Processes      ": utils.get_threads(),
                                   #"05-Pi-Plates      ": get_card_address(),
                                   "10-Relay Board   0": utils.is_relay_online(0),
                                   "11-Relay Board   1": utils.is_relay_online(0),
                                   "20-Stepper Board 0": utils.is_stepper_online(0),
                                   "21-Stepper Board 1": utils.is_stepper_online(1),
                                   "22-Stepper Board 2": utils.is_stepper_online(2),
                                   "23-Stepper Board 3": utils.is_stepper_online(3),
                                   "24-Stepper Board 4": utils.is_stepper_online(4),
                                   "25-Stepper Board 5": utils.is_stepper_online(5),
                                   "26-Stepper Board 6": utils.is_stepper_online(6),
                                   "27-Stepper Board 7": utils.is_stepper_online(7),
                                   "28-Servo Board   0": i2c_utils.is_servo_online(0)
                                   },sort_keys=True)

                self.mqttc.publish("sys/status", data, 1)  # publish
                # commands are parsed here

    def check_fsm_request(self,mqttc, obj, msg):
        # request-response setup to modify FSM behaviour
        print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

        if (msg.topic == hostname()+ "/fsm"):

            if (msg.payload == "ENABLE"):
                self.fsm_is_enabled=True #enable triggering to next state

            if (msg.payload == "DISABLE"):
                self.fsm_is_enabled = False
                self.test_FSM.to_init()

    #FSM thread callback
    def run_generic_fsm(self): #thats a thread

        self.mqttc.publish(hostname + "/messages", "{} {} thread started! "
                           .format(time.strftime("%Y-%m-%d %H:%M:%S"),threading.currentThread().getName()), 0)  # publish

        while self.running:
            if self.fsm_is_enabled:
                self.test_FSM.trigger()
                #add logic here to skip or got specific states
            else:
                #print "fsm disabled"
                sleep(1) # do nothing

    #Main MQTT actios
    def run(self):
        self.mqttc.connect(broker, port, 60)
        # subscribe to respond to direct requests to control hardware
        self.mqttc.subscribe(hostname + '/steppers/#', 0)
        self.mqttc.subscribe(hostname + '/relays/#', 0)
        self.mqttc.subscribe(hostname + '/servos/#', 0)
        self.mqttc.subscribe(hostname + '/fsm', 0)
        self.mqttc.subscribe('sys/#', 0)

        # board address, channel, name,interval time in seconds,full description)

        #Setting up polling intervals threads
        temperature = SensorPolling(client=self.mqttc, fsm=self.test_FSM,address=0, channel=0, name="Temperatures", interval=.5, verbose=True)
        temperature.start()

        switch = SwitchPolling(client=self.mqttc, address=0, channel=0, name="Switches", interval=.3, verbose=True)
        switch.start()

        heartbeat=StandardPolling(interval=2, name="Watchdog")
        heartbeat.start()

        #start  finite state machine thread
        t_generic_FSM = threading.Thread(name="Generic FSM", target=self.run_generic_fsm)
        t_generic_FSM.daemon = True
        t_generic_FSM.start()

        #start client loop to process callbacks in a thread
        self.mqttc.loop_forever()

        '''
        self._mqttc.loop_start()
        #other blocking stuff here
        while True:
            print"still running....."
            time.sleep (2)
        '''

# main program
def main():
    # clear old move commands and start fresh, remove power and reset to a know state
    MOTOR.RESET(0)
    MOTOR.RESET(1)

    mqttc = MqttClient('hardware')
    mqttc.run()

    atexit.register(on_terminate)

if __name__ == "__main__":

    main()
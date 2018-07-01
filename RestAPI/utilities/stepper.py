# CURRENT APPLICATION INFO
# 200 steps/rev
# 26V, 1.3A
# TB6600 = 1/16 microstep mode, signals are reversed
# Turn a 200 step motor left one full revolution: 3200

from time import sleep
import RPi.GPIO as gpio  # https://pypi.python.org/pypi/RPi.GPIO


# import exitHandler #uncomment this and line 58 if using exitHandler

class Stepper:
    # instantiate stepper
    # pins = [stepPin, directionPin, enablePin]
    def __init__(self, pins):
        # setup pins
        self.pins = pins
        self.stepPin = self.pins[0]
        self.directionPin = self.pins[1]
        self.enablePin = self.pins[2]

        # use the broadcom layout for the gpio
        gpio.setmode(gpio.BCM)

        # set gpio pins
        gpio.setup(self.stepPin, gpio.OUT)
        gpio.setup(self.directionPin, gpio.OUT)
        gpio.setup(self.enablePin, gpio.OUT)

        # set enable to high (i.e. power is NOT going to the motor)
        gpio.output(self.enablePin, True)

        #print "Stepper initialized (step= {} , direction= {}, enable={})".format(self.stepPin,self.directionPin,self.enablePin)

        # clears GPIO settings
    def cleanGPIO(self):
        gpio.cleanup()

    # step the motor
    # steps = number of steps to take
    # dir = direction stepper will move
    # speed = defines the denominator in the waitTime equation: waitTime = 0.000001/speed.
    # As "speed" is increased, the waitTime between steps is lowered
    # stayOn = defines whether or not stepper should stay "on" or not.
    # If stepper will need to receive a new step command immediately, this should be set to "True." Otherwise, it should remain at "False."
    def step(self, steps, dir, speed=1, stayOn=True):
        # set enable to high(i.e. power IS going to the motor)
        gpio.output(self.enablePin, True)

        # set the output to true for left and false for right
        turnCW = True
        if (dir == 'CW'):
            turnCW = False;
        elif (dir != 'CCW'):
            print "STEPPER ERROR: no direction supplied"
            return False
        gpio.output(self.directionPin, turnCW)

        stepCounter = 0

        waitTime = 0.0001 / speed  # waitTime controls speed

        while stepCounter < steps:
            # gracefully exit if ctr-c is pressed
            # exitHandler.exitPoint(True) #exitHandler.exitPoint(True, cleanGPIO)

            # turning the gpio on and off tells the easy driver to take one step
            gpio.output(self.stepPin, False)
            gpio.output(self.stepPin, True)
            stepCounter += 1

            # wait before taking the next step thus controlling rotation speed
            sleep(waitTime)

        if (stayOn == False):
            # set enable to low (i.e. power is NOT going to the motor)
            gpio.output(self.enablePin, False)

        #print "stepperDriver complete (turned {} {}  steps)".format(dir,str(steps))

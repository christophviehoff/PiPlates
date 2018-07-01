import smbus,subprocess,sys

VALID_I2C_ADRESSES=['0x20']
VALID_I2C_PIN_NUMBERS = [0,1,2,3,4,5,6,7,10,11,12,13,14,15,16,17] #i2c module addresses
I2C_ADDRESS=0x20

PIN_NAMES = {'0' : '0.0-spare',
             '1' : '0.1-spare',
             '2' : '0.2-spare',
             '3' : '0.3-spare',
             '4' : '0.4-spare',
             '5' : '0.5-spare',
             '6' : '0.6-spare',
             '7' : '0.7-spare',
             '10': '1.0-spare',
             '11': '1.1-spare',
             '12': '1.2-spare',
             '13': '1.3-spare',
             '14': '1.4-spare',
             '15': '1.5-spare',
             '16': '1.6-spare',
             '17': '1.7-spare'
             }

# class for using a PCA9555 chips on an I2C bus
class PCA9555():
    # open Linux device /dev/ic2-1
    i2c = smbus.SMBus(1)

    # construct a new object with the I2C address of the PCA9555
    def __init__(self, address):
        self.address = address
        self.setInputDirection(0xFFFF)  # all pins are inputs by default now


    # write a 16 bit value to a register pair
    # write low byte of value to register reg,
    # and high byte of value to register reg+1
    def writeRegisterPair(self, reg, value):
        low = value & 0xff
        high = (value >> 8) & 0xff
        self.i2c.write_byte_data(self.address, reg, low)
        self.i2c.write_byte_data(self.address, reg + 1, high)

    # read a 16 bit value from a register pair
    def readRegisterPair(self, reg):
        low = self.i2c.read_byte_data(self.address, reg)
        high = self.i2c.read_byte_data(self.address, reg + 1)
        return low | (high << 8)

    # set IO ports to input, if the corresponding direction bit is 1,
    # otherwise set it to output
    def setInputDirection(self, direction):
        self.writeRegisterPair(6, direction)

    # set the IO port outputs
    def setOutput(self, value):
        self.writeRegisterPair(2, value)

    # read the IO port inputs
    def getInput(self):
        return self.readRegisterPair(0)

    def digitalRead(self,pin):
        if self.getInput() & (0x0001<< pin):  # MASK PIN 0 of a 16 bit word
            return 1
        else:
            return 0

def pin_status(pin_number):
    ioExpander = PCA9555(I2C_ADDRESS)

    if pin_number in VALID_I2C_PIN_NUMBERS:
        value=ioExpander.digitalRead(pin_number)
        data = {'pin_number': pin_number,
                'pin_name': PIN_NAMES[str(pin_number)],
                'value': value,
                'status': 'SUCCESS',
                'error': None,
                'address':VALID_I2C_ADRESSES
                }
    else:
        data = {'status': 'ERROR',
                'error': 'Invalid pin number.'}

    return data

def check_i2c_devices():
    print()
    print("listing of all i2c devices on the i2cbus")
    print()
    subprocess.call(['i2cdetect', '-y', '1'])
    # check if any i2c devices are present
    print()
    if not is_connected_to_device(0x70): sys.exit()

def is_connected_to_device(address):
    try:
        smbus.SMBus(1).read_byte_data(address,0x00)
    except IOError:
        print ("Could not open the i2c bus at address {} ".format(hex(address)))
        print ("Please check that i2c device is connected and powered up")
        print ()
        return False
    else:
        return True

def list_of_i2c_devices():
    # list of available com ports
    i2c_devices = []
    # select only the dispenser via the VID identifier
    for address in range(0x00,0x71):
        try:
            smbus.SMBus(1).read_byte_data(address, 0x00)
        except IOError:
            pass
        else:
            i2c_devices.append(hex(address))

    return i2c_devices

def list_of_i2c_servos():
    # list of available com ports
    i2c_devices = []
    # select only the dispenser via the VID identifier
    for address in range(0x40,0x4F):
        try:
            smbus.SMBus(1).read_byte_data(address, 0x00)
        except IOError:
            pass
        else:
            i2c_devices.append(hex(address))

    return i2c_devices

def list_of_i2c_steppers():
    # list of available com ports
    i2c_devices = []
    # select only the dispenser via the VID identifier
    for address in range(0x60,0x6F):
        try:
            smbus.SMBus(1).read_byte_data(address, 0x00)
        except IOError:
            pass
        else:
            i2c_devices.append(hex(address))

    return i2c_devices

def list_of_i2c_io():
    # list of available com ports
    i2c_devices = []
    # select only the dispenser via the VID identifier
    for address in range(0x20,0x2F):
        try:
            smbus.SMBus(1).read_byte_data(address, 0x00)
        except IOError:
            pass
        else:
            i2c_devices.append(hex(address))

    return i2c_devices

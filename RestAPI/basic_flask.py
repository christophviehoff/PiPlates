from flask import Flask,jsonify,request
from utilities import gpio,i2c

import datetime,random,string
import socket


PORT=5000
HOSTNAME=socket.gethostname()+".local"

app =Flask(__name__)

#root default
@app.route("/") #home page
def home():
    #respone to browser
    return "<h1> Hello to my API</h1>"

@app.route("/about") #about page
def about():
    aboutMe = [{
        "name": "IO resources",
        "description": "Relay module and i2c resource",
        "hostname": HOSTNAME,
        "timestamp": datetime.datetime.utcnow(),
        "status": "offline",
        "GPIO": "4,27,13,26",
        "i2c":i2c.list_of_i2c_io(),
        "port": PORT,
        "id": ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])
    }]
    return jsonify({"AboutMe":aboutMe})

@app.route("/api/v1/ping/", methods=['GET'])
def api_status():
    if request.method == 'GET':
        data = {'api_name': 'RPi GPIO API',
                'version': '1.0',
                'status': 'SUCCESS',
                'response': 'pong'}
        return jsonify(data)


########       relay  board       ########

@app.route("/api/v1/gpio/<pin_number>", methods=['POST', 'GET'])
def gpio_pin(pin_number):
    pin_number = int(pin_number)


    print (request.method)
    if request.method == 'GET':
        data = gpio.pin_status(pin_number)

    elif request.method == 'POST':
        data = request.get_json()
        print (data,type(data))
        value=data["value"]
        if value in gpio.VALID_HIGH_VALUES:
            data = gpio.pin_update(pin_number, 1)
        elif value in gpio.VALID_LOW_VALUES:
            data = gpio.pin_update(pin_number, 0)
        else:
            data = {'status': 'ERROR',
                    'error': 'Invalid value.'}
    return jsonify(data)

@app.route("/api/v1/gpio/status/", methods=['GET'])
def gpio_status():
    data_list = []
    for pin in gpio.VALID_BCM_PIN_NUMBERS:
        data_list.append(gpio.pin_status(pin))

    data = {'gpio data': data_list}
    return jsonify(data)

@app.route("/api/v1/gpio/all-high/", methods=['POST'])
def gpio_all_high():
    data_list = []
    for pin in gpio.VALID_BCM_PIN_NUMBERS:
        data_list.append(gpio.pin_update(pin, 1))

    data = {'gpio data': data_list}
    return jsonify(data)

@app.route("/api/v1/gpio/all-low/", methods=['POST'])
def gpio_all_low():
    data_list = []
    for pin in gpio.VALID_BCM_PIN_NUMBERS:
        data_list.append(gpio.pin_update(pin, 0))

    data = {'gpio data': data_list}
    return jsonify(data)


########       i2c devices       ########

@app.route("/api/v1/i2c/status/", methods=['GET'])
def i2c_status():
    data_list = []
    for pin in i2c.VALID_I2C_PIN_NUMBERS:
        data_list.append(i2c.pin_status(pin))

    data = {'i2c data': data_list}
    return jsonify(data)

@app.route("/api/v1/i2c/<pin_number>", methods=['GET'])
def i2c_pin(pin_number):
    pin_number = int(pin_number)

    if request.method == 'GET':
        data = i2c.pin_status(pin_number)

    return jsonify(data)

app.run(host=HOSTNAME,port=PORT,debug=True)


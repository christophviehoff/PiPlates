import socket,threading
#Piplates classes
import piplates.RELAYplate as RELAY
import piplates.MOTORplate as MOTOR

def get_hostname():
    return socket.gethostname()

def get_local_ip_address():
    # get local IP for status information
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 1))
    return s.getsockname()[0]

def get_threads():

    threads=[]
    main_thread = threading.current_thread()
    for t in threading.enumerate():
        if t is main_thread: # exclude main thread
            continue
        threads.append(t.getName())
    return (threading.active_count()-1,threads)

def is_relay_online(address):
    # match addresses to make sure the card is there
    if RELAY.getADDR(address) == address:
        return "online"
    else:
        return "offline"

def is_stepper_online(address):
    if MOTOR.getADDR(address) == address:
        return "online"
    else:
        return "offline"

def get_card_address():
    relays = []
    motors = []
    for address in range(0, 2):
        relays.append({"address":RELAY.getADDR(address),"status":is_relay_online(address)})

    for address in range(0, 8):
        if MOTOR.getADDR(address) > -1: #suppress cards that don't exist , code -16
            motors.append({"address":MOTOR.getADDR(address),"status":is_stepper_online(address)})

    # remove duplicates with set

    return {'Relays': list((relays)),
            'Steppers': list(motors),
            }

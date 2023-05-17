import datetime

import geocoder
from flask import Flask, render_template, request, redirect, url_for
from flask_apscheduler import APScheduler
from suntime import Sun

from controller.led_controllers import ControllerChain, LEDController

RETURN_TO_PREVIOUS_PAGE: str = '<script>document.location.href = document.referrer</script>'
app: Flask = Flask(__name__)
controllerChain: ControllerChain = ControllerChain()

# Sunlight sensor
sunlight: bool = False
# Water sensor
water: bool = False

override: bool = False

light_pin: int = 23
water_pin: int = 5

try:
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(light_pin, GPIO.IN)
    GPIO.setup(water_pin, GPIO.IN)

except ImportError:
    import controller.GPIOSim as GPIO


def set_from_light_sensor():
    global sunlight, override

    if not override:
        sunlight = GPIO.input(light_pin)

    for controller in controllerChain:
        if controller.use_light_sensor:
            calculated_color = list(controller.color.hsv)
            calculated_color[2] = 100 if sunlight else 0
            controller.color.hsv = calculated_color

    # if use_default and not override:
    #     sunlight = bool(random.getrandbits(1))


def get_water_sensor():
    global water, override
    if not override:
        water = bool(GPIO.input(water_pin))
        # water = bool(random.getrandbits(1))


scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
scheduler.add_job(id='set_from_light_sensor', func=set_from_light_sensor, trigger='interval', seconds=1)
scheduler.add_job(id='get_water_sensor', func=get_water_sensor, trigger='interval', seconds=1)


@app.route('/')
def index():
    # get_led_intensity_from_sun()
    return redirect(url_for('rgb_controller'))


@app.route('/rgb_controller/')
@app.route('/rgb_controller/<int:cid>', methods=['GET', 'POST'])
def rgb_controller(cid: int = -1):
    if cid == -1 or not controllerChain.check_id_is_valid(cid):
        # If the given id is not valid go to default controller (id 0)
        return redirect(url_for('rgb_controller', cid=0))

    controller: LEDController = controllerChain[cid]
    if request.method == 'POST':
        data = request.get_json()
        if 'color' in data:
            color = data['color']
            controller.color.hsv = color['h'], color['s'], color['v']

        if 'temperature' in data:
            controller.temperature = float(data['temperature'])

    return render_template('controller.html', selectedController=controller, controllers=controllerChain.controllers,
                           water=water)


@app.route('/add_controller', methods=['GET', 'POST'])
def add_controller():
    controllerToAdd = LEDController()  # Create dummy controller to hold settings
    returnValue = configure_controller_from_request(controllerToAdd)
    if returnValue:
        return returnValue

    return render_template('configure_controller.html', controller=controllerToAdd, add_controller=True)


@app.route('/configure_controller/<int:cid>', methods=['GET', 'POST'])
def configure_controller(cid: int):
    if not controllerChain.check_id_is_valid(cid):
        return RETURN_TO_PREVIOUS_PAGE  # If controller ID is not valid

    controller: LEDController = controllerChain[cid]
    returnValue = configure_controller_from_request(controller)
    if returnValue:
        return returnValue

    return render_template('configure_controller.html', controller=controller, add_controller=False)


@app.route('/parameter', methods=['GET', 'POST'])
def change_params():
    global water, sunlight, override
    if request.method == 'POST':
        # Data can be taken from a form or from a fetch post (json)
        data: dict = request.form
        if not data:
            data = request.get_json()

        if 'override' in data:
            override = data['override']

        if 'sunlight' in data:
            sunlight = data['sunlight']

        if 'water' in data:
            water = data['water']

    return render_template('params.html', water=water, sunlight=sunlight, override=override)


def configure_controller_from_request(controller: LEDController):
    if request.method == 'POST':
        # Data can be taken from a form or from a fetch post (json)
        data: dict = request.form
        if not data:
            data = request.get_json()

        if 'name' in data:
            controller.name = data['name']
            controllerChain.save_controllers()

        if 'use_light_sensor' in data:
            controller.use_light_sensor = data['use_light_sensor']
            controllerChain.save_controllers()

        if 'color' in data:
            color: dict = data['color']
            controller.calibration.hsv = color['h'], color['s'], color['v']
            controllerChain.save_controllers()

        if 'action' in data:
            action = data['action']
            if action == 'delete':
                controllerChain.delete_controller(cid=controller.cid)
                return redirect(url_for('rgb_controller'))

            elif action == 'add':
                newLED = controllerChain.add_controller(existingController=controller)
                return redirect(url_for('rgb_controller', cid=newLED.cid))


def get_led_intensity_from_sun() -> float:
    """
    Calculates how strong the lights should be based on current location and sunset/sunrise time
    :return: Intensity of lights from 0.0 to 1.0 (0-100%)
    """
    # Get today's sunrise and sunset in UTC
    g = geocoder.ip('me')
    latitude, longitude = g.latlng
    sun = Sun(latitude, longitude)
    sunrise = sun.get_sunrise_time()
    sunset = sun.get_sunset_time()

    currentTime = datetime.datetime.now()
    currentTime = currentTime.replace(tzinfo=datetime.timezone.utc)  # Make timezone aware

    if sunrise < currentTime < sunset:
        return 0.0

    else:
        return 1.0


if __name__ == '__main__':
    app.run(host='0.0.0.0')

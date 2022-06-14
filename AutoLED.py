import datetime

import geocoder
from flask import Flask, render_template, request, redirect, url_for
from suntime import Sun

from controller.led_controllers import ControllerChain, LEDController
from controller.color import Color

RETURN_TO_PREVIOUS_PAGE: str = '<script>document.location.href = document.referrer</script>'
app: Flask = Flask(__name__)
controllerChain: ControllerChain = ControllerChain()


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

    return render_template('controller.html', selectedController=controller, controllers=controllerChain.controllers)


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


def configure_controller_from_request(controller: LEDController):
    if request.method == 'POST':
        # Data can be taken from a form or from a fetch post (json)
        data = request.form
        if not data:
            data = request.get_json()

        if 'name' in data:
            controller.name = data['name']
            controllerChain.save_controllers()

        if 'color' in data:
            color = data['color']
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

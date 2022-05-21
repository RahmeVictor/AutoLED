import datetime

import geocoder
from flask import Flask, render_template, request, redirect, url_for
from suntime import Sun

from led_controllers import ControllerChain, LEDController

RETURN_TO_PREVIOUS_PAGE: str = '<script>document.location.href = document.referrer</script>'
app = Flask(__name__)
controllerChain: ControllerChain = ControllerChain()


@app.route('/')
def index():
    get_led_intensity_from_sun()
    return redirect(url_for('rgb_controller', cid=0))


@app.route('/rgb_controller/<int:cid>', methods=['GET', 'POST'])
def rgb_controller(cid: int):
    if not controllerChain.check_id_is_valid(cid):
        # If the given id is not valid go to default controller (id 0)
        return redirect(url_for('rgb_controller', cid=0))

    controller: LEDController = controllerChain[cid]
    if request.method == 'POST':
        if 'color' in request.form:
            controller.color = LEDController.hex2rgb(request.form['color'])

        if 'warmth' in request.form:
            warmth = float(request.form['warmth'])
            controller.color = LEDController.kelvin2rgb(warmth)

    return render_template('index.html', selectedController=controller, controllers=controllerChain.controllers)


@app.route('/add_controller', methods=['POST'])
def add_controller():
    newLED = controllerChain.add_controller(name=request.form['name'])
    return redirect(url_for('rgb_controller', cid=newLED.cid))


@app.route('/rename_controller', methods=['POST'])
def rename_controller():
    cid = int(request.form['controllerID'])
    if controllerChain.check_id_is_valid(cid):
        controllerChain[cid].name = request.form['name']
        return redirect(url_for('rgb_controller', cid=cid))

    return RETURN_TO_PREVIOUS_PAGE


@app.route('/delete_controller', methods=['POST'])
def delete_controller():
    cid = int(request.form['controllerID'])
    if controllerChain.check_id_is_valid(cid):
        controllerChain.delete_controller(cid=cid)

    return RETURN_TO_PREVIOUS_PAGE


@app.route('/kelvin2hex/<kelvin>', methods=['GET'])
def kelvin2hex(kelvin):
    return LEDController.kelvin2hex(float(kelvin))


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
    currentTime = currentTime.replace(tzinfo=datetime.timezone.utc)

    if sunrise < currentTime < sunset:
        return 0

    else:
        return 1


if __name__ == '__main__':
    app.run(host="0.0.0.0")

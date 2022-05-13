from flask import Flask, render_template, request, redirect, url_for

from led_controllers import ControllerChain, LEDController

RETURN_FROM_REDIRECT = '<script>document.location.href = document.referrer</script>'
app = Flask(__name__)
controllerChain = ControllerChain()


@app.route('/')
def index():
    return redirect(url_for('rgb_controller', cid=0))


@app.route('/rgb_controller/<int:cid>', methods=['GET', 'POST'])
def rgb_controller(cid: int):
    if not controllerChain.check_id_is_valid(cid):
        return redirect(url_for('rgb_controller', cid=0))

    controller = controllerChain[cid]
    if request.method == 'POST':
        if 'color' in request.form:
            controllerChain[cid].color = LEDController.hex2rgb(request.form['color'])
            print(controller.color)

        if 'brightness' in request.form:
            controller.brightness = request.form['brightness']
            print(controller.brightness)

    data = {
        'selectedController': controller,
        'controllers': controllerChain.controllers,
    }
    return render_template('index.html', **data)


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

    return RETURN_FROM_REDIRECT


@app.route('/delete_controller', methods=['POST'])
def delete_controller():
    cid = int(request.form['controllerID'])
    if controllerChain.check_id_is_valid(cid):
        controllerChain.delete_controller(cid=cid)

    return RETURN_FROM_REDIRECT


if __name__ == '__main__':
    app.run(host="0.0.0.0")

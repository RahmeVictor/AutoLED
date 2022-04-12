function send_color_data(color) {
    // Send the current color as a HEX string, such as #defff4
    $.post(window.location, {
        color: color.hexString,
    });
}

function send_brightness_data() {
    let brightness = document.getElementById('brightnessInput');
    $.post(window.location, {
        brightness: brightness.value
    });

    update_brightness_text();
}

function update_brightness_text(){
    let brightness = document.getElementById('brightnessInput');
    document.getElementById('brightness-label').innerHTML ='Brightness: ' + brightness.value +'%';
}

window.onload = function () {
    $("#brightness").on('input change', send_brightness_data);
    update_brightness_text()
}
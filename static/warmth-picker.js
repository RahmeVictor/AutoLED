// When the page loads attach a function on warmth picker input change
window.onload = function () {
    let warmth = $("#warmth")
    warmth.on('input change', send_warmth_data);
    update_warmth_visuals(false).then(() => {
    });
}

function send_warmth_data() {
    let warmth = document.getElementById('warmthInput');
    $.post(window.location, {
        warmth: warmth.value
    });
    update_warmth_visuals().then(() => {
    });
}

async function update_warmth_visuals(updatePicker = true) {
    let warmthInput = document.getElementById('warmthInput');
    let kelvin = warmthInput.value

    // Update text
    document.getElementById('warmth-label').innerHTML = 'Warmth: ' + kelvin + 'k';

    // Update color using fetch
    let response = await fetch('/kelvin2hex/' + kelvin);
    let hex = await response.text();

    // Update colorPicker color
    if (typeof colorPicker !== 'undefined' && updatePicker)
        colorPicker.color.hexString = hex;
}
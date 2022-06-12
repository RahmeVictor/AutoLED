// When the page loads attach a function on warmth picker input change
window.addEventListener('load', function() {
    let warmth = document.getElementById('warmthInput');
    warmth.oninput = update_warmth_visuals;
    update_warmth_visuals(false).then(() => {
    });
})

async function update_warmth_visuals(updatePicker = true) {
    // Update text
    let kelvin = document.getElementById('warmthInput').value;
    document.getElementById('warmth-label').innerHTML = 'Warmth: ' + kelvin + 'k';

    // Update colorPicker color from kelvin input using fetch
    if (typeof colorPicker !== 'undefined' && updatePicker) {
        let response = await fetch('/kelvin2hex/' + kelvin);
        colorPicker.color.hexString = await response.text();
    }
}
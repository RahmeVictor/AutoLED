///////// Unused /////////

// // When the page loads attach a function on temperature picker input change
// window.addEventListener('load', function() {
//     let temperature = document.getElementById('temperatureInput');
//     temperature.oninput = update_temperature_visuals;
//     update_temperature_visuals(false).then(() => {
//     });
// })
//
// async function update_temperature_visuals(updatePicker = true) {
//     // Update text
//     let kelvin = document.getElementById('temperatureInput').value;
//     document.getElementById('temperature-label').innerHTML = 'Temperature: ' + kelvin + 'k';
//
//     // Update colorPicker color from temperature input using fetch from (/kelvin2hex/<kelvin>)
//     if (typeof colorPicker !== 'undefined' && updatePicker) {
//         let response = await fetch('/kelvin2hex/' + kelvin);
//         colorPicker.color.hexString = await response.text();
//     }
// }
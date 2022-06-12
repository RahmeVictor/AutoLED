/*
Creates a color picker on any element with id #picker-container
Adds a listener that sends post data to current URL about selected color.
*/

// Initialize color picker
function initialize_color_picker(initialColor = "#ffffff") {
    window.addEventListener('load', function () {
        colorPicker = new iro.ColorPicker("#picker-container", {
            width: 300, // Size of the color picker
            color: initialColor // Initial color
        });

        colorPicker.on('color:change', function (color) {
            // When color changes send the current color trough POST as HEX string
            post_data(window.location, {color: color.hexString})
        });
    })
}
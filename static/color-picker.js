/*
Creates a color picker on any element with id #picker-container
Adds a listener that sends post data to current URL about selected color.
*/

// Initialize color picker
function initialize_color_picker(initialColor = {h: 360, s: 100, v: 50}) {
    // When window loads
    window.addEventListener('load', function () {
        // Create color picker, use variable from outer scope to store it
        colorPicker = new iro.ColorPicker("#picker-container", {
            width: 300, // Size of the color picker
            color: initialColor, // Initial color
            layout: [
                {
                    component: iro.ui.Wheel,
                },
                {
                    component: iro.ui.Slider,
                },
                {
                    component: iro.ui.Slider,
                    options: {sliderType: 'kelvin', maxTemperature: 6500}
                },
            ]
        });

        // When color changes send the current color trough POST as HSV dictionary
        colorPicker.on('color:change', function (color) {
            post_data(window.location, {color: color.hsv})
        });
    })
}
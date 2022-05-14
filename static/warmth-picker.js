function send_warmth_data() {
    let warmth = document.getElementById('warmthInput');
    $.post(window.location, {
        warmth: warmth.value
    });

    update_warmth_text();
}

function update_warmth_text() {
    let warmth = document.getElementById('warmthInput');
    document.getElementById('warmth-label').innerHTML = 'Warmth: ' + warmth.value + 'k';
}

// When the page loads attach a function on warmth picker input change
window.onload = function () {
    let warmth = $("#warmth")
    warmth.on('input change', send_warmth_data);
    update_warmth_text()
}
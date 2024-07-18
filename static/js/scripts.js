function startDetection() {
    fetch('/control_detection', {
        method: 'POST',
        body: new URLSearchParams({ action: 'start' })
    })
    .then(response => response.json())
    .then(data => console.log(data));
}

function updateDetails() {
    fetch('/get_details')
        .then(response => response.json())
        .then(data => {
            document.getElementById('object').innerText = Object.keys(data.object).join(', ') || "Not detected";
            document.getElementById('weight').innerText = data.weight ? data.weight.toFixed(2) + " g" : "Waiting for data...";
            document.getElementById('total-weight').innerText = Object.values(data.total_weight).reduce((a, b) => a + b, 0).toFixed(2) + " g";
            document.getElementById('price').innerText = data.price.toFixed(2) + " Rs";
        });
}

setInterval(updateDetails, 1000);

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
            document.getElementById('object').innerText = data.object || "Not detected";
            document.getElementById('weight').innerText = data.weight ? data.weight.toFixed(2) + " g" : "Waiting for data...";
            document.getElementById('price').innerText = data.price ? data.price.toFixed(2) + " Rs" : "0.00 Rs";
        });
}

setInterval(updateDetails, 1000);

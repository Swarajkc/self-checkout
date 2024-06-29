function startDetection() {
    fetch('/start_detection')
        .then(response => response.json())
        .then(data => console.log(data));
}

function updateDetails() {
    fetch('/get_details')
        .then(response => response.json())
        .then(data => {
            document.getElementById('object').innerText = data.object || "Not detected";
            document.getElementById('weight').innerText = data.weight || "Waiting for data...";
            document.getElementById('price').innerText = data.price || "0.00 Rs";
        });
}

setInterval(updateDetails, 1000);

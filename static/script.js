function startDetection() {
    fetch('/start_detection')
        .then(response => response.json())
        .then(data => console.log(data));
}

function updateDetails() {
    fetch('/get_details')
        .then(response => response.json())
        .then(data => {
        document.getElementById('details').innerHTML = `Detected: ${data.object}, Weight: ${data.weight}, Price: ${data.price}`;
    });
    setTimeout(updateDetails, 2000);  // Update every 2 seconds
}

updateDetails();

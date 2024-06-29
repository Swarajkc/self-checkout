function startDetection() {
    fetch('/start_detection')
        .then(response => response.json())
        .then(data => console.log(data))
        .catch(error => console.error('Error:', error));

    setInterval(fetchDetails, 1000);  // Fetch details every second
}

function fetchDetails() {
    fetch('/get_details')
        .then(response => response.json())
        .then(data => {
            document.getElementById('object').textContent = data.object || 'None';
            document.getElementById('weight').textContent = data.weight || '0 grams';
            document.getElementById('price').textContent = data.price + ' Rs';
        })
        .catch(error => console.error('Error:', error));
}

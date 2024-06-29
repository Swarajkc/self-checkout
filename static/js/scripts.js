function startDetection() {
    fetch('/start_detection').then(response => response.json()).then(data => {
        console.log("Detection started");
    });

    setInterval(() => {
        fetch('/get_details')
        .then(response => response.json())
        .then(data => {
            document.getElementById('objectName').textContent = 'Object: ' + data.object;
            document.getElementById('objectWeight').textContent = 'Weight: ' + data.weight;
            document.getElementById('objectPrice').textContent = 'Price: ' + data.price;
            document.getElementById('objectImage').src = '/static/images/' + data.object.toLowerCase() + '.jpg';
        });
    }, 5000);  // Update the UI every 5 seconds
}

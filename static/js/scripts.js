/**
 * Start object detection by sending a request to the backend.
 */
function startDetection() {
    fetch('/control_detection', {
        method: 'POST',
        body: new URLSearchParams({ action: 'start' }),
    })
        .then(response => {
            if (response.ok) {
                console.log("Detection started successfully.");
                alert("Detection started!");
            } else {
                console.error(`Error starting detection: ${response.statusText}`);
                alert("Failed to start detection. Please try again.");
            }
        })
        .catch(error => {
            console.error("Error starting detection:", error);
            alert("An error occurred while starting detection.");
        });
}

/**
 * Fetch and update detection details from the backend.
 */
function updateDetails() {
    fetch('/get_details')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Update detected object, weight, and price
            document.getElementById('object').innerText = data.object || "Not detected";
            document.getElementById('weight').innerText = data.weight
                ? `${data.weight.toFixed(2)} g`
                : "Waiting for data...";
            document.getElementById('price').innerText = data.price
                ? `${data.price.toFixed(2)} Rs`
                : "0.00 Rs";

            // Update detected images dynamically
            const imagesContainer = document.querySelector('.images');
            imagesContainer.innerHTML = ''; // Clear previous images

            if (data.detected_images && data.detected_images.length > 0) {
                data.detected_images.forEach(image => {
                    const img = document.createElement('img');
                    img.src = `/static/${image}`;
                    img.alt = "Detected Object";
                    img.classList.add('detected-image'); // Add CSS class for styling
                    imagesContainer.appendChild(img);
                });
            } else {
                imagesContainer.innerHTML = `
                    <p class="no-detection">No objects detected. Place items for detection.</p>
                `;
            }
        })
        .catch(error => {
            console.error("Error updating details:", error);
        });
}

/**
 * Reset all detection details (e.g., object, weight, price) on page load.
 */
function resetDetails() {
    document.getElementById('object').innerText = "Not detected";
    document.getElementById('weight').innerText = "Waiting for data...";
    document.getElementById('price').innerText = "0.00 Rs";

    const imagesContainer = document.querySelector('.images');
    imagesContainer.innerHTML = '<p class="no-detection">No objects detected. Place items for detection.</p>';
}

/**
 * Stop object detection by sending a request to the backend.
 */
function stopDetection() {
    fetch('/control_detection', {
        method: 'POST',
        body: new URLSearchParams({ action: 'stop' }),
    })
        .then(response => {
            if (response.ok) {
                console.log("Detection stopped successfully.");
                alert("Detection stopped!");
            } else {
                console.error(`Error stopping detection: ${response.statusText}`);
                alert("Failed to stop detection. Please try again.");
            }
        })
        .catch(error => {
            console.error("Error stopping detection:", error);
            alert("An error occurred while stopping detection.");
        });
}

/**
 * Set intervals for continuously updating detection details.
 */
document.addEventListener('DOMContentLoaded', () => {
    // Reset details when the page is loaded
    resetDetails();

    // Continuously update detection details every second
    setInterval(updateDetails, 1000);

    // Add event listener for the stop button if present
    const stopButton = document.querySelector('button[name="action"][value="stop"]');
    if (stopButton) {
        stopButton.addEventListener('click', event => {
            event.preventDefault();
            stopDetection();
        });
    }
});

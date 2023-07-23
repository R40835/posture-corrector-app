// js for real time alerts (templates/main/monitoring.html)
var source = new EventSource("{% url 'main:sse' %}");
var isFirstLoad = true; // Flag to prevent popup on first load
source.addEventListener('message', function(event) {
    var data = JSON.parse(event.data);
    var backAlertsElem = document.getElementById('back-alerts');
    var neckAlertsElem = document.getElementById('neck-alerts');
    var backAlerts = parseInt(backAlertsElem.innerText);
    var neckAlerts = parseInt(neckAlertsElem.innerText);
    // Update the values of the elements with the received data
    backAlertsElem.innerText = data.back_alert;
    neckAlertsElem.innerText = data.neck_alert;
    // Show the modal popup if the value of back-alerts or neck-alerts changes
    var message = '';
    if (!isFirstLoad && parseInt(data.back_alert) > backAlerts) {
        message += 'Straighten your back! ';
    }
    if (!isFirstLoad && parseInt(data.neck_alert) > neckAlerts) {
        message += 'straighten your neck!';
    }
    if (message !== '') {
        showModal(message);
    }
    // Set the flag to false after the first load
    isFirstLoad = false;
});

function showModal(message) {
    var modal = document.getElementById('alert-modal');
    var modalMessage = document.getElementById('alert-message');
    modalMessage.innerText = message;
    var audio = document.getElementById('notification-audio');
    audio.play(); // play the audio
    modal.style.display = "block";
    setTimeout(function() {
        modal.style.display = "none";
    }, 3000);
}

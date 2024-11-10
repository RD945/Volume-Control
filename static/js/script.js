function updateVolume() {
    fetch('/get_volume')
        .then(response => response.json())
        .then(data => {
            document.getElementById('volume-percentage').textContent = `Volume: ${data.volume}%`;
        });
}

// Call updateVolume every second
setInterval(updateVolume, 1000);

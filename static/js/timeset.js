function updateMyTime() {
    var currentTime = new Date();
    var formattedTime = currentTime.getFullYear() + "-" +
                        ('0' + (currentTime.getMonth() + 1)).slice(-2) + "-" +
                        ('0' + currentTime.getDate()).slice(-2) + " " +
                        ('0' + currentTime.getHours()).slice(-2) + ":" +
                        ('0' + currentTime.getMinutes()).slice(-2) + ":" +
                        ('0' + currentTime.getSeconds()).slice(-2);
    
    document.getElementById("myTime").innerText = formattedTime;
}

// Update the time every second
setInterval(updateMyTime, 1000);

// Initial update
updateMyTime();
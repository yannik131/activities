function barClick() {
    const menu = document.getElementById("sidemenu");
    if(menu.className === "sidemenu") {
        menu.className += " clicked";
    }
    else {
        menu.className = "sidemenu";
    }
}

function playSound() {
    var audio = new Audio('https://www.wavsource.com/snds_2020-10-01_3728627494378403/sfx/boing2.wav');
    audio.play();
}

const user_websocket = new WebSocket(
    'ws://'
    + window.location.host
    + '/ws/user/'
    + {{ user.id }}
    + '/'
);

user_websocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    console.log(data.message)
    playSound();
}
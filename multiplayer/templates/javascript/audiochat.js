var streamer = new WSAudioAPI.Streamer({
    server: 'wss://'
    + window.location.host
    + '/ws/multiplayer/audio/'
    + '{{ match.id }}/'
    + '{{ user.username }}/'
});

var player = new WSAudioAPI.Player({
    server: 'wss://'
    + window.location.host
    + '/ws/multiplayer/audio/'
    + '{{ match.id }}/'
    + '{{ user.username }}/'
});

function joinAudio() {
    initAudio();
    initCrap();
    player.start();
    streamer.start();
    var button = document.getElementById("join-audio");
    button.innerHTML = "Austreten";
    button.onclick = leaveAudio;
}

function leaveAudio() {
    player.stop();
    streamer.stop();
    var button = document.getElementById("join-audio");
    button.innerHTML = "Beitreten";
    button.onclick = joinAudio;
}
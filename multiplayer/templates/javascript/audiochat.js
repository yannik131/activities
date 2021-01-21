var streamer, player;
var init_happened = false;

function joinAudio() {
    if(!init_happened) {
        initAudio();
        initCrap();
        streamer = new WSAudioAPI.Streamer({
            server: 'wss://'
            + window.location.host
            + '/ws/multiplayer/audio/'
            + '{{ match.id }}/'
            + '{{ user.username }}/'
        });
        player = new WSAudioAPI.Player({
            server: 'wss://'
            + window.location.host
            + '/ws/multiplayer/audio/'
            + '{{ match.id }}/'
            + '{{ user.username }}/'
        });
    }

    player.start();
    streamer.start();
    var button = document.getElementById("join-audio");
    button.innerHTML = "Austreten";
    button.onclick = leaveAudio;
    init_happened = true;
}

function leaveAudio() {
    player.stop();
    streamer.stop();
    var button = document.getElementById("join-audio");
    button.innerHTML = "Beitreten";
    button.onclick = joinAudio;
}
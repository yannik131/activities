var streamer, player;
var init_happened = false;

function joinAudio() {
    if(!init_happened) {
        initAudio();
        initCrap();
        prefix = getWsPrefix();
        streamer = new WSAudioAPI.Streamer({
            server: prefix
            + '/ws/multiplayer/audio/'
            + '{{ match.id }}/'
            + '{{ user.username }}/'
        });
        player = new WSAudioAPI.Player({
            server: prefix
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
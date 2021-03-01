{% load static %}
{% load i18n %}
var streamer, player;
var init_happened = false;

function joinAudio() {
    if(!init_happened) {
        initAudio();
        initCrap();
        prefix = getWsPrefix();
        streamer = new WSAudioAPI.Streamer({
            server: prefix
            + '/ws/multiplayer/audio/receive/'
            + '{{ match.id }}/'
            + '{{ user.username }}/'
        });
        player = new WSAudioAPI.Player({
            server: prefix
            + '/ws/multiplayer/audio/send/'
            + '{{ match.id }}/'
            + '{{ user.username }}/'
        });
        init_happened = true;
    }
    
    player.start();
    streamer.start();
    var button = document.getElementById("join-audio");
    button.innerHTML = "<img src='" +
    "{% static 'icons/leave.png' %}" +
    "'>" +
    "{% trans 'Austreten' %}"
    button.onclick = leaveAudio;
}

function leaveAudio() {
    try {
        player.stop();
        streamer.stop();
    } 
    catch(err) { 
        console.log("Error leaving audio: ", err);
    }
    var button = document.getElementById("join-audio");
    button.innerHTML = "<img src='" +
    "{% static 'icons/login.png' %}" +
    "'>" +
    "{% trans 'Konferenz' %}"
    button.onclick = joinAudio;
}
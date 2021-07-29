{% load static %}
{% load i18n %}

const configuration = {
    "iceServers": [{
        urls: 'turn:turn.myactivities.net:5349',
        credential: 'a cool password',
        username: 'guest'
    },
    {
        urls: 'stun:stun.myactivities.net:5349',
        credential: 'a cool password',
        username: 'guest'
    }]
};

var peerConnections = {};
var users = [];
var remoteAudioElements = {};
var remoteMediaStreams = {};
var tracks = {};
let localTrack;
var acceptingConnections = false;
var old_colors = {};

function requestShow(room_id) {
    if(user_websocket.readyState != user_websocket.OPEN) {
        user_websocket.addEventListener('open', function() { requestShow(room_id); });
    }
    else {
        send({'type': 'rtc', 'action': 'request_show', 'room_id': room_id});
    }
}

function handleRTCMessage(data) {
    switch(data.action) {
        case 'join':
            colorize(data.user_id, data.room_id, 'darkgreen');
            break;
        case 'leave':
        case 'disconnect':
            colorize(data.user_id, data.room_id, 'white');
            break;
        case 'request_show':
            if(data.room_id != audio_room_id) {
                return;
            }
            send({'type': 'rtc', 'action': 'show', 'room_id': data.room_id, 'live': acceptingConnections});
            break;
        case 'show':
            colorize(data.user_id, data.room_id, data.live? 'darkgreen': 'white');
            break;
        default:
            break;
    }
    if(!acceptingConnections || data.room_id != audio_room_id) {
        return;
    }
    //console.log(data.user_id, "sent", data.action);
    switch(data.action) {
        case 'join':
            handleJoin(data);
            break;
        case 'offer':
            handleOffer(data);
            break;
        case 'answer':
            handleAnswer(data);
            break;
        case 'candidate':
            handleCandidate(data);
            break;
        case 'leave':
        case 'disconnect':
            handleLeave(data);
            break;
        default:
            break;
    }
}

function colorize(user_id, room_id, color) {
    var user_span = document.getElementById(room_id+'-member-name-'+user_id);
    if(user_span) {
        var old_color = old_colors[user_span.id];
        var new_color;
        if(!old_color) {
            old_color = "white" || user_span.style.color;
            old_colors[user_span.id] = old_color;
        }
        if(color == "white") {
            new_color = old_colors[user_span.id];
        }
        else {
            new_color = color;
        }
        user_span.style.color = new_color;
    }
}

function setOnIceCandidate(pc, sender) {
    pc.onicecandidate = function(event) {
        if(event.candidate) {
            send({
                'type': 'rtc', 
                'action': 'candidate', 
                'candidate': event.candidate,
                'channel': 'user-'+sender
            });
        }
    }
}

function getOrCreatePeerConnection(sender) {
    var pc = peerConnections[sender];
    if(!pc) {
        //console.log("creating peer connection for", sender);
        pc = new RTCPeerConnection(configuration);
        colorize(sender, audio_room_id, 'darkgreen');
        peerConnections[sender] = pc;
        var mediaStream = new MediaStream();
        remoteMediaStreams[sender] = mediaStream;
        var audio = document.createElement('audio');
        audio.srcObject = mediaStream;
        remoteAudioElements[sender] = audio;
        
        if(localTrack) {
            pc.addTrack(localTrack);
        }
        pc.ontrack = function(event) {
            remoteMediaStreams[sender].addTrack(event.track);
            tracks[sender] = event.track;
            remoteAudioElements[sender].play(); //some browsers deactivate autoplay
        }
        users.push(sender);
    }
    return pc;
}

function handleJoin(data) {
    const pc = getOrCreatePeerConnection(data.user_id);
    pc.createOffer().then(function(offer) {
        return pc.setLocalDescription(new RTCSessionDescription(offer));
    }).then(function() {
        send({
            'type': 'rtc',
            'action': 'offer',
            'offer': pc.localDescription,
            'channel': 'user-'+data.user_id
        });
        setOnIceCandidate(pc, data.user_id);
    }).catch(function(reason) {
        console.log('Error setting local sd from local offer?', reason);
    });
}

function handleOffer(data) {
    const pc = getOrCreatePeerConnection(data.user_id);
    pc.setRemoteDescription(new RTCSessionDescription(data.offer))
    .then(function() {
        return pc.createAnswer();
    })
    .then(function(answer) {
        return pc.setLocalDescription(new RTCSessionDescription(answer));
    })
    .then(function() {
        send({
            'type': 'rtc',
            'action': 'answer',
            'answer': pc.localDescription,
            'channel': 'user-'+data.user_id
        });
        setOnIceCandidate(pc, data.user_id);
    })
    .catch(function(reason) {
        console.log('Error setting local sd after answer to', data.user_id, ':', reason, pc.signalingState);
    });
}

function handleAnswer(data) {
    const pc = peerConnections[data.user_id];
    pc.setRemoteDescription(new RTCSessionDescription(data.answer))
    .catch(function(reason) {
        console.log('Error handling answer from', data.user_id, ':', reason);
    })
}

function handleCandidate(data) {
    const pc = peerConnections[data.user_id];
    pc.addIceCandidate(new RTCIceCandidate(data.candidate))
    .catch(function(reason) {
        console.log('Error handling candidate from', data.user_id, ':', reason);
    });
}

function handleLeave(data) {
    deletePeerConnection(data.user_id);
    /*data.message = data.username+" {% trans 'verlässt die Konferenz.' %}";
    data.time = new Date();
    addMessageToChat(data);*/
}

function deletePeerConnection(user) {
    const pc = peerConnections[user];
    if(!pc) {
        return;
    }
    const track = tracks[user];
    if(track) {
        remoteMediaStreams[user].removeTrack(track);
        delete tracks[user];
        remoteAudioElements[user].remove();
        delete remoteAudioElements[user];
    }
    pc.close();
    pc.onicecandidate = null;
    pc.ontrack = null;
    delete peerConnections[user];
    users.splice(users.indexOf(user), 1);
}

function negotiate(mediaStream) {
    if(mediaStream) {
        localTrack = mediaStream.getAudioTracks()[0];
    }
    acceptingConnections = true;
    send({'type': 'rtc', 'action': 'join', 'room_id': audio_room_id});
    colorize({{ user.id }}, audio_room_id, 'darkgreen');
    var joinButton = document.getElementById('call-button-'+audio_room_id);
    if(joinButton) {
        joinButton.src = "{% static 'icons/hangup.png' %}";
        joinButton.onclick = leaveAudio;
    }
    window.addEventListener('beforeunload', function(e) {
        if(localTrack) {
            localTrack.stop();
        }
    });
}

function joinAudio(room_id, clicked) {
    if(acceptingConnections) {
        leaveAudio();
    }
    audio_room_id = room_id;
    if(navigator.mediaDevices) {
        navigator.mediaDevices.getUserMedia({audio: true}).then(function(mediaStream) {
            negotiate(mediaStream)
        });
    }
    else {
        negotiate();
    }
    if(clicked) {
        send({'type': 'chat', 'action': 'sent', 'message': "{{ user }} {% trans 'tritt der Konferenz bei.' %}", 'id': audio_room_id});
    }
}

function leaveAudio() {
    acceptingConnections = false;
    if(localTrack) {
        localTrack.stop();
    }
    while(users.length > 0) {
        deletePeerConnection(users[users.length-1]);
    }
    send({'type': 'rtc', 'action': 'leave', 'room_id': audio_room_id});
    send({'type': 'chat', 'action': 'sent', 'message': this_user+" {% trans 'verlässt die Konferenz.' %}", 'id': audio_room_id});
    colorize({{ user.id }}, audio_room_id, 'white');
    var button = document.getElementById('call-button-'+audio_room_id);
    if(button) {
        button.src = "{% static 'icons/call.png' %}";
        var room_id = audio_room_id;
        button.onclick = function() { joinAudio(room_id, true); };
    }
    audio_room_id = undefined;
}

{% if user.audio_room_id %}
    window.addEventListener('load', function() {
        user_websocket.addEventListener('open', function() {
            joinAudio({{ user.audio_room_id }});
        });
    });
{% endif %}
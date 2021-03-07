{% load static %}
{% load i18n %}


const joinBbutton = document.getElementById("join-audio");
const remoteAudio = document.getElementById('remote-audio');
let remoteMediaStream;

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
var tracks = {};
var users = [];
let localTrack;
var acceptingConnections = false;
var old_colors = {};

function requestShow() {
    send({'type': 'rtc', 'action': 'request_show', 'room_id': {{ room.id }}});
}

user_websocket.addEventListener('open', requestShow);

function handleRTCMessage(data) {
    switch(data.action) {
        case 'join':
            colorize(data.sender, 'darkgreen');
            break;
        case 'leave':
        case 'disconnect':
            colorize(data.sender, 'white');
            break;
        case 'request_show':
            send({'type': 'rtc', 'action': 'show', 'room_id': {{ room.id }}, 'live': acceptingConnections});
            break;
        case 'show':
            colorize(data.sender, data.live? 'darkgreen': 'white');
            break;
        default:
            break;
    }
    if(!acceptingConnections) {
        return;
    }
    console.log(data.sender, "sent", data.action);
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

function colorize(user, color) {
    var user_span = document.getElementById('member-name-'+user);
    if(user_span) {
        var old_color = old_colors[user_span.id];
        var new_color;
        if(!old_color) {
            old_color = user_span.style.color || "white";
            old_colors[user_span.id] = old_color;
        }
        if(color == "white") {
            new_color = old_colors[user_span.id];
        }
        else {
            new_color = color;
        }
        user_span.style.color = new_color || color;
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
        console.log("creating peer connection for", sender);
        pc = new RTCPeerConnection(configuration);
        colorize(sender, 'darkgreen');
        peerConnections[sender] = pc;
        users.push(sender);
        if(localTrack) {
            pc.addTrack(localTrack);
        }
        pc.ontrack = function(event) {
            remoteMediaStream.addTrack(event.track);
            tracks[sender] = event.track;
            remoteAudio.play(); //some browsers deactivate autoplay
        }
    }
    return pc;
}

function handleJoin(data) {
    const pc = getOrCreatePeerConnection(data.sender);
    pc.createOffer().then(function(offer) {
        return pc.setLocalDescription(new RTCSessionDescription(offer));
    }).then(function() {
        send({
            'type': 'rtc',
            'action': 'offer',
            'offer': pc.localDescription,
            'channel': 'user-'+data.sender
        });
        setOnIceCandidate(pc, data.sender);
    }).catch(function(reason) {
        console.log('Error setting local sd from local offer?', reason);
    });
}

function handleOffer(data) {
    const pc = getOrCreatePeerConnection(data.sender);
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
            'channel': 'user-'+data.sender
        });
        setOnIceCandidate(pc, data.sender);
    })
    .catch(function(reason) {
        console.log('Error setting local sd after answer to', data.sender, ':', reason, pc.signalingState);
    });
}

function handleAnswer(data) {
    const pc = peerConnections[data.sender];
    pc.setRemoteDescription(new RTCSessionDescription(data.answer))
    .catch(function(reason) {
        console.log('Error handling answer from', data.sender, ':', reason);
    })
}

function handleCandidate(data) {
    const pc = peerConnections[data.sender];
    pc.addIceCandidate(new RTCIceCandidate(data.candidate))
    .catch(function(reason) {
        console.log('Error handling candidate from', data.sender, ':', reason);
    });
}

function handleLeave(data) {
    deletePeerConnection(data.sender);
}

function deletePeerConnection(user) {
    console.log('Attempting to delete connection for', user);
    const pc = peerConnections[user];
    if(!pc) {
        console.log('No connection found, aborting');
        return;
    }
    const track = tracks[user];
    if(track) {
        remoteMediaStream.removeTrack(track);
        delete tracks[user];
    }
    pc.close();
    pc.onicecandidate = null;
    pc.ontrack = null;
    delete peerConnections[user];
    users.splice(users.indexOf(user), 1);
}

function negotiate(mediaStream) {
    remoteMediaStream = new MediaStream();
    remoteAudio.srcObject = remoteMediaStream;
    if(mediaStream) {
        localTrack = mediaStream.getAudioTracks()[0];
    }
    acceptingConnections = true;
    send({'type': 'rtc', 'action': 'join', 'room_id': '{{ room.id }}'});
    send({'type': 'chat', 'message': "{{ user }} {% trans 'tritt der Konferenz bei.' %}", 'id': {{ room.id }}});
    colorize({{ user.id }}, 'darkgreen');
    var joinButton = document.getElementById('call-button');
    joinButton.src = "{% static 'icons/hangup.png' %}";
    joinButton.onclick = leaveAudio;
    window.addEventListener('beforeunload', function(e) {
        if(localTrack) {
            localTrack.stop();
        }
    });
}

function joinAudio() {
    if(navigator.mediaDevices) {
        navigator.mediaDevices.getUserMedia({audio: true}).then(function(mediaStream) {
            negotiate(mediaStream)
        });
    }
    else {
        negotiate();
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
    send({'type': 'rtc', 'action': 'leave', 'room_id': '{{ room.id }}'});
    send({'type': 'chat', 'message': "{{ user }} {% trans 'verlässt die Konferenz.' %}", 'id': {{ room.id }}});
    colorize({{ user.id }}, 'white');
    var button = document.getElementById('call-button');
    button.src = "{% static 'icons/call.png' %}";
    button.onclick = joinAudio;
}
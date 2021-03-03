{% load static %}
{% load i18n %}


const button = document.getElementById("join-audio");
const remoteAudio = document.getElementById('remote-audio');
const remoteMediaStream = new MediaStream();
remoteAudio.srcObject = remoteMediaStream;
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

function handleRTCMessage(data) {
    if(!acceptingConnections) {
        return;
    }
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
            handleLeave(data);
            break;
        default:
            break;
    }
}

function getOrCreatePeerConnection(sender) {
    var pc = peerConnections[sender];
    if(!pc) {
        console.log("creating peer connection for", sender);
        pc = new RTCPeerConnection(configuration);
        peerConnections[sender] = pc;
        users.push(sender);
        pc.addTrack(localTrack);
        pc.ontrack = function(event) {
            remoteMediaStream.addTrack(event.track);
            tracks[pc] = event.track;
        }
        pc.onicecandidate = function(event) {
            if(event.candidate) {
                send({
                    'type': 'rtc', 
                    'action': 'candidate', 
                    'candidate': event.candidate
                });
            }
        }
    }
    return pc;
}

function handleJoin(data) {
    const pc = getOrCreatePeerConnection(data.sender);
    pc.createOffer().then(function(offer) {
        pc.setLocalDescription(new RTCSessionDescription(offer));
        send({
            'type': 'rtc',
            'action': 'offer',
            'offer': offer
        });
    });
}

function handleOffer(data) {
    pc = getOrCreatePeerConnection(data.sender);
    pc.setRemoteDescription(new RTCSessionDescription(data.offer));
    pc.createAnswer().then(function(answer) {
        pc.setLocalDescription(new RTCSessionDescription(answer));
        send({
            'type': 'rtc',
            'action': 'answer',
            'answer': answer
        });
    })
}

function handleAnswer(data) {
    pc = peerConnections[data.sender];
    pc.setRemoteDescription(new RTCSessionDescription(data.answer));
}

function handleCandidate(data) {
    pc = peerConnections[data.sender];
    pc.addIceCandidate(new RTCIceCandidate(data.candidate));
}

function handleLeave(data) {
    deletePeerConnection(data.sender);
}

function deletePeerConnection(user) {
    const pc = peerConnections[user];
    const track = tracks[pc];
    remoteMediaStream.removeTrack(track);
    tracks[pc].stop();
    delete tracks[pc];
    users.splice(users.indexOf(user), 1);
    pc.close();
    pc.onicecandidate = null;
    pc.ontrack = null;
    delete peerConnections[user];
}

function joinAudio() {
    navigator.mediaDevices.getUserMedia({audio: true}).then(function(mediaStream) {
        localTrack = mediaStream.getAudioTracks()[0];
        acceptingConnections = true;
        send({'type': 'rtc', 'action': 'join'});
        button.innerHTML = "<img src='" +
        "{% static 'icons/leave.png' %}" +
        "'>" +
        "{% trans 'Austreten' %}"
        button.onclick = leaveAudio;
    });
}

function leaveAudio() {
    acceptingConnections = false;
    socket.send(JSON.stringify({'type': 'rtc', 'action': 'leave'}));
    for(var i = 0; i < users.length; i++) {
        deletePeerConnection(users[i]);
    }
    localTrack.stop();
    button.innerHTML = "<img src='" +
    "{% static 'icons/login.png' %}" +
    "'>" +
    "{% trans 'Konferenz' %}"
    button.onclick = joinAudio;
}
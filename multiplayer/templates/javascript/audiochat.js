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
var channel_names = {};

function handleRTCMessage(data) {
    if(data.action == 'channel_request') {
        send({
            'type': 'rtc',
            'action': 'channel_name',
            'origin': data.origin
        });
        return;
    }
    else if(data.action == 'channel_name') {
        channel_names[data.sender] = data.name;
    }
    else if(data.action == 'leave') {
        delete channel_names[data.sender];
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
            console.log('adding track from', sender, ':', event.track);
            remoteMediaStream.addTrack(event.track);
            tracks[pc] = event.track;
        }
        pc.onicecandidate = function(event) {
            if(event.candidate) {
                console.log("sending candidate to", sender, event.candidate);
                send({
                    'type': 'rtc', 
                    'action': 'candidate', 
                    'candidate': event.candidate,
                    'channel': channel_names[sender]
                });
            }
        }
    }
    return pc;
}

function handleJoin(data) {
    const pc = getOrCreatePeerConnection(data.sender);
    pc.createOffer().then(function(offer) {
        pc.setLocalDescription(new RTCSessionDescription(offer)).catch(function(reason) {
            console.log('Error setting local sd from local offer?', reason);
        });
        console.log('sending offer to', data.sender);
        send({
            'type': 'rtc',
            'action': 'offer',
            'offer': offer,
            'channel': channel_names[data.sender]
        });
    });
}

function handleOffer(data) {
    pc = getOrCreatePeerConnection(data.sender);
    pc.setRemoteDescription(new RTCSessionDescription(data.offer)).catch(function(reason) {
        console.log('Error setting remote sd after offer from', data.sender, ':', reason);
    });
    pc.createAnswer().then(function(answer) {
        pc.setLocalDescription(new RTCSessionDescription(answer)).catch(function(reason) {
            console.log('Error setting local sd after answer to', data.sender, ':', reason);
        });
        console.log('sending answer to', data.sender);
        send({
            'type': 'rtc',
            'action': 'answer',
            'answer': answer,
            'channel': channel_names[data.sender]
        });
    })
}

function handleAnswer(data) {
    pc = peerConnections[data.sender];
    pc.setRemoteDescription(new RTCSessionDescription(data.answer)).catch(function(reason) {
        console.log('Error handling answer from', data.sender, ':', reason);
    })
}

function handleCandidate(data) {
    pc = peerConnections[data.sender];
    pc.addIceCandidate(new RTCIceCandidate(data.candidate)).catch(function(reason) {
        console.log('Error handling candidate from', data.sender, ':', reason);
    });
}

function handleLeave(data) {
    deletePeerConnection(data.sender);
}

function deletePeerConnection(user) {
    console.log('Attempting to delete connection for', user);
    console.log('peerConnections:', peerConnections, 'tracks:', tracks);
    const pc = peerConnections[user];
    console.log('PeerConnection:', pc);
    if(!pc) {
        console.log('No connection found, aborting');
        return;
    }
    const track = tracks[pc];
    console.log('Track:', track);
    remoteMediaStream.removeTrack(track);
    delete tracks[pc];
    pc.close();
    pc.onicecandidate = null;
    pc.ontrack = null;
    delete peerConnections[user];
    users.splice(users.indexOf(user), 1);
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
        window.onbeforeunload = function() {
            localTrack.stop();
        }
    });
}

function leaveAudio() {
    acceptingConnections = false;
    localTrack.stop();
    console.log('Deleting peer connections for', users);
    while(users.length > 0) {
        deletePeerConnection(users[users.length-1]);
    }
    socket.send(JSON.stringify({'type': 'rtc', 'action': 'leave'}));
    button.innerHTML = "<img src='" +
    "{% static 'icons/login.png' %}" +
    "'>" +
    "{% trans 'Konferenz' %}"
    button.onclick = joinAudio;
}
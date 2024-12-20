{% load i18n %}
{% load static %}
{% load account_tags %}

var members = {{ match.members.count }};
var start_member_limit = {{ match.start_member_limit }};

function updateMatchMembers(data) {
    switch(data.info) {
        case "joined":
            var username = document.getElementById('grid-member-'+data.position);
            username.innerHTML = data.username;
            if('{{ user }}' == '{{ match.admin }}') {
                var img = document.getElementById('kick-img-'+data.position);
                img.style.display = "flex";
                img.username = data.username;
                img.onclick = function() {
                    kickUser(this.username);
                }
            }
            members++;
            break;
        case "left":
            var username = document.getElementById('grid-member-'+data.position);
            username.innerHTML = "";
            if('{{ user }}' == '{{ match.admin }}') {
                var img = document.getElementById('kick-img-'+data.position);
                img.style.display = "none";
            }
            if(data.username === "{{ user.username }}") {
                kicked_out = true;
                location.href = "/multiplayer/lobby/{{ match.activity.name }}/kicked/";
            }
            members--;
            deletePeerConnection(data.id);
            break;
        case "start":
            location.href = "/multiplayer/game/{{ match.activity.name }}/" + data.match_id;
            break;
        case "abort":
            location.href = data.url;
            break;
    }
}

function startMatch() {
    if(members >= start_member_limit) {
        send({'type': 'multiplayer', 'action': 'start', 'match_id': {{ match.id }}});
    }
}

function kickUser(username) {
    send({'type': 'multiplayer', 'action': 'kick_user', 'username': username, 'match_id': {{ match.id }}});
}
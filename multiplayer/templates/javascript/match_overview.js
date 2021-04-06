{% load i18n %}
{% load static %}
{% load account_tags %}

var members = {{ match.members.count }};
var member_limit = {{ match.member_limit }};

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
                location.href = "{% call_method match 'lobby_url' request %}";
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
    if(members == member_limit) {
        openLink("{% url 'multiplayer:start_match' match.activity.name match.id %}");
    }
}

function kickUser(username) {
    send({'type': 'multiplayer', 'action': 'kick_user', 'username': username, 'match_id': {{ match.id }}});
}
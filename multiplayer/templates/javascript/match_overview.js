{% load i18n %}
{% load static %}
{% load account_tags %}

var members = {{ match.members.all.count }};
var member_limit = {{ match.member_limit }};

function addChatMember(username, id, img_src) {
    var member = document.createElement('div');
    member.className = 'chat-member';
    member.onclick = function() {
        openLink("/account/detail/"+username+"/");
    }
    var img = document.createElement('img');
    if(img_src.length == 0) {
        img_src = "{% static 'icons/users-and-groups-user@32px.png' %}";
    }
    img.src = img_src;
    member.appendChild(img);
    var span = document.createElement('span');
    span.className = username+"-span";
    span.id = "member-name-"+id;
    span.innerHTML = username;
    member.appendChild(span);
    document.querySelector('.chat-members').appendChild(member);
    var all_members = document.getElementsByClassName('chat-member');
    for(var i = 0; i < all_members.length; i++) {
        all_members[i].id = "member-"+i;
    }
    moveMembers(all_members.length);
}

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
            addChatMember(data.username, data.id, data.url);
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
            var member_span = document.querySelector('.'+data.username+"-span");
            var parent = member_span.parentElement;
            parent.remove();
            moveMembers();
            deletePeerConnection(data.id);
            colorize(data.id, 'white');
            members--;
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
    console.log('kicking', username);
    send({'type': 'multiplayer', 'action': 'kick_user', 'username': username, 'match_id': {{ match.id }}});
}


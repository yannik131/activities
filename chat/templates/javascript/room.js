{% load i18n %}
{% load thumbnail %}
{% load account_tags %}
{% load static %}

var top = document.querySelector('.chat-top');
var middle = document.querySelector('.chat-middle');
var bottom = document.querySelector('.chat-bottom');
var input = document.querySelector('.chat-input');
var whitespaceRegex = /\s/
var kicked_out = false;

input.onkeyup = function(e) {
    if(e.which == 13 && !e.shiftKey) {
        submitClick();
    }
}

input.addEventListener('focusout', function() {
    window.scrollTo(0, 0);
});

window.addEventListener('resize', function() {
    window.scrollTo(0, 0);
});

function submitClick() {
    var message = input.innerText;
    while(message.slice(-1).search(whitespaceRegex) != -1) {
        message = message.slice(0, -1);
    }
    message = message.replace('\n\n', '\n');
    input.innerHTML = "";
    if(message.length > 0) {
        user_websocket.send(JSON.stringify({'type': 'chat', 'message': message, 'id': {{ room.id }}}));
    }
};

function addMessageToChat(data) {
    var msg = document.createElement('div');
    var info = document.createElement('div');
    info.className = 'message-info';
    var isMe = data.username === '{{ request.user.username }}';
    var name = isMe ? "{% trans 'Sie' %}" : data.username;
    msg.className = isMe? 'chat-message-right' : 'chat-message-left';
    info.innerHTML = name + ', ' + format_time_str(data.time);
    info.style.fontWeight = "bold";
    msg.appendChild(info);
    var message = document.createElement('div');
    message.innerHTML = data.message.replace('\n', '<br>');
    msg.appendChild(message);
    middle.appendChild(msg);
    middle.scrollTop = msg.offsetTop;
    var game_field = document.querySelector('.game-field');
    var game_chat = document.querySelector('.game-chat');
    if(game_field && (!game_chat.style.display || game_chat.style.display == "none")) {
        var button = document.getElementById('chat-button');
        button.style.backgroundColor = "red";
    }
};

window.addEventListener('beforeunload', function(e) {
    if(kicked_out) {
        return;
    }
    user_websocket.send(JSON.stringify({'type': 'chat', 'update_check': '', 'id': {{ room.id }}}));
});

function moveMembers() {
    var padding = 10;
    var title_div = document.querySelector('.title');
    var members_div = document.querySelector('.chat-members');
    if(title_div) {
        members_div.style.left = title_div.offsetWidth+padding+"px";
    }
    else {
        members_div.style.left = 0;
        members_div.style.scrollbarWidth = "none";
        var member = document.querySelector('.chat-member');
        member.style.display = "flex";
        member.style.left = (members_div.offsetWidth-member.offsetWidth)/2+"px";
        return;
    }
    var last_member_div;
    var current_pos = 0;
    var all_members = document.getElementsByClassName('chat-member');
    for(var i = 0; i < all_members.length; i++) {
        all_members[i].id = "member-"+i;
    }
    var count = all_members.length;
    for(var i = 0; i < count; i++) {
        var member = document.getElementById('member-'+i);
        if(!member) {
            continue;
        }
        if(last_member_div) {
            current_pos += last_member_div.offsetWidth+padding;
        }
        member.style.left = current_pos+"px";
        last_member_div = member;
        member.style.display = 'flex';
    }
}

function openChat() {
    document.querySelector('.game-chat').style.display = "block";
    var button = document.getElementById('chat-button');
    button.style.backgroundColor = "#2a2a2a";
    button.style.color = "white";
    var img = document.getElementById('open-chat-img');
    img.src = "{% static 'icons/leave.png' %}";
    document.getElementById('chat-button').onclick = closeChat;
    var last_msg = document.getElementById('last-message');
    if(last_msg) {
        document.querySelector('.chat-middle').scrollTop = last_msg.offsetTop;
    }
    moveMembers();
}

function closeChat() {
    document.querySelector('.game-chat').style.display = "none";
    var img = document.getElementById('open-chat-img');
    img.src = "{% static 'icons/chat.png' %}";
    document.getElementById('chat-button').onclick = openChat;
}

function positionChat() {
    var middle = document.querySelector('.chat-middle');
    var last_msg = document.getElementById('last-message');
    if(last_msg) {
        middle.scrollTop = last_msg.offsetTop;
    }
    moveMembers();
}

window.addEventListener('resize', positionChat);

window.addEventListener('load', positionChat);


{% load i18n %}
{% load thumbnail %}
{% load account_tags %}
{% load static %}

var room_id;
var whitespaceRegex = /\s/
var kicked_out = false;
var room_imgs_loaded = {};

function init_chat(pk) {
    var chat_input = document.getElementById('chat-input-'+pk);
    room_imgs_loaded[pk] = 0;
    room_id = pk;

    chat_input.onkeyup = function(e) {
        if(e.which == 13 && !e.shiftKey) {
            submitClick();
        }
    }

    chat_input.addEventListener('focusout', function() {
        window.scrollTo(0, 0);
    });

    window.addEventListener('resize', function() {
        window.scrollTo(0, 0);
    });
}

function handleChatMessage(data) {
    switch(data.action) {
        case 'join':
            addChatMember(data.username, data.user_id, data.room_id, data.url);
            data.time = new Date();
            data.message = data.username + " {% trans 'ist dem Chat beigetreten.' %}";
            addMessageToChat(data);
            break;
        case 'leave':
            var member_span = document.querySelector('.'+data.username+"-span");
            var parent = member_span.parentElement;
            parent.remove();
            room_imgs_loaded[data.room_id] -= 2;
            moveMembers(data.room_id);
            data.time = new Date();
            data.message = data.username + " {% trans 'hat den Chat verlassen.' %}";
            addMessageToChat(data);
            break;
        case 'sent':
            addMessageToChat(data);
            break;
        default:
            console.error('Unknown action', data.action);
    }
}

function submitClick() {
    var chat_input = document.getElementById('chat-input-'+room_id);
    var message = chat_input.innerText;
    while(message.slice(-1).search(whitespaceRegex) != -1) {
        message = message.slice(0, -1);
    }
    message = message.replace('\n\n', '\n');
    chat_input.innerHTML = "";
    if(message.length > 0) {
        user_websocket.send(JSON.stringify({'type': 'chat', 'action': 'sent', 'message': message, 'id': room_id}));
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
    var middle = document.getElementById('middle-'+data.room_id);
    middle.appendChild(msg);
    middle.scrollTop = msg.offsetTop;
    if(!isMe) {
        playSound("https://www.wavsource.com/snds_2020-10-01_3728627494378403/sfx/click_x.wav");
    }
};

window.addEventListener('beforeunload', function(e) {
    if(kicked_out || !room_id) {
        return;
    }
    user_websocket.send(JSON.stringify({'type': 'chat', 'update_check': '', 'id': room_id}));
});

function moveMembers(id) {
    if(!room_id) {
        init_chat(id);
    }
    room_imgs_loaded[id]++;
    var members_div = document.getElementById('chat-members-'+room_id);
    var all_members = members_div.getElementsByClassName('chat-member');
    if(room_imgs_loaded[id] < all_members.length) {
        return;
    }
    var padding = 10;
    var title_div = document.getElementById('title-'+room_id);
    
    if(title_div) {
        members_div.style.left = title_div.offsetWidth+padding+"px";
    }
    else {
        members_div.style.left = 0;
        members_div.style.scrollbarWidth = "none";
        var member = all_members[0];
        member.style.display = "flex";
        member.style.left = (members_div.offsetWidth-member.offsetWidth)/2+"px";
        return;
    }
    var last_member_div;
    var current_pos = 0;
    for(var i = 0; i < all_members.length; i++) {
        all_members[i].id = room_id+"-member-"+i;
        var member = all_members[i];
        if(!member) {
            continue;
        }
        member.style.zIndex = 10000;
        if(last_member_div) {
            current_pos += last_member_div.offsetWidth+padding;
        }
        member.style.left = current_pos+"px";
        last_member_div = member;
        member.style.display = 'flex';
    }
}

function positionChat() {
    var chat_window = document.getElementById('chat-window-'+room_id);
    if(!chat_window) {
        return;
    }
    var last_msg = document.getElementById('last-message-'+room_id);
    if(last_msg) {
        var middle = document.getElementById('middle-'+room_id);
        middle.scrollTop = last_msg.offsetTop;
    }
}

function addChatMember(username, user_id, room_id, img_src) {
    var member = document.createElement('div');
    member.className = 'chat-member';
    member.onclick = function() {
        openLink("/account/detail/"+username+"/");
    }
    var img = document.createElement('img');
    member.appendChild(img);
    var span = document.createElement('span');
    span.className = username+"-span";
    span.id = room_id+"-member-name-"+user_id;
    span.style.color = "yellow";
    span.innerHTML = username;
    member.appendChild(span);
    var chat_window = document.getElementById('chat-window-'+room_id);
    chat_window.querySelector('.chat-members').appendChild(member);
    
    img.addEventListener('load', function() {
        moveMembers(room_id);
    });
    if(img_src.length == 0) {
        img_src = "{% static 'icons/users-and-groups-user@32px.png' %}";
    }
    img.src = img_src;
}

window.addEventListener('resize', positionChat);

window.addEventListener('load', positionChat);
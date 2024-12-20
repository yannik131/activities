{% load i18n %}
{% load thumbnail %}
{% load account_tags %}
{% load static %}

var whitespaceRegex = /\s/
var kicked_out = false;
var room_imgs_loaded = {};
var audio_room_id;
var is_typing = false;
var stopped_typing_callback;

function init_chat(pk) {
    if(room_imgs_loaded[pk] != undefined) {
        return;
    }
    var chat_input = document.getElementById('chat-input-'+pk);
    room_imgs_loaded[pk] = 0;

    chat_input.onkeydown = function(e) {
        if(e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitClick(this);
            if(stopped_typing_callback) {
                sendStoppedTyping(chat_input.id.split('-')[2]);
            }
        }
        else {
            sendIsTyping(this);
        }
    }
    var joinButton = document.getElementById('call-button-'+audio_room_id);
    if(joinButton) {
        joinButton.src = "{% static 'icons/hangup.png' %}";
        joinButton.onclick = leaveAudio;
        var user_span = document.getElementById(audio_room_id+'-member-name-{{ user.id }}');
        if(user_span) {
            user_span.style.color = 'darkgreen';
        }
    }
    
    var send_img = document.getElementById('chat-img-'+pk);
    send_img.onclick = function() { submitClick(chat_input); }

    chat_input.addEventListener('focusout', function() {
        window.scrollTo(0, 0);
    });

    window.addEventListener('resize', function() {
        window.scrollTo(0, 0);
    });
    requestShow(pk);
}

function sendIsTyping(chat_input) {
    var room_id = chat_input.id.split('-')[2];
    if(stopped_typing_callback) {
        clearTimeout(stopped_typing_callback);
    }
    else {
        send({'type': 'chat', 'action': 'typing', 'id': room_id});
    }
    stopped_typing_callback = setTimeout(function() { sendStoppedTyping(room_id); }, 2000);
}

function sendStoppedTyping(room_id) {
    if(stopped_typing_callback) {
        send({'type': 'chat', 'action': 'stopped_typing', 'id': room_id});
        clearTimeout(stopped_typing_callback);
        stopped_typing_callback = null;
    }
}

function handleTypingState(room_id, user_id, state) {
    if(user_id == this_user_id) {
        return;
    }
    var user_span = document.getElementById(room_id+'-member-name-'+user_id);
    if(!user_span) {
        return;
    }
    if(state) {
        old_colors[user_id] = user_span.style.color;
        user_span.style.color = "red";
    }
    else {
        user_span.style.color = old_colors[user_id] == 'darkgreen'? 'darkgreen' : 'yellow';
    }
}

function handleChatMessage(data) {
    switch(data.action) {
        case 'join':
            addChatMember(data.username, data.user_id, data.sex, data.room_id, data.url);
            data.time = new Date();
            data.message = data.username + " {% trans 'ist dem Chat beigetreten.' %}";
            addMessageToChat(data);
            break;
        case 'leave':
            var member_span = document.getElementById(`${data.room_id}-member-name-${data.user_id}`);
            var parent = member_span.parentElement;
            parent.remove();
            room_imgs_loaded[data.room_id] -= 2;
            moveMembers(data.room_id);
            data.time = new Date();
            data.message = data.username + " {% trans 'hat den Chat verlassen.' %}";
            changeMembersCount(-1, data.room_id);
            addMessageToChat(data);
            break;
        case 'delete':
            console.log("todo: delete");
            break;
        default:
            console.error('Unknown action', data.action);
    }
}

function submitClick(chat_input) {
    var room_id = chat_input.id.split('-')[2];
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
};

function manageChatWindows(action, room_id, target, is_this_user) {
    const list = document.getElementById('chat-list');
    if(list && is_this_user) {
        const item = document.getElementById(`chat-item-${room_id}`);
        switch(action) {
            case 'join':
                if(!item) {
                    addItemToChatList(room_id, target, list);
                }
                break;
            case 'leave':
            case 'delete':
                if(item) {
                    removeItemFromChatList(room_id);
                }
                break;
        }
    }
}

function addItemToChatList(room_id, target, list) {
    list.innerHTML += `
    <div class="chat-item" id="chat-item-${room_id}" onclick="requestChatWindow(${room_id})">\
        <div class="chat-list-image">\
            <img src="">\
        </div>\
        <div class="chat-list-title">\
        ${list.children.length+1}. ${target}\
        </div>\
        <div class="chat-bell">\
            <img src="{% static 'icons/bell.png' %}" id="chat-bell-${room_id}" style="display: none">\
        </div>\
    </div>'`
}

function removeItemFromChatList(room_id) {
    document.getElementById(`chat-item-${room_id}`).remove();
    const chat_window = document.getElementById(`chat-window-${room_id}`);
    if(chat_window) {
        chat_window.remove();
    }
}

/*window.addEventListener('beforeunload', function(e) {
    if(kicked_out || !document.getElementsByClassName('chat-top')) {
        return;
    }
    user_websocket.send(JSON.stringify({'type': 'chat', 'update_check': '', 'id': room_id}));
});*/

function moveMembers(room_id) {
    init_chat(room_id);
    room_imgs_loaded[room_id]++;
    var members_div = document.getElementById('chat-members-'+room_id);
    var all_members = members_div.getElementsByClassName('chat-member');
    if(room_imgs_loaded[room_id] < all_members.length) {
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
        member.style.zIndex = 2;
        if(last_member_div) {
            current_pos += last_member_div.offsetWidth+padding;
        }
        member.style.left = current_pos+"px";
        last_member_div = member;
        member.style.display = 'flex';
    }
}

function positionChat(room_id) {
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

function addChatMember(username, user_id, sex, room_id, img_src) {
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
    document.getElementById(`chat-members-${room_id}`).appendChild(member);
    
    img.addEventListener('load', function() {
        moveMembers(room_id);
    });
    if(img_src.length == 0) {
        if(sex == 'm') {
            img_src = "{% static 'icons/male_user.png' %}";
        }
        else if(sex == 'w') {
            img_src = "{% static 'icons/female_user.png' %}";
        }
        else {
            img_src = "{% static 'icons/male_female_user.png' %}";
        }
    }
    img.src = img_src;
    changeMembersCount(1, room_id);
}

function changeMembersCount(n, room_id) {
    var span = document.getElementById(`total-members-count-${room_id}`);
    span.innerHTML = parseInt(span.innerText)+n;
}

if(current_room_id) {
    window.addEventListener('load', function() { positionChat(current_room_id); });
}

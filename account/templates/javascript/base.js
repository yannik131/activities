{% load i18n %}
{% load static %}

var user_websocket;
var reconnect_count = 0;
const this_user = "{{ user }}";
var unload_room_id;
let current_room_id;
{% if current_chat_room %}
    current_room_id = {{ current_chat_room.id }};
{% elif user.audio_room_id %}
    current_room_id = {{ user.audio_room_id }};
{% endif %}

function activateMenu(element_id) {
    var content = document.querySelector('.content');
    const menu = document.getElementById(element_id);
    var widescreen = window.innerWidth >= 850;
    if(element_id == 'right-chat') {
        if(menu) {
            if(menu.style.display != "none") {
                menu.style.display = "none";
                content.style.right = 0;
                unload_room_id = undefined;
            }
            else {
                menu.style.display = "flex";
                if(widescreen) {
                    content.style.right = "355px";
                }
                var items = document.getElementsByClassName('chat-item');
                for(var i = 0; i < items.length; i++) {
                    if(items[i].style.backgroundColor == 'darkcyan') {
                        const split = items[i].id.split('-');
                        unload_room_id = parseInt(split[split.length-1]);
                        document.getElementById('chat-bell-'+unload_room_id).style.display = 'none';
                        delete new_messages[unload_room_id];
                        updateMessageCount();
                        break;
                    };
                }
            }
        }
        else {
            send({'type': 'chat', 'action': 'list', 'language_code': '{{ request.LANGUAGE_CODE }}'});
        }
    }
    else {
        if(window.innerWidth >= 1220) {
            return;
        }
        if(menu.className == element_id)
            menu.className += " clicked";
        else
            menu.className = element_id;
    }
    if(typeof game_resize == 'function') {
        game_resize();
    }
}

function createMessage(text) {
    var container = document.querySelector('.base-container');
    var message = document.createElement('div');
    message.className = 'django-message';
    var p = document.createElement('p');
    p.innerHTML = text;
    message.appendChild(p);
    var center_div = document.createElement('div');
    center_div.className = 'center-container';
    var button = document.createElement('a');
    button.className = 'blue-button';
    button.onclick = function() {
        document.querySelector('.django-message').remove();
    }
    button.innerHTML = '{% trans 'OK!' %}';
    center_div.appendChild(button);
    message.appendChild(center_div);
    container.appendChild(message);

}

function changeCount(element_id, value) {
    count = document.getElementById(element_id);
    var oldValue = parseInt(count.textContent);
    if(isNaN(oldValue)) {
        oldValue = 0;
    }
    const newValue = oldValue + value;
    if(newValue == 0) {
        count.textContent = "";
    }
    else {
        count.textContent = newValue;
    }
}

function removeNotification(id, notification_url) {
    const userAlert = document.getElementById("notification-" + id);
    var request = new XMLHttpRequest();
    request.onreadystatechange = function() {
        if(request.readyState == 4 && request.status == 204) {
            userAlert.style.display = 'none';
            changeCount("notifications-count", -1);
            if(notification_url) {
                location.href = notification_url;
            }
        }
    }
    const url = "/notifications/delete/" + id;
    request.open("GET", url, true);
    request.send();
}

function addNotification(id, text, url) {
    const sidemenu = document.getElementById("sidemenu");
    var alert = document.createElement('div');
    alert.className = 'alert';
    alert.id = 'notification-'+id;
    alert.style.fontWeight = 'bold';
    alert.innerHTML = (
        '<a class="notification-url" onclick="removeNotification('+id+', \''+url+'\')">'+ 
            text+ 
        '</a>'+
        '<div class="closebtn-container" onclick="removeNotification('+id+');">'+
            '<div class="closebtn"">'+
                '&times;'+
            '</div>'+
        '</div>'
    );
    const logout = document.getElementById('m-logout');
    sidemenu.insertBefore(alert, logout.nextElementSibling);
    changeCount("notifications-count", 1);
}

function playSound(url) {
    const audio = new Audio(url);
    audio.volume = 1;
    audio.play().catch(function(reason) {
        console.log('Sound could not be played:', reason);
    });
}

function format_time_str(time) {
    var language = window.location.hostname.split('.')[0]
    if(language != 'de' && language != 'en') {
        language = 'de';
    }
    return new Date(time).toLocaleString(language);
}

function getWsPrefix() {
    if(location.protocol == "https:") {
        return "wss://" + window.location.host;
    }
    return "ws://" + window.location.host;
}

function manageChatItems(room_id) {
    var room = document.getElementById('chat-window-'+room_id);
    //this is a stand-alone chat
    if(room && room.parentElement.id != 'live-chat') {
        return;
    }
    var right_chat = document.getElementById('right-chat');
    if(right_chat && right_chat.style.display != 'none') {
        var item = document.getElementById('chat-item-'+room_id);
        if(item) {
            var parent = item.parentElement;
            item.remove();
            parent.insertBefore(item, parent.firstChild);
        }
    }
    if(unload_room_id == room_id) {
        return;
    }
    new_messages[room_id] = '1';
    updateMessageCount();
    var bell = document.getElementById('chat-bell-'+room_id);
    if(bell) {
        bell.style.display = 'flex';
    }
}

function connect() {
    reconnect_count++;
    user_websocket = new WebSocket(
        getWsPrefix()
        + '/ws/user/'
        + '{{ user.id }}/'
        + '{{ user.ws_key }}/'
    );
    user_websocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        switch(data.type) {
            case "chat_message":
                switch(data.action) {
                    case 'room':
                        var chat = document.getElementById('live-chat');
                        var div = document.createElement('div');
                        div.className = 'chat-window';
                        div.id = 'chat-window-'+data.id;
                        div.innerHTML = data.html;
                        chat.appendChild(div);
                        showChat(div, data.id);
                        init_chat(data.id);
                        positionChat(data.id);
                        break;
                    case 'list':
                        if(!data.html) {
                            createMessage("{% trans 'Sie haben noch keine Chats. Finden Sie Freunde, Gruppen, Aktivitäten etc., um zu chatten!' %}");
                            return;
                        }
                        var menu = document.getElementById('right-chat');
                        if(!menu) {
                            var container = document.getElementById('base-container');
                            var div = document.createElement('div');
                            div.innerHTML = data.html;
                            div.className = 'right-chat';
                            div.id ='right-chat';
                            div.style.display = 'none';
                            container.appendChild(div);
                            activateMenu('right-chat');
                            if(current_room_id) {
                                var item = document.getElementById(`chat-item-${current_room_id}`);
                                if(item) {
                                    requestChatWindow(current_room_id);
                                    document.getElementById('chat-list').scrollTop = item.offsetTop-20;
                                }
                            }
                            updateMessageCount();
                        }
                        break;
                    case 'sent':
                        var chat_window = document.getElementById('chat-window-'+data.room_id);
                        if(chat_window) {
                            addMessageToChat(data);
                        }
                        manageChatItems(data.room_id);
                        if(data.username != this_user) {
                            playSound("{% static 'sounds/click.wav' %}");
                        }
                        break;
                    case 'leave':
                    case 'join':
                    case 'delete':
                        manageChatWindows(data.action, data.room_id, data.target, data.username == this_user);
                        break;
                    default:
                        console.error('Unknown chat action', data.action);
                }
                break;
            case "notification":
                if(data.action == "close") {
                    alert("{% trans 'Verbindung getrennt, weil ein neuer Tab geöffnet wurde! Bitte verwenden Sie nur einen Tab für myactivities.net :)' %}");
                    return;
                }
                addNotification(data.id, data.text, data.url);
                playSound("{% static 'sounds/boing.wav' %}");
                break;
            case "multiplayer":
                if(data.action == "match_list") {
                    updateMatchList(data);
                }
                else if(data.action == "members_changed") {
                    if(typeof updateMatchMembers != "undefined") {
                        updateMatchMembers(data);
                    }
                }
                break;
            case "rtc":
                if(typeof handleRTCMessage != 'undefined')
                    handleRTCMessage(data);
                break;
            case 'character':
                handleCurrentQuestion(data.current_question);
                break;
        }
    }

    user_websocket.onclose = function(e) {
        if(e.code == 1000) {
            return;
        }
        console.log('User socket closed unexpectedly. Attempting reconnect in 1 second. Code: ', e);
        if(reconnect_count > 15) {
            alert("{% trans 'Es konnte keine Verbindung zum Server aufgebaut werden! Laden Sie die Seite bitte neu. Falls das nicht hilft, beschweren Sie sich gerne bei myactivities.net@web.de! Jedes Feedback hilft.' %}");
        }
        else {
            setTimeout(function() {
                connect();
            }, 1000);
        }
        
    }

    user_websocket.onerror = function(err) {
        console.error('User socket encountered error: ', err, 'Closing socket.');
        user_websocket.close();
    }
}

function send(message) {
    user_websocket.send(JSON.stringify(message));
}

function parse(json_string) {
    if(typeof json_string == "undefined" || !json_string.length) {
        return null;
    }
    return JSON.parse(json_string);
}

function openLink(link) {
    if(arguments.length > 2) {
        var search = new URLSearchParams(location.search);
        for(var i = 1; i+1 < arguments.length; i += 2) {
            search.set(arguments[i], arguments[i+1]);
        }
        link += "?"+search.toString();
    }
    if(arguments.length % 2 == 0) {
        const last_argument = arguments[arguments.length-1];
        if(typeof last_argument == 'string' && last_argument.length > 1 && last_argument[0] == '#') {
            link += last_argument;
        }  
    }
    location.href = link;
}

function footerResize(max) {
    // First we get the viewport height and we multiple it by 1% to get a value for a vh unit
    var vh = window.innerHeight*0.01;
    if(max) {
        var body = document.body,
        html = document.documentElement;

        vh = Math.max(body.scrollHeight, body.offsetHeight, html.clientHeight, html.scrollHeight, html.offsetHeight)*0.01;
    // Then we set the value in the --vh custom property to the root of the document
    }
    document.documentElement.style.setProperty('--vh', `${vh}px`);
}

footerResize();

window.addEventListener('resize', footerResize);

function showChat(chat, id) {
    var chats = document.getElementsByClassName('chat-window');
    for(var i = 0; i < chats.length; i++) {
        chats[i].style.display = "none";
    }
    chat.style.display = 'flex';
    room_id = id;
    var bell = document.getElementById('chat-bell-'+room_id);
    bell.style.display = "none";
    var items = document.getElementsByClassName('chat-item');
    for(var i = 0; i < items.length; i++) {
        items[i].style.backgroundColor = 'darkgray';
    }
    var item = document.getElementById('chat-item-'+id);
    item.style.backgroundColor = 'darkcyan';
}

function requestChatWindow(room_id) {
    var chat = document.getElementById('chat-window-'+room_id);
    unload_room_id = room_id;
    if(chat) {
        showChat(chat, room_id);
    }
    else {
        send({'type': 'chat', 'action': 'room', 'id': room_id});
    }
    delete new_messages[room_id];
    updateMessageCount();
}

function get_color(percent, reverse) {
    if(!reverse) {
        return "rgb("+((1-percent)*255)+","+(percent*255)+",0)";
    }
    else {
        return "rgb("+(percent*255)+","+((1-percent)*255)+",0)";
    }
}

function updateMessageCount() {
    const keys = Object.keys(new_messages);
    document.getElementById('messages-count').innerHTML = keys.length;
    if(document.getElementById('chat-list')) {
        for(var i = 0; i < keys.length; i++) {
            var bell = document.getElementById('chat-bell-'+keys[i]);
            if(bell) {
                bell.style.display = 'flex';
            }
        }
    }
}

window.addEventListener('load', updateMessageCount);

function sendUpdateCheck(room_id) {
    user_websocket.send(JSON.stringify({'type': 'chat', 'action': 'sent', 'id': room_id, 'update_check': '1'}));
}

{% if user.is_authenticated %}
    connect();
    window.addEventListener('beforeunload', function() {
        if(unload_room_id && !new_messages[unload_room_id]) {
            sendUpdateCheck(unload_room_id);
        }
        if(current_room_id) {
            sendUpdateCheck(current_room_id);
        }
        user_websocket.close();
    });
{% endif %}
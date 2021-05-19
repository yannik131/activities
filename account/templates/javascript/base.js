{% load i18n %}

var user_websocket;
const this_user = "{{ user }}";

function activateMenu(element_id) {
    var content = document.querySelector('.content');
    const menu = document.getElementById(element_id);
    var widescreen = window.innerWidth >= 850;
    if(element_id == 'right-chat') {
        if(menu) {
            if(menu.style.display != "none") {
                menu.style.display = "none";
                content.style.right = 0;
            }
            else {
                menu.style.display = "flex";
                if(widescreen) {
                    content.style.right = "355px";
                }
            }
        }
        else {
            send({'type': 'chat', 'action': 'list', 'language_code': '{{ request.LANGUAGE_CODE }}'});
        }
        count = document.getElementById('messages-count');
        count.innerHTML = "";
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
    var button = document.createElement('a');
    button.className = 'blue-button';
    button.onclick = function() {
        document.querySelector('.django-message').remove();
    }
    button.innerHTML = '{% trans 'OK!' %}';
    message.appendChild(button);
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
    audio.volume = 0.5;
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

function addMessageToChatMenu(data) {
    var item = document.getElementById('chat-item-'+data.room_id);
    if(item) {
        var chat = document.getElementById('chat-window-'+data.room_id);
        if(!chat || window.getComputedStyle(chat).display == 'none') {
            var parent = item.parentElement;
            item.remove();
            parent.insertBefore(item, parent.firstChild);
            var bell = document.getElementById('chat-bell-'+data.room_id);
            bell.style.display = 'flex';
        }
    }
    changeCount("messages-count", 1);
}

function getWsPrefix() {
    if(location.protocol == "https:") {
        return "wss://" + window.location.host;
    }
    return "ws://" + window.location.host;
}

function connect() {
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
                        positionChat();
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
                            {% if current_chat_room %}
                                requestChatWindow({{ current_chat_room.id }});
                            {% endif %}
                            activateMenu('right-chat');
                        }
                        break;
                    case 'sent':
                    case 'leave':
                    case 'join':
                        const is_this_user = data.username == this_user;
                        var chat = document.getElementById('chat-window-'+data.room_id);
                        if(chat) {
                            handleChatMessage(data);
                        }
                        else if(data.action == 'sent' && !is_this_user) {
                            addMessageToChatMenu(data);
                            playSound("https://www.wavsource.com/snds_2020-10-01_3728627494378403/sfx/click_x.wav");
                        }
                        else if(data.action == 'leave' || data.action == 'join') {
                            manageChatWindows(data.action, data.room_id, data.target, is_this_user);
                        }
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
                playSound("https://www.wavsource.com/snds_2020-10-01_3728627494378403/sfx/boing_x.wav")
                break;
            case "multiplayer":
                if(data.action == "match_list") {
                    updateMatchList(data);
                }
                else if(data.action == "members_changed") {
                    if(typeof updateMatchMembers != "undefined") {
                        updateMatchMembers(data);
                    }
                    else {
                        //TODO: Add notification
                    }
                }
                break;
            case "rtc":
                if(typeof handleRTCMessage != 'undefined')
                    handleRTCMessage(data);
                break;
        }
    }

    user_websocket.onclose = function(e) {
        if(e.code == 1000) {
            return;
        }
        console.log('User socket closed unexpectedly. Attempting reconnect in 1 second. Code: ', e);
        setTimeout(function() {
            connect();
        }, 1000);
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
    if(chat) {
        showChat(chat, room_id);
    }
    else {
        send({'type': 'chat', 'action': 'room', 'id': room_id});
    }
}

function get_color(percent, reverse) {
    if(!reverse) {
        return "rgb("+((1-percent)*255)+","+(percent*255)+",0)";
    }
    else {
        return "rgb("+(percent*255)+","+((1-percent)*255)+",0)";
    }
}

{% if user.is_authenticated %}
    connect();
    window.addEventListener('beforeunload', function() {
        if(user_websocket.readyState != 2 && user_websocket.readyState != 3) {
            user_websocket.close();
        }
    });
{% endif %}
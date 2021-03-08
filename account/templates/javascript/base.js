var user_websocket;

function activateMenu(element_id) {
    const menu = document.getElementById(element_id);
    if(menu.className == "chat-menu" && parseInt(document.getElementById("messages-count").textContent) == 0)
        return;
    if(menu.className == element_id)
        menu.className += " clicked";
    else
        menu.className = element_id;
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
    sidemenu.innerHTML += (
        '<div class="alert" id="notification-'
        + id
        + '"><a class="notification-url" onclick="removeNotification('
        + id 
        + ', \''
        + url 
        + '\')">'
        + text
        + '</a><div class="closebtn-container" onclick="removeNotification('
        + id
        + ');"><div class="closebtn"">&times;</span></div>');
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
    const menu = document.getElementById("chat-menu");
    menu.innerHTML += (
        '<div class="chat-box" id="room-' +
        data.id +
        '"><a href="' +
        data.url +
        '"><span class="room-name">' +
        data.origin +
        ': </span><span class="message"><span class="message-date">' +
        format_time_str(data.time) +
        ': </span><span class="message-content">' +
        data.message +
        '</span></span></a></div>'
    );
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
        + '{{ user.id }}'
        + '/'
    );
    user_websocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        switch(data.type) {
            case "chat_message":
                var chat = document.getElementById("full-chat-" + data.id)
                if(chat) {
                    addMessageToChat(data);
                    if(data.username !== '{{ user.username }}')
                        playSound("https://www.wavsource.com/snds_2020-10-01_3728627494378403/sfx/click_x.wav");
                }
                else {
                    addMessageToChatMenu(data);
                    playSound("https://www.wavsource.com/snds_2020-10-01_3728627494378403/sfx/click_x.wav");
                }
                break;
            case "notification":
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

function resize() {
    var content = document.querySelector('.content');
    if(content) {
        content.style.height = window.innerHeight-50+"px";
    }
}

window.addEventListener('load', resize);
window.addEventListener('resize', resize);

{% if user.is_authenticated %}
    connect();
    window.addEventListener('beforeunload', function() {
        user_websocket.close();
    });
    
{% endif %}
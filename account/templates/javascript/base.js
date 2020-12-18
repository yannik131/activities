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

function removeNotification(id) {
    const userAlert = document.getElementById("notification-" + id);
    var request = new XMLHttpRequest();
    request.onreadystatechange = function() {
        if(request.readyState == 4 && request.status == 204) {
            userAlert.style.display = 'none';
            changeCount("notifications-count", -1)
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
        + '"><a href="'
        + url
        + '" class="notification-url">'
        + text
        + '</a><span class="closebtn" onclick="removeNotification('
        + id
        + ');">&times;</span></div>');
    changeCount("notifications-count", 1);
}

function playSound(url) {
    const audio = new Audio(url);
    audio.volume = 0.5;
    audio.play();
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

function connect() {
    user_websocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/user/'
        + {{ user.id }}
        + '/'
    );

    user_websocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if(data.type == "chat_message") {
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
        }
        else {
            addNotification(data.id, data.text, data.url);
            playSound("https://www.wavsource.com/snds_2020-10-01_3728627494378403/sfx/boing_x.wav")
        }
    }

    user_websocket.onclose = function(e) {
        console.log('User socket closed unexpectedly. Attempting reconnect in 1 second.', e.reason);
        setTimeout(function() {
            connect();
        }, 1000);
    };

    user_websocket.onerror = function(err) {
        console.error('User socket encountered error: ', err.message, 'Closing socket.');
        user_websocket.close();
    }
}

connect();

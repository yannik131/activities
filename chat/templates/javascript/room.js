var full_chat = document.getElementById('full-chat-{{ room.id }}');
var input = document.getElementById('chat-message-input');
var submit = document.getElementById('chat-message-submit');

input.focus();
input.onkeyup = function(e) {
    if (e.which == 13) {
        submitClick();
    }
};

function submitClick() {
    var message = input.value;
    if(message) {
        user_websocket.send(JSON.stringify({'message': message, 'id': {{ room.id }}}));
        input.value = "";
        input.focus();
    }
};

function addMessageToChat(data) {
    var message = data.message;
    var isMe = data.username === '{{ request.user.username }}';
    var name = isMe ? 'Sie' : data.username;

    full_chat.innerHTML += ('<div class="message"><b>' + name + ', ' + format_time_str(data.time) + ' </b> ' + message + '</div>');
};

window.onbeforeunload = function() {
    user_websocket.send(JSON.stringify({'update_check': '', 'id': {{ room.id }}}));
};
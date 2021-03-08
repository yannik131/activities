var socket;

function gameConnect(game, match_id, username) {
    if(!username) {
        console.log("connecting to", game, "without a username?");
        return;
    }
    socket = new WebSocket(
        getWsPrefix()
        + '/ws/multiplayer/'
        + game + "/"
        + match_id + "/"
        + username + "/"
    );

    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if(data.action == "match_list") {
            updateMatchList(data);
        }
        else {
            processMultiplayerData(data);
        }
    }
    
    socket.onopen = function() {
        sendAction("request_data");
    }

    socket.onclose = function(e) {
        if(e.code == 1000) {
            return;
        }
        console.log('Game socket closed unexpectedly. Attempting reconnect in 1 second. Code:', e.code);
        setTimeout(function() {
            gameConnect(game, match_id, username);
        }, 1000);
    }

    socket.onerror = function(err) {
        console.error('Game socket encountered error:', err.message, 'Closing socket.');
        socket.close();
    }
}

window.addEventListener('beforeunload', function() {
    socket.close();
});

function sendAction(action) {
    socket.send(JSON.stringify({
        'action': action
    }));
}
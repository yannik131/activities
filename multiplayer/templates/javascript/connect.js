function gameConnect(socket, match_id, username) {
    socket = new WebSocket(
        getWsPrefix()
        + '/ws/multiplayer/skat/'
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
        console.log('User socket closed unexpectedly. Attempting reconnect in 1 second. Code: ', e.code);
        setTimeout(function() {
            gameConnect();
        }, 1000);
    }

    socket.onerror = function(err) {
        console.error('User socket encountered error: ', err.message, 'Closing socket.');
        socket.close();
    }
}

function sendAction(action) {
    socket.send(JSON.stringify({
        'action': action
    }));
}
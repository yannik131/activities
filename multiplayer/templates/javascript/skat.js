

function skatConnect() {
    skat_websocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/multiplayer/skat/'
        + '{{ match.id }}/'
        + '{{ user.username }}/'
    );

    skat_websocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if(data.action == "match_list") {
            updateMatchList(data);
        }
        else {
            processMultiplayerData(data);
        }
    }
    
    skat_websocket.onopen = function() {
        sendAction("request_data");
    }

    skat_websocket.onclose = function(e) {
        console.log('User socket closed unexpectedly. Attempting reconnect in 1 second. Code: ', e.code);
        setTimeout(function() {
            skatConnect();
        }, 1000);
    }

    skat_websocket.onerror = function(err) {
        console.error('User socket encountered error: ', err.message, 'Closing socket.');
        skat_websocket.close();
    }
}

skatConnect();
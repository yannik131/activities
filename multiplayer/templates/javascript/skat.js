var skat_websocket;
var player_list;
var game_mode;
var this_user = "{{ user }}";
var last_bid;

function processMultiplayerData(data) {
    switch(data.action) {
        case "load_data":
            loadGameField(data);
            break;
        case "bid":
            handleBidding(data);
    }
}

function handleBidding(data) {
    changeInfoFor(data.username, data.bid);
}

function cardClicked(value, suit, card) {
    
}

function loadGameField(data) {
    removeCardsFromDeck(100);
    for(var i = 1; i < 5; i++) {
        removeCardFrom(i, 100);
    }
    player_list = JSON.parse(data.players);
    positionPlayers(player_list);
    updatePlayerInfo(data);
    addCardsToDeck(3);
    defineSortValues(ten_high=true, jacks_max=true);
    displayCards(data, player_list);
    game_mode = data.mode;
    switch(game_mode) {
        case "bidding":
            createBidButtons(data);
            break;
    }
}

function sendBid(bid) {
    skat_websocket.send(JSON.stringify({
        'bid': bid
    }));
}

function createBidButtons(data) {
    bid_values = [18, 20, 22, 23, 24, 27, 30, 33, 35, 36, 40, 44, 45, 46, 48, 50, 54, 55, 59, 60, 63, 66, 70, 72, 77, 84, 96, 120, 144, 168]
    last_bid = data.last_bid;
    if(data.active == this_user) {
        var bid = next(last_bid, bid_values);
        createButton(bid, bid, function() {
            sendBid(this.id);
        });
        createButton("Passe", "pass", function() {
            sendAction("pass");
        });
    }
}

function updatePlayerInfo(data) {
    var forehand = data.forehand;
    var middle = next(forehand, player_list);
    var behind = next(middle, player_list);
    changeInfoFor(data.forehand, "Vorhand");
    changeInfoFor(middle, "Mittelhand");
    changeInfoFor(behind, "Hinterhand");
}

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

function sendAction(action) {
    skat_websocket.send(JSON.stringify({
        'action': action
    }));
}

skatConnect();
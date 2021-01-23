var skat_websocket;
var player_list;
var game_mode;
var this_user = "{{ user }}";
var last_bid;
var player_positions;
var active;

function processMultiplayerData(data) {
    console.log("received: " + data.action + " active: " + data.active);
    if(data.active) {
        active = data.active;
    }
    switch(data.action) {
        case "load_data":
            loadGameField(data);
            break;
        case "bid":
            handleBidding(data);
            break;
        case "take":
            handleTake(data);
            break;
        case "no_take":
            chooseGameMode(data);
            break;
    }
}

function handleTake(data) {
    clearButtons();
    removeCardsFromDeck(3);
    var deck = parse(data.deck);
    addCardTo(players[active], 1, deck[0]);
    addCardTo(players[active], 1, deck[1]);
    chooseGameMode(data);
}

function chooseGameMode(data) {
    if(active != this_user) {
        return;
    }
    
}

function createTakeButtons() {
    if(this_user != active) {
        return;
    }
    createButton("Aufnehmen", "take", function() {
        sendAction("take");
    });
    createButton("Hand spielen", "no_take", function() {
        sendAction("no_take");
    });
}

function handleBidding(data) {
    clearButtons();
    var last_bid = parse(data.last_bid);
    updatePlayerInfo(last_bid[1], last_bid[0]);
    if(data.mode == "taking") {
        createTakeButtons();
    }
    else {
        createBidButtons(data.active, parse(data.highest_bid), data.more);
    }
}

function updatePlayerInfo(player, bid, game) {
    var info = "";
    if(player == active) {
        info += " (*) ";
    }
    info += player_positions[player];
    if(bid == "pass") {
        info += " nö";
    }
    else {
        info += " "+bid;
    }
    switch(game) {
        case "c": info += " Kreuz"; break;
        case "s": info += " Pik"; break;
        case "h": info += " Herz"; break;
        case "d": info += " Karo"; break;
        case "g": info += " Grand"; break;
        case "n": info += " Null"; break;
        default: break;
    }
    changeInfoFor(player, info);
}


function cardClicked(value, suit, card) {
    
}

function loadGameField(data) {
    clearButtons();
    removeCardsFromDeck(100);
    for(var i = 1; i < 5; i++) {
        removeCardFrom(i, 100);
    }
    player_list = JSON.parse(data.players);
    positionPlayers(player_list);
    updatePlayerPositions(data);
    for(var i = 0; i < player_list.length; i++) {
        var player = player_list[i];
        updatePlayerInfo(player, data[player+"_bid"])
    }
    var deck = parse(data.deck);
    if(deck.length) {
        addCardsToDeck(3);
    }
    defineSortValues(ten_high=true, jacks_max=true);
    displayCards(data, player_list);
    game_mode = data.mode;
    switch(data.mode) {
        case "bidding":
            createBidButtons(data.active, parse(data.highest_bid), data.more);
            break;
        case "taking":
            createTakeButtons();
            break;
        case "declaring":
            chooseGameMode(data);
            break;
        case "playing":
            break;
    }
}

function sendBid(bid) {
    skat_websocket.send(JSON.stringify({
        'action': 'bid',
        'bid': bid
    }));
}

function createBidButtons(active, highest_bid, more) {
    if(this_user != active) {
        return;
    }
    bid_values = [18, 20, 22, 23, 24, 27, 30, 33, 35, 36, 40, 44, 45, 46, 48, 50, 54, 55, 59, 60, 63, 66, 70, 72, 77, 84, 96, 120, 144, 168]
    if(more && highest_bid) {
        var bid = next(highest_bid[0], bid_values);
        createButton(bid, bid, function() {
            sendBid(bid);
        });
    }
    else {
        if(!highest_bid) {
            createButton(bid_values[0], bid_values[0], function() {
                sendBid(bid_values[0]);
            });
        }
        else {
            createButton("Ja, "+highest_bid[0], highest_bid[0], function() {
                sendBid(highest_bid[0]);
            });
        }
    }
    createButton("Passe", "pass", function() {
        sendBid("pass");
    });
}

function updatePlayerPositions(data) {
    var forehand = data.forehand;
    var middle = next(forehand, player_list);
    var behind = next(middle, player_list);
    player_positions = {[forehand]: "Vorhand", [middle]: "Mittelhand", [behind]: "Hinterhand"};
}

function skatConnect() {
    skat_websocket = new WebSocket(
        getWsPrefix()
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
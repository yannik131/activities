var skat_websocket;
var player_list;
var game_type; //d, c, g, ...
var this_user = "{{ user }}";
var player_positions; //uname:pos
var active;
var mode; //playing or undefined/null
var solist;

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
            chooseGameMode();
            break;
        case "declare":
            chooseGameMode();
            break;
        case "start":
            handleStart(data);
            break;
        case "play":
            handlePlay(data);
            break;
    }
    updateAllInfo();
}

function loadGameField(data) {
    clearButtons();
    removeCardsFromDeck(100);
    for(var i = 1; i < 5; i++) {
        removeCardFrom(i, 100);
    }
    player_list = JSON.parse(data.players);
    solist = data.solist;
    positionPlayers(player_list);
    updatePlayerPositions(data);
    for(var i = 0; i < player_list.length; i++) {
        var player = player_list[i];
        updatePlayerInfo(player, data[player+"_bid"], data.game_type)
    }
    var deck = parse(data.deck);
    if(deck.length) {
        addCardsToDeck(3);
    }
    defineSortValues(ten_high=true, jacks_max=true);
    displayCards(data, player_list);
    game_type = data.game_type;
    mode = data.mode;
    switch(data.mode) {
        case "bidding":
            createBidButtons(data.active, parse(data.highest_bid), data.more);
            break;
        case "taking":
            createTakeButtons();
            break;
        case "declaring":
            chooseGameMode();
            break;
        case "putting":
            handlePutting();
            break;
        case "playing":
            updateSortingOrder(data.game_type);
            mode = "playing";
            var trick = JSON.parse(data.trick);
            if(trick.length) {
                refreshStacks([JSON.parse(data.trick)]);
            }
            updatePlayerInfo(solist, null, game_type);
            break;
    }
}

function handleStart(data) {
    game_type = data.game_type;
    updateSortingOrder();
    mode = "playing";
    solist = data.solist;
    updatePlayerInfo(solist, null, game_type);
    clearButtons();
}

function handlePlay(data) {
    clearStacks();
    var trick = JSON.parse(data.trick);
    if(trick.length) {
        refreshStacks([JSON.parse(data.trick)]);
    }
    if(data.username != this_user) {
        removeCardFrom(players[data.username], 1);
    }
    updateAllInfo();
    if(data.clear) {
        setTimeout(clearStacks, 500);
    }
    if(data.round) {
        var new_data = data.round;
        if(game_type == "n") {
            alert(solist+": "+data.result);
        }
        else {
            alert(solist+": "+data.result+", Augen: "+data.points);
        }
        loadGameField(new_data);
    }
}

function updateAllInfo() {
    for(var i = 0; i < player_list.length; i++) {
        var player = player_list[i];
        updatePlayerInfo(player, null, game_type);
    }
}

function updateSortingOrder() {
    switch(game_type) {
        case "c":
        case "s":
        case "h":
        case "d":
            trump_suit = game_type;
            defineSortValues(ten_high=true, jacks_max=true);
            break;
        case "n":
            trump_suit = null;
            defineSortValues(ten_high=false, jacks_max=false);
            break;
        default:
            return;
    }
    updateCardsFor(1, true);
}

function handleTake(data) {
    clearButtons();
    removeCardsFromDeck(3);
    var deck = parse(data.deck);
    addCardTo(players[active], 1, deck[0]);
    addCardTo(players[active], 1, deck[1]);
    handlePutting();
}

function handlePutting() {
    if(this_user != active) {
        return;
    }
    createButton("Drücken", "put", function() {
        if(player1_cards.length != 10) {
            return;
        }
        var skat = [stacks[0][0].id, stacks[1][0].id];
        sendSkat(skat);
    });
    for(var i = 0; i < player1_cards.length; i++) {
        var card = player1_cards[i];
        card.onclick = function() {
            if(player1_cards.length <= 10) {
                return;
            }
            removePlayerCard(this, true);
            addStack(this.id);
            setStackCallbacks();
        }
    }
}

function setStackCallbacks() {
    for(var i = 0; i < stacks.length; i++) {
        stacks[i][0].onclick = function() {
            var cards = [];
            for(var j = 0; j < stacks.length; j++) {
                cards.push(stacks[j][0]);
            }
            stacks = [];
            for(var i = 0; i < cards.length; i++) {
                cards[i].remove();
                if(cards[i].id == this.id) {
                    continue;
                }
                else {
                    addStack(cards[i].id);
                }
            }
            addCardTo(1, 1, this.id);
            handlePutting();
            setStackCallbacks();
        }
    }
}

function sendSkat(skat) {
    skat_websocket.send(JSON.stringify({
        "action": "put", 
        "skat": JSON.stringify(skat),
        "hand": JSON.stringify(getConvertedHand())
    }));
    for(var i = 0; i < player1_cards.length; i++) {
        var card = player1_cards[i];
        var vs = getVs(card.id);
        player1_cards[i].onclick = function() {
            cardClicked(vs.calue, vs.suit, this);
        }
    }
}

function chooseGameMode() {
    clearButtons();
    if(active != this_user) {
        return;
    }
    if(stacks.length) {
        clearStacks();
        addCardsToDeck(3);
    }
    var games = [["&clubs;", "c"],
                 ["&spades;", "s"],
                 ["&hearts;", "h"],
                 ["&diams;", "d"],
                 ["Null", "n"],
                 ["Grand", "g"]];
    for(var i = 0; i < games.length; i++) {
        createButton(games[i][0], games[i][1], function() {
            sendDeclaration(this.id);
        });
    }
    var red = document.getElementById("h");
    red.style.color = "red";
    red = document.getElementById("d");
    red.style.color = "red";
}

function sendDeclaration(game) {
    skat_websocket.send(JSON.stringify({
        'action': 'declare',
        'game': game
    }));
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
    var important = false;
    if(player == active) {
        info += " (*) ";
        important = true;
    }
    info += player_positions[player];
    if(bid == "pass") {
        info += " nö";
    }
    else if(bid) {
        info += " "+bid;
    }
    if(player == solist) {
        switch(game) {
            case "c": info += " Kreuz"; break;
            case "s": info += " Pik"; break;
            case "h": info += " Herz"; break;
            case "d": info += " Karo"; break;
            case "g": info += " Grand"; break;
            case "n": info += " Null"; break;
            default: break;
        }
    }
    
    changeInfoFor(player, info, important);
}

function isTrump(value, suit) {
    switch(game_type) {
        case "c":
        case "s":
        case "h":
        case "d":
            return value == "J" || suit == game_type;
        case "g":
            return value == "J";
        default:
            return false;
    }
}

function playerHasTrump() {
    switch(game_type) {
        case "c":
        case "s":
        case "h":
        case "d":
            return playerHandContains("J", game_type);
        case "g":
            return playerHandContains("J");
        default:
            return false;
    }
}

function cardClicked(value, suit, card) {
    console.log("card clicked:", value, suit);
    if(active != this_user || mode != "playing") {
        return;
    }
    if(stacks.length == 0) {
        addStack(card.id);
        removePlayerCard(card, true);
        sendMove();
        return;
    }
    var first_card = stacks[0][0];
    var vs = getVs(first_card.id);
    switch(game_type) {
        case "c":
        case "s":
        case "h":
        case "d":
        case "g":
            if(isTrump(vs.value, vs.suit) && playerHasTrump() && !isTrump(value, suit)) {
                return;
            }
            else if(!isTrump(vs.value, vs.suit) && playerHandContains("x", vs.suit, "J") && vs.suit != suit) {
                return;
            }
            beatStack(1, card.id);
            break;
        case "n":
            if(playerHandContains("x", vs.suit) && vs.suit != suit) {
                return;
            }
            beatStack(1, card.id);
            break;
    }
    removePlayerCard(card, true);
    sendMove();
}

function compare(vs1, vs2) {
    
    return getCardSortValue(vs1.value+vs1.suit, true) > getCardSortValue(vs2.value+vs2.suit, true);
}

function indexOfHighestCard() {
    var highest_vs = getVs(stacks[0][0].id);
    var index = 0;
    for(var i = 1; i < stacks[0].length; i++) {
        var vs = getVs(stacks[0][i].id);
        if(trump_suit) {
            if(isTrump(stacks[0][0].id)) {
                if(compare(vs, highest_vs)) {
                    index = i;
                    highest_vs = vs;
                }
            }
            else {
                if(isTrump(vs.value, vs.suit)) {
                    if(compare(vs, highest_vs)) {
                        index = i;
                        highest_vs = vs;
                    }
                }
                else if(vs.suit != highest_vs.suit) {
                    continue;
                }
                else if(compare(vs, highest_vs)) {
                    index = i;
                    highest_vs = vs;
                }
            }
        }
        else {
            if(vs.suit != highest_vs.suit) {
                continue;
            }
            if(value_values[vs.value] > value_values[highest_vs.value]) {
                index = i;
                highest_vs = vs;
            }
        }
    }
    return index;
}

function sendMove() {
    if(stacks[0].length == 3) {
        skat_websocket.send(JSON.stringify({
            "action": "play",
            "trick": JSON.stringify(getConvertedStack()[0]),
            "index": indexOfHighestCard(),
            "hand": JSON.stringify(getConvertedHand())
        }));
    }
    else {
        skat_websocket.send(JSON.stringify({
            "action": "play",
            "trick": JSON.stringify(getConvertedStack()[0]),
            "hand": JSON.stringify(getConvertedHand())
        }));
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
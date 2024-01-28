{% load i18n %}

var player_list;
var game_type; //d, c, g, ...
var player_positions; //uname:pos
var active;
var mode; //playing or undefined/null
var solist;
var no_take = "";
var ouvert = false;
const bid_values = [18, 20, 22, 23, 24, 27, 30, 33, 35, 36, 40, 44, 45, 46, 48, 50, 54, 55, 59, 60, 63, 66, 70, 72, 77, 80, 81, 84, 88, 90, 96, 99, 100, 108, 110, 117, 120, 121, 126, 130, 132, 135, 140, 143, 144, 150, 154, 156, 160, 165, 168, 176, 180, 192, 216];
var game_type_translations = {
    "c": "{% trans 'Kreuz' %}",
    "s": "{% trans 'Pik' %}",
    "h": "{% trans 'Herz' %}",
    "d": "{% trans 'Karo' %}",
    "g": "{% trans 'Grand' %}",
    "n": "{% trans 'Null' %}"
};
var bid_translations = {
    "pass": "{% trans 'Nö' %}"
};

{% include 'javascript/common_sd.js' %}

function defineSortValues(ten_high, jacks_max, trump_suit) {
    var suits = ["d", "h", "s", "c"];
    var count = 100;
    for(var i = 0; i < suits.length; i++) {
        if(suits[i] == trump_suit) {
            suit_values[suits[i]] = 400;
        }
        else {
            suit_values[suits[i]] = count;
            count += 100;
        }
    }
    var values;
    if(ten_high) {
        values = ["2", "3", "4", "5", "6", "7", "8", "9", "J", "Q", "K", "10", "A"];
    }
    else {
        values = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"];
    }
    for(var i = 0; i < values.length; i++) {
        value_values[values[i]] = i;
    }
    if(jacks_max) {
        value_values["J"] = 1000;
    }
}

function getCardSortValue(type) {
    const vs = getVs(type);
    const value = vs.value, suit = vs.suit;
    if(game_type != "n" && value == "J") {
        switch(suit) {
            case "c": return 4000;
            case "s": return 3000;
            case "h": return 2000;
            case "d": return 1000;
        }
    }
    return suit_values[suit] + value_values[value];
}

function processMultiplayerData(data) {
    //console.log(JSON.stringify(data));
    if(data.active) {
        active = data.active;
    }
    clearStacksSafety();
    switch(data.action) {
        case "load_data":
            loadGameField(data);
            return;
        case "bid":
            handleBidding(data);
            return;
        case "take":
            handleTake(data);
            return;
        case "no_take":
            chooseGameMode();
            return;
        case "declare":
            chooseGameMode();
            return;
        case "start":
            handleStart(data);
            break;
        case "play":
            handlePlay(data);
            break;
        case "abort":
            location.href = data.url;
    }
    updateAllInfo();
    lastTrickButton();
}

function loadGameField(data) {
    ouvert = data.declarations.includes("o");
    game_type = data.game_type;
    mode = data.mode;
    player_list = JSON.parse(data.players);
    solist = data.solist;
    last_trick = JSON.parse(data.last_trick);
    no_take = "";
    clearStacks();
    clearButtons();
    removeCardsFromDeck(100);
    for(var i = 1; i < 5; i++) {
        removeCardFrom(i, 100);
    }
    positionPlayers(player_list);
    updatePlayerPositions(data.forehand);
    for(var i = 0; i < player_list.length; i++) {
        var player = player_list[i];
        updatePlayerInfo(player, data[player+"_bid"], data.game_type)
    }
    var deck = parse(data.deck);
    if(deck.length) {
        addCardsToDeck(3, false);
    }
    if(ouvert) {
        displayCards(data, player_list, [data.solist]);
        var hand = JSON.parse(data[data.solist]);
        for(var i = 0; i < hand.length; i++) {
            addCardTo(players[data.solist], 1, hand[i]);
        }
    }
    else {
        displayCards(data, player_list);
    }
    updateSortingOrder();
    switch(data.mode) {
        case "bidding":
            createBidButtons(data.active, parse(data.highest_bid), data.more);
            break;
        case "taking":
            createTakeButtons();
            break;
        case "declaring":
            no_take = data.declarations;
            chooseGameMode();
            break;
        case "putting":
            handlePutting();
            break;
        case "playing":
            mode = "playing";
            var trick = JSON.parse(data.trick);
            if(trick.length) {
                refreshStacks([JSON.parse(data.trick)], true);
            }
            updatePlayerInfo(solist, null, game_type);
            lastTrickButton();
            break;
    }
    if(data.summary && !document.getElementById('info-alert')) {
        var info = "";
        if(game_type.length && solist.length) {
            info += solist + ": " + game_type_translations[game_type] + "\n";
        }
        summary = info+"{% trans 'Stand nach Spiel Nummer' %} "+data.game_number+":\n"+data.summary;
        showScore();
    }
    else if(game_type.length && solist.length) {
        summary = solist + ": " + game_type_translations[game_type], info_duration;
        showScore();
    }
}

function handleStart(data) {
    if(deck.length == 0) {
        addCardsToDeck(3, false);
        if(data.solist != this_user) {
            removeCardFrom(players[data.solist], 2);
        }
        
    }
    game_type = data.game_type;
    mode = "playing";
    solist = data.solist;
    updatePlayerInfo(solist, null, game_type);
    clearButtons();
    if(data.declarations.includes("o") && this_user != data.solist) {
        ouvert = true;
        removeCardFrom(players[data.solist], 100);
        var hand = JSON.parse(data[data.solist]);
        for(var i = 0; i < hand.length; i++) {
            addCardTo(players[data.solist], 1, hand[i]);
        }
    }
    updateSortingOrder();
    createInfoAlert(solist + ": " + game_type_translations[game_type], info_duration);
}

function handlePlay(data) {
    var trick = JSON.parse(data.trick);
    if(trick.length) {
        refreshStacks([JSON.parse(data.trick)], true);
    }
    if(data.username != this_user) {
        if(ouvert && data.username == solist) {
            removeCardFrom(players[data.username], 1, trick[trick.length-1]);
        }
        else {
            removeCardFrom(players[data.username], 1);
        }
    }
    if(data.round) {
        showInitialPlayerCards(data);
        var info = "{% trans 'Stand nach Spiel Nummer' %} "+data.game_number+":\n"+solist+": ";
        if(data.result == "won")
            info += "{% trans 'gewonnen' %}"
        else if(data.result == "lost")
            info += "{% trans 'verloren' %}"
        else
            info += "{% trans 'überreizt' %}"
        if(game_type != "n") {
            info += ", {% trans 'Augen' %}: " + data.round.points;
        }
        summary = info+"\n"+data.summary;
        showScore();
        createNextRoundButton(data.round, loadGameField);
    }
    else if(data.clear) {
        clearStacksTimeout = setTimeout(clearStacksTimeoutCallback, clearStacksTimeoutDuration);
        last_trick = trick;
    }
    else {
        updatePlayerPositions(data.forehand);
    }
    if(play_automatically) {
        setTimeout(playAutomatically, data.clear? clearStacksTimeoutDuration + 50 : 100);
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
        case "n":
            defineSortValues(ten_high=false, jacks_max=false);
            break;
        case "c":
        case "s":
        case "h":
        case "d":
            defineSortValues(ten_high=true, jacks_max=true, game_type[0]);
            break;
        case "g":
        default:
            defineSortValues(ten_high=true, jacks_max=true);
            break;
    }
    updateCardsFor(1);
    if(ouvert && this_user != solist) {
        updateCardsFor(players[solist]);
    }
}

function handleTake(data) {
    clearButtons();
    removeCardsFromDeck(3);
    var deck = parse(data.deck);
    if(players[active] == 1) {
        addStack(deck[0]);
        addStack(deck[1]);
        setStackCallbacks();
    }
    else {
        addCardTo(players[active], 2);
    }
    handlePutting();
}

function handlePutting() {
    if(this_user != active) {
        return;
    }
    createButton("{% trans 'Drücken' %}", "put", function() {
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
            removePlayerCard(this, game_type != "n");
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
    socket.send(JSON.stringify({
        "action": "put", 
        "skat": JSON.stringify(skat),
        "hand": JSON.stringify(getConvertedHand())
    }));
    for(var i = 0; i < player1_cards.length; i++) {
        player1_cards[i].onclick = function() {
            var vs = getVs(this.id);
            cardClicked(vs.value, vs.suit, this);
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
        addCardsToDeck(3, false);
    }
    var games = [["&clubs; {% trans 'Kreuz' %}", "c"],
                 ["&spades; {% trans 'Pik' %}", "s"],
                 ["&hearts; {% trans 'Herz' %}", "h"],
                 ["&diams; {% trans 'Karo' %}", "d"],
                 ["Null", "n"],
                 ["Grand", "g"]];
    for(var i = 0; i < games.length; i++) {
        createButton(games[i][0], games[i][1], function() {
            prepareDeclarations(this.id);
        });
    }
    var red = document.getElementById("h");
    red.style.color = "red";
    red = document.getElementById("d");
    red.style.color = "red";
}

function prepareDeclarations(game_type) {
    clearButtons();
    if(game_type == "n") {
        createButton("{% trans 'Ouvert' %}", 'ouvert', function() {
            sendDeclaration("no");
        })
        createButton("{% trans 'Normal' %}", 'normal', function() {
            sendDeclaration("n");
        })
    }
    else if(no_take) {
        createButton("{% trans 'Normal' %}", "n", function() {
            sendDeclaration(game_type);
        })
        createButton("{% trans 'Schneider' %}", "s", function() {
            sendDeclaration(game_type+"s");
        });
        createButton("{% trans 'Schwarz' %}", "b", function() {
            sendDeclaration(game_type+"b");
        });
        createButton("{% trans 'Offen' %}", "o", function() {
            sendDeclaration(game_type+"o");
        });
    }
    else {
        sendDeclaration(game_type);
    }
}

function sendDeclaration(game) {
    socket.send(JSON.stringify({
        'action': 'declare',
        'game': game
    }));
}

function createTakeButtons() {
    if(this_user != active) {
        return;
    }
    createButton("{% trans 'Aufnehmen' %}", "take", function() {
        sendAction("take");
    });
    createButton("{% trans 'Hand spielen' %}", "no_take", function() {
        sendAction("no_take");
        no_take = true;
    });
}

function handleBidding(data) {
    handleBidGuard(data);
    clearButtons();
    if(data.round) {
        createInfoAlert("{% trans 'Eingepasst' %}", info_duration);
        showInitialPlayerCards(data);
        createNextRoundButton(data.round, loadGameField);
        return;
    }
    var last_bid = parse(data.last_bid);
    updatePlayerInfo(last_bid[1], last_bid[0]);
    if(this_user != last_bid[1]) {
        var info = last_bid[0];
        if(info == "pass") {
            info = bid_translations[info];
        }
        createInfoAlert(last_bid[1]+": "+info, info_duration);
    }
    if(data.mode == "taking") {
        createTakeButtons();
    }
    else {
        createBidButtons(data.active, parse(data.highest_bid), data.more);
    }
}

function sendBid(bid) {
    socket.send(JSON.stringify({
        'action': 'bid',
        'bid': bid
    }));
}

function updatePlayerInfo(player, bid, game) {
    var info = "";
    var important = player == active;
    if(important) {
        info += " (*) ";
    }
    info += player_positions[player];
    if(bid == "pass") {
        info += " "+bid_translations[bid];
    }
    else if(bid) {
        info += " "+bid;
    }
    if(player == solist) {
        info += " "+game_type_translations[game];
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
    if(active != this_user || mode != "playing") {
        return;
    }
    if(stacks.length == 0) {
        addStack(card.id);
        removePlayerCard(card);
        sendMove();
        return;
    }
    if(stacks[0].length == 3) {
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
            else if(!isTrump(vs.value, vs.suit) && (vs.suit != suit || isTrump(value, suit)) && playerHandContains('x', vs.suit, 'J')) {
                return;
            }
            beatStack(1, card.id, true);
            break;
        case "n":
            if(playerHandContains("x", vs.suit) && vs.suit != suit) {
                return;
            }
            beatStack(1, card.id, true);
            break;
    }
    removePlayerCard(card, game_type != "n");
    sendMove();
    active = undefined;
}

function createBidButtons(active, highest_bid, more) {
    if(this_user != active) {
        return;
    }
    if(highest_bid && highest_bid[0] == bid_values[bid_values.length-1]) {
        sendBid('pass');
        return;
    }
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
            createButton("{% trans 'Ja' %}, "+highest_bid[0], highest_bid[0], function() {
                sendBid(highest_bid[0]);
            });
        }
    }
    createButton("{% trans 'Passe' %}", "pass", function() {
        sendBid("pass");
    });
}

function updatePlayerPositions(forehand) {
    if(!forehand) {
        return;
    }
    var forehand = forehand;
    var middle = next(forehand, player_list);
    var behind = next(middle, player_list);
    player_positions = {[forehand]: "{% trans 'Vorhand' %}", [middle]: "{% trans 'Mittelhand' %}", [behind]: "{% trans 'Hinterhand' %}"};
}

window.addEventListener('load', function() {
    gameConnect('skat', '{{ match.id }}', '{{ user.username }}');
});

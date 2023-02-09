{% load i18n %}

var game_type;
var mode;
const bid_translations = {
    "healthy": "{% trans 'Gesund' %}",
    "marriage": "{% trans 'Hochzeit' %}", 
    "queens": "{% trans 'Damen' %}",
    "jacks": "{% trans 'Buben' %}",
    "clubs": "{% trans 'Kreuz' %}",
    "spades": "{% trans 'Pik' %}",
    "hearts": "{% trans 'Herz' %}",
    "diamonds": "{% trans 'Trumpf' %}",
    "without": "{% trans 'Fleischlos' %}"
};
const values = ["w", "9", "6", "3", "s"];
const value_translations = {
    "9": "{% trans 'Keine 90' %}",
    "6": "{% trans 'Keine 60' %}",
    "3": "{% trans 'Keine 30' %}",
    "s": "{% trans 'Schwarz' %}"
};
const team_translations = {
    "re": "{% trans 'Re' %}",
    "contra": "{% trans 'Kontra' %}"
};
var solist;
var re_value;
var contra_value;
var m_show;
var player_info = {};
var re;
var value_ncards;
let hand_cards_for_value;

{% include 'javascript/common_sd.js' %}

function defineSortValues() {
    var suits = ["d", "h", "s", "c"];
    var count = 0;
    for(var i = 0; i < suits.length; i++) {
        suit_values[suits[i]] = count;
        count += 10;
    }
    var values;
    if(solist && solist.length) {
        values = ["9", "J", "Q", "K", "10", "A"];
    }
    else {
        values = ["9", "K", "J", "Q", "10", "A"];
    }
    for(var i = 0; i < values.length; i++) {
        value_values[values[i]] = i;
    }
}

function getCardSortValue(type) {
    var vs = getVs(type);
    if(game_type == "diamonds" || game_type == "hearts" || game_type == "spades" || game_type == "clubs" || game_type == "marriage") {
        if(vs.value == "10" && ((game_type == "marriage" || game_type == "diamonds") && vs.suit == "h" || (game_type != "marriage" && game_type != "diamonds") && vs.suit == game_type[0])) {
            return 101;
        }
        else if(vs.value == "Q") {
            switch(vs.suit) {
                case "c": return 100;
                case "s": return 99;
                case "h": return 98;
                case "d": return 97;
            }
        }
        else if(vs.value == "J") {
            switch(vs.suit) {
                case "c": return 96;
                case "s": return 95;
                case "h": return 94;
                case "d": return 93;
            }
        }
        else if(vs.suit == game_type[0] || (game_type == "marriage" && vs.suit == "d")) {
            switch(vs.value) {
                case "A": return 92;
                case "10": return 91;
                case "K": return 90;
                case "9": return 89;
            }
        }
        else {
            return getCardSortValueDefault(type);
        }
    }
    else if(game_type == "jacks") {
        if(vs.value == "J") {
            switch(vs.suit) {
                case "c": return 96;
                case "s": return 95;
                case "h": return 94;
                case "d": return 93;
            }
        }
    }
    else if(game_type == "queens") {
        if(vs.value == "Q") {
            switch(vs.suit) {
                case "c": return 100;
                case "s": return 99;
                case "h": return 98;
                case "d": return 97;
            }
        }
    }
    return getCardSortValueDefault(type);
}

function processMultiplayerData(data) {
    //console.log("received: " + data.action + " active: " + data.active);
    if(data.active) {
        active = data.active;
    }
    switch(data.action) {
        case "load_data":
            loadGameField(data);
            break;
        case "bid":
            handleBid(data);
            break;
        case "value":
            handleValue(data);
            break;
        case "play":
            handlePlay(data);
            break;
        case "abort":
            location.href = data.url;
    }
}

function handleValue(data) {
    var info = data.username + ": ";
    value_ncards = parseInt(data.value_ncards);
    if(data.who == "re") {
        re_value = data.value;
    }
    else {
        contra_value = data.value;
    }
    if(data.value == "w") {
        info += team_translations[data.who];
    }
    else {
        info += value_translations[data.value];
    }
    createValueButtons();
    if(data.username == this_user) {
        return;
    }
    createInfoAlert(info);
}

function handlePlay(data) {
    var trick = JSON.parse(data.trick);
    if(trick.length) {
        refreshStacks([JSON.parse(data.trick)], true);
    }
    if(data.username != this_user) {
        removeCardFrom(players[data.username], 1);
    }
    if(data.m_show) {
        m_show = parseInt(data.m_show);
    }
    if(data.re_1) {
        setRe(data);
        createInfoAlert("Re: "+data.re_1+", "+data.re_2, info_duration);
    }
    if(data.round) {
        setTimeout(function() {
            clearStacks();
            var new_data = data.round;
            active = new_data.active;
            last_trick = null;
            loadGameField(new_data);
        }, 1000);
    }
    else {
        createValueButtons();
        if(data.clear) {
            setTimeout(function() {
                clearStacks();
                lastTrickButton();
            }, 500);
            last_trick = trick;
        }
    }
    updateAllInfo();
}

function handleStart() {
    for(var i = 0; i < player1_cards.length; i++) {
        player1_cards[i].onclick = function() {
            var vs = getVs(this.id);
            cardClicked(vs.value, vs.suit, this);
        }
    }
    mode = "playing";
    createValueButtons();
    if(solist.length) {
        createInfoAlert(solist + ": " + bid_translations[game_type], info_duration);
    }
    else {
        createInfoAlert("{% trans 'Normalspiel' %}", info_duration);
    }
}

function updateAllInfo() {
    for(var i = 0; i < player_list.length; i++) {
        updatePlayerInfo(player_list[i]);
    }
}

function maxCardsForValue(value) {
    if(without_nines) {
        return values_cards[value]-m_show-1;
    }
    return values_cards[value]-m_show;
}

function createValueButtons() {
    clearButtons(lastTrickButton);
    if(this_user != active || game_type == "marriage" && !m_show) {
        return;
    }
    var last_bid;
    if(re) {
        last_bid = re_value;
    }
    else {
        last_bid = contra_value;
    }
    const l = player1_cards.length;
    var value;
    if(!m_show) {
        m_show = 0;
    }
    const allowed = (value_ncards && value_ncards-player1_cards.length <= 1);
    const n = hand_cards_for_value[last_bid];
    if(last_bid == "" && (l >= n-m_show || allowed)) {
        value = "w";
    }
    else if(last_bid == "w" && (l >= n-m_show || allowed)) {
        value = "9";
    }
    else if(last_bid == "9" && (l >= n-m_show || allowed)) {
        value = "6";
    }
    else if(last_bid == "6" && (l >= n-m_show || allowed)) {
        value = "3";
    }
    else if(last_bid == "3" && (l >= n-m_show || allowed)) {
        value = "s";
    }
    if(value) {
        var trans = value_translations[value];
        if(value == "w") {
            if(re) {
                trans = "Re";
            }
            else {
                trans = "{% trans 'Kontra' %}";
            }
        }
        createButton(trans, value, function() {
            sendValue(value);
        });
    }
}

function sendValue(value) {
    socket.send(JSON.stringify({
        'action': 'value',
        'value': value,
        'who': re? "re" : "contra",
        "value_ncards": player1_cards.length-1
    }));
}

function setRe(data) {
    re = this_user == data.re_1 || this_user == data.re_2 || this_user == data.solist;
}

function handleBid(data) {
    if(data.game_type) {
        game_type = data.game_type;
        setRe(data);
        if(data.solist.length) {
            updatePlayerInfo(data.solist, undefined, data.game_type);
            solist = data.solist;
            defineSortValues();
            updateCardsFor(1);
        }
        handleStart();
        updateAllInfo();
    }
    else {
        createBidButtons();
        updatePlayerInfo(data.username, data.bid);
    }
    
}

function loadGameField(data) {
    //game_type = data.game_type;
    document.querySelector('.player5-info').style.display = "none";
    mode = data.mode;
    player_list = JSON.parse(data.players);
    solist = data.solist;
    game_type = data.game_type || "diamonds";
    re_value = data.re_value;
    contra_value = data.contra_value;
    m_show = parseInt(data.m_show);
    value_ncards = parseInt(data.value_ncards);
    last_trick = JSON.parse(data.last_trick);
    if(data.without_nines === '1') {
        hand_cards_for_value = {
            '': 9, 'w': 8, '9': 7, '6': 6, '3': 5
        };
    }
    else {
        hand_cards_for_value = {
            '': 11, 'w': 10, '9': 9, '6': 8, '3': 7
        };
    }
    setRe(data);
    defineSortValues();
    clearButtons(lastTrickButton);
    positionPlayers(player_list);
    for(var i = 0; i < player_list.length; i++) {
        var player = player_list[i];
        if(data.mode == "bidding") {
            updatePlayerInfo(player, data[player+"_bid"]);
        }
        else {
            updatePlayerInfo(player);
        }
    }
    for(var i = 1; i < 5; i++) {
        removeCardFrom(i, 100);
    }
    displayCards(data, player_list);
    switch(data.mode) {
        case "bidding":
            createBidButtons();
            break;
        case "playing":
            handleStart();
            var trick = JSON.parse(data.trick);
            if(trick.length) {
                refreshStacks([JSON.parse(data.trick)]);
            }
            break;
    }
    if(data.summary) {
        summary = "{% trans 'Spiel Nummer' %}: "+data.game_number+"\n"+data.summary;
        showScore();
    }
}

function cardClicked(value, suit, card) {
    if(this_user != active || mode != "playing") {
        return;
    }
    if(stacks.length == 0) {
        addStack(card.id);
    }
    else {
        if(stacks[0].length == 4) {
            return;
        }
        var first_vs = getVs(stacks[0][0].id);
        if(isTrump(first_vs.value, first_vs.suit) && playerHasTrump() && !isTrump(value, suit)) {
            return;
        }
        else if(!isTrump(first_vs.value, first_vs.suit) && (suit != first_vs.suit || isTrump(value, suit))) {
            var cards = getPlayerCards("x", first_vs.suit);
            for(var i = 0; i < cards.length; i++) {
                if(!isTrump(cards[i].value, cards[i].suit)) {
                    return;
                }
            }
        }
        beatStack(1, card.id, true);
    }
    active = undefined;
    removePlayerCard(card);
    sendMove();
}

function playerHasTrump() {
    for(var i = 0; i < player1_cards.length; i++) {
        var vs = getVs(player1_cards[i].id);
        if(isTrump(vs.value, vs.suit)) {
            return true;
        }
    }
    return false;
}

function isTrump(value, suit) {
    switch(game_type) {
        case "marriage":
        case "diamonds":
        case "clubs":
        case "hearts":
        case "spades":
            if(value == "Q" || value == "J" || value == "10" && ((game_type == "marriage" || game_type == "diamonds") && suit == "h" || (game_type != "marriage" && game_type != "diamonds") && suit == game_type[0])) {
                return true;
            }
            else if(game_type == "marriage" && suit == "d" || game_type[0] == suit) {
                return true;
            }
            break;
        case "queens":
            return value == "Q";
        case "jacks":
            return value == "J";
        default:
            return false;
    }
    return false;
}

function createBidButtons() {
    if(active != this_user) {
        clearButtons(lastTrickButton);
        return;
    }
    createButton("{% trans 'Gesund' %}", 'healthy', function() {
        sendBid("healthy");
    });
    var count = 0;
    for(var i = 0; i < player1_cards.length; i++) {
        if(player1_cards[i].id == "Qc") {
            count++;
        }
    }
    if(count == 2) {
        createButton(bid_translations.marriage, 'marriage', function() {
            sendBid("marriage");
        });
    }
    createButton(bid_translations.queens, 'queens', function() {
        sendBid("queens");
    });
    createButton(bid_translations.jacks, 'jacks', function() {
        sendBid("jacks");
    });
    createButton(bid_translations.clubs, 'clubs', function() {
        sendBid("clubs");
    });
    createButton(bid_translations.spades, 'spades', function() {
        sendBid("spades");
    });
    createButton(bid_translations.hearts, 'hearts', function() {
        sendBid("hearts");
    });
    createButton(bid_translations.diamonds, 'diamonds', function() {
        sendBid("diamonds");
    });
    createButton(bid_translations.without, 'without', function() {
        sendBid("without");
    });
}

function updatePlayerInfo(player, bid) {
    var info = "";
    var important = player == active;
    if(important) {
        info += " (*) ";
    }
    if(bid) {
        info += bid_translations[bid];
    }
    if(game_type.length && player == solist) {
        info += bid_translations[game_type];
    }
    
    changeInfoFor(player, info, important);
}

function sendBid(bid) {
    socket.send(JSON.stringify({
        'action': 'bid',
        'bid': bid,
        're': getConvertedHand().includes("Qc")? "1" : "0"
    }));
}

window.addEventListener('load', function() {
    gameConnect('doppelkopf', '{{ match.id }}', '{{ user.username }}');
});

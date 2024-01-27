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
var re;
var value_ncards;
let hand_cards_for_value;
let play_automatically = false;
let clearStacksTimeout;

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
        if(vs.value == "10" && ((game_type == "marriage" || game_type == "diamonds" || game_type == "hearts" || game_type == "spades" || game_type == "clubs") && vs.suit == "h")) {
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
    //console.log("received: " + data.action + "(data: " + JSON.stringify(data) + ")");
    if(data.active) {
        active = data.active;
    }
    if(clearStacksTimeout) {
        clearTimeout(clearStacksTimeout);
        clearStacksTimeout = undefined;
        clearStacksTimeoutCallback();
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

function setUpNewRound(new_data) {
    clearStacks();
    active = new_data.active;
    last_trick = null;
    loadGameField(new_data);
}

function showInitialPlayerCards(data) {
    var player_list = JSON.parse(data.round.players);
    for(let i = 0; i < player_list.length; ++i) {
        var initial_cards = JSON.parse(data[player_list[i]+"_initial_hand"]);
        for(let j = 0; j < initial_cards.length; ++j) {
            addCardTo(players[player_list[i]], 1, initial_cards[j]);
        }
    }
}

function createNextRoundButton(new_data) {
    deleteButton("last_trick");
    function callback() {
        deleteButton("next-round");
        clearStacks();
        setUpNewRound(new_data);
        removeScoreAlert();
    }
    createButton("Weiter", "next-round", callback);
    let button = document.getElementById("next-round");
    let field_width = document.querySelector('.game-field').offsetWidth;
    button.style.right = (field_width - button.offsetWidth) / 2 + "px";
    let score_alert = document.getElementById("score-alert");
    button.style.top = score_alert.offsetTop - button.offsetHeight - 5 + "px";
}

function clearStacksTimeoutCallback() {
    clearStacks();
    lastTrickButton();
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
        showInitialPlayerCards(data);
        summary = "{% trans 'Stand nach Spiel ' %}"+data.game_number+":\n"+data.summary;
        showScore();
        createNextRoundButton(data.round);
    }
    else {
        createValueButtons();
        if(data.clear) {
            clearStacksTimeout = setTimeout(clearStacksTimeoutCallback, 500);
            last_trick = trick;
        }
    }
    updateAllInfo();
    if(play_automatically) {
        setTimeout(playAutomatically, data.clear? 600 : 100);
    }
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

function createValueButtons() {
    clearButtons(lastTrickButton);
    const l = player1_cards.length;
    if(game_type == "marriage" && !m_show) {
        const n_cards_played = hand_cards_for_value["w"] + 2 - l;
        if(n_cards_played >= 3) {
            //If 3 tricks have been played and the decisive trick in the marriage has not yet happened
            //the 3rd trick is considered to have been the decisive trick
            m_show = 3;
        }
    }
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
    var value;
    if(!m_show) {
        m_show = 0;
    }
    const allowed = (value_ncards && value_ncards-player1_cards.length <= 1);
    const n = hand_cards_for_value[last_bid];
    const create_button = (l >= n-m_show || allowed);
    if(last_bid == "" && create_button) {
        value = "w";
    }
    else if(last_bid == "w" && create_button) {
        value = "9";
    }
    else if(last_bid == "9" && create_button) {
        value = "6";
    }
    else if(last_bid == "6" && create_button) {
        value = "3";
    }
    else if(last_bid == "3" && create_button) {
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
    let button = document.getElementById("next-round");
    if(button) {
        button.click();
        active = data.active;
    }
    else {
        removeScoreAlert();
    }
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

function playAutomatically() {
    if(player1_cards.length != 0) {
        let length = player1_cards.length;
        for (let i = 0; player1_cards.length == length && i < player1_cards.length; ++i) {
            player1_cards[i].click();
        }
    }
}

function loadGameField(data) {
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
        summary = "{% trans 'Stand nach Spiel ' %}"+data.game_number+":\n"+data.summary;
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


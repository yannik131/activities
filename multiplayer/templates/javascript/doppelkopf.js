{% load i18n %}

var this_user = '{{ user }}';
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
var solist;
var re_value;
var contra_value;
var m_show;

{% include 'javascript/common_sd.js' %}

function defineSortValues() {
    var suits = ["d", "h", "s", "c"];
    var count = 0;
    for(var i = 0; i < suits.length; i++) {
        suit_values[suits[i]] = count;
        count += 10;
    }
    var values = ["9", "K", "J", "Q", "10", "A"];
    for(var i = 0; i < values.length; i++) {
        value_values[values[i]] = i;
    }
}

function getCardSortValue(type) {
    var vs = getVs(type);
    if(game_type == "diamonds" || game_type == "hearts" || game_type == "spades" || game_type == "clubs" || game_type == "marriage") {
        if(type == "10h") {
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
        else if(vs.suit == game_type[0]) {
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
    console.log("received: " + data.action + " active: " + data.active);
    if(data.active) {
        active = data.active;
    }
    switch(data.action) {
        case "load_data":
            loadGameField(data);
            return;
        case "bid":
            handleBid(data);
            return;
        case "value":
            handleValue(data);
            break;
        case "start":
            handleStart();
            if(data.solist) {
                solist = data.solist;
            }
            break;
        case "play":
            handlePlay(data);
            break;
        case "abort":
            location.href = data.url;
    }
}

function handleValue(data) {
    createValueButtons();
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
    m_show = data.m_show;
    if(data.clear) {
        setTimeout(clearStacks, 500);
    }
    if(data.round) {
        var new_data = data.round;
        var info = "{% trans 'Spiel Nummer' %}: "+data.game_number+"\n";
        createInfoAlert(info+"\n"+data.summary);
        active = new_data.active;
        loadGameField(new_data);
    }
    createValueButtons();
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
}

function createValueButtons(m_show) {
    clearButtons();
    var last_bid;
    if(this_user == solist || getConvertedHand().includes("Qc")) {
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
    if(last_bid == "" && l >= 11-m_show) {
        value = "w";
    }
    else if(last_bid == "w" && l >= 10-m_show) {
        value = "9";
    }
    else if(last_bid == "9" && l >= 9-m_show) {
        value = "6";
    }
    else if(last_bid == "6" && l >= 8-m_show) {
        value = "3";
    }
    else if(last_bid == "3" && l >= 7-m_show) {
        value = "s";
    }
    if(value) {
        var trans = value_translations[value];
        if(value == "w") {
            if(getConvertedHand().includes("Qc")) {
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

function handleBid(data) {
    console.log("bid, game_type: ", data.game_type);
    if(data.game_type) {
        game_type = data.game_type;
        if(data.solist.length) {
            updatePlayerInfo(data.solist, undefined, data.game_type);
        }
        handleStart();
    }
    else {
        createBidButtons();
        updatePlayerInfo(data.username, data.bid);
    }
}

function loadGameField(data) {
    //game_type = data.game_type;
    mode = data.mode;
    player_list = JSON.parse(data.players);
    solist = data.solist;
    game_type = data.game_type || "diamonds";
    re_value = data.re_value;
    contra_value = data.contra_value;
    m_show = data.m_show;
    
    clearButtons();
    positionPlayers(player_list);
    for(var i = 0; i < player_list.length; i++) {
        var player = player_list[i];
        if(data.mode == "bidding") {
            updatePlayerInfo(player, data[player+"_bid"], undefined)
        }
        else {
            if(data.solist == player) {
                updatePlayerInfo(player, undefined, data.game_type);
            }
            else {
                updatePlayerInfo(player, undefined, undefined);
            }
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
        createInfoAlert("{% trans 'Spiel Nummer' %}: "+data.game_number+"\n"+data.summary);
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
        var first_vs = getVs(stacks[0][0].id);
        if(isTrump(first_vs.value, first_vs.suit) && playerHasTrump() && !isTrump(value, suit)) {
            return;
        }
        else if(suit != first_vs.suit) {
            var cards = getPlayerCards("x", first_vs.suit);
            for(var i = 0; i < cards.length; i++) {
                if(!isTrump(cards[i].value, cards[i].suit)) {
                    return;
                }
            }
        }
        beatStack(1, card.id);
    }
    
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
            if(value == "Q" || value == "J" || (value == "10" && suit == "h")) {
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
        clearButtons();
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

function updatePlayerInfo(player, bid, game) {
    var info = "";
    var important = player == active;
    if(important) {
        info += " (*) ";
    }
    if(bid) {
        info += bid_translations[bid];
    }
    if(game) {
        info += bid_translations[game];
    }
    
    changeInfoFor(player, info, important);
}

defineSortValues();

gameConnect('doppelkopf', '{{ match.id }}', '{{ user.username }}');
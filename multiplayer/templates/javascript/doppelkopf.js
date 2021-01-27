{% load i18n %}

var this_user = '{{ user }}';
var game_type = "Q"; //fleischlos, farbsolo, standard

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
    if(game_type == "d" || game_type == "h" || game_type == "s" || game_type == "c") {
        if(game_type == "d" && type == "10h") {
            return 101;
        }
        else if(game_type != "d" && type == "10"+game_type) {
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
        else if(vs.suit == game_type) {
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
    else if(game_type == "J") {
        if(vs.value == "J") {
            switch(vs.suit) {
                case "c": return 96;
                case "s": return 95;
                case "h": return 94;
                case "d": return 93;
            }
        }
    }
    else if(game_type == "Q") {
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
}

function loadGameField(data) {
    //game_type = data.game_type;
    mode = data.mode;
    player_list = JSON.parse(data.players);
    solist = data.solist;
    defineSortValues("d");
    updateSortingOrder();
    clearButtons();
    for(var i = 1; i < 5; i++) {
        removeCardFrom(i, 100);
    }
    positionPlayers(player_list);
    for(var i = 0; i < player_list.length; i++) {
        var player = player_list[i];
        updatePlayerInfo(player, data[player+"_solo"], data.game_type)
    }
    displayCards(data, player_list);
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
                refreshStacks([JSON.parse(data.trick)]);
            }
            updatePlayerInfo(solist, null, game_type);
            break;
    }
    if(data.summary) {
        createInfoAlert("{% trans 'Spiel Nummer' %}: "+data.game_number+"\n"+data.summary);
    }
}

function updateSortingOrder() {
    
}

function updatePlayerInfo() {
    
}

gameConnect('{{ match.id }}', '{{ user.username }}');
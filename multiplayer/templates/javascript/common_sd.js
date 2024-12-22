{% load i18n %}
{% load multiplayer_tags %}

var info_duration = 1500;
var last_trick;
beat_right = true;
let play_automatically = "{% settings_value "DEBUG" %}" === "True";
let clearStacksTimeout;
const clearStacksTimeoutDuration = 700;

function compare(vs1, vs2) {
    return getCardSortValue(vs1.value+vs1.suit) > getCardSortValue(vs2.value+vs2.suit);
}

function indexOfHighestCard() {
    var highest_vs = getVs(stacks[0][0].id);
    var index = 0;
    for(var i = 1; i < stacks[0].length; i++) {
        var vs = getVs(stacks[0][i].id);
        if(!isTrump(highest_vs.value, highest_vs.suit) && !isTrump(vs.value, vs.suit) && vs.suit != highest_vs.suit) {
            continue;
        }
        if(compare(vs, highest_vs)) {
            index = i;
            highest_vs = vs;
        }
    }
    return index;
}

function sendMove() {
    var response = {
        "action": "play",
        "trick": JSON.stringify(getConvertedStack()[0]),
        "hand": JSON.stringify(getConvertedHand())
    };
    if(stacks[0].length == player_list.length) {
        response["index"] = indexOfHighestCard();
    }
    socket.send(JSON.stringify(response));
}

function lastTrickButton() {
    if(!last_trick || last_trick.length == 0) {
        deleteButton("last_trick");
        return;
    }
    var trick = document.getElementById("last_trick0");
    var label = "{% trans 'Stich' %}";
    if(trick) {
        label = "{% trans 'Okay' %}";
    }
    var button = document.getElementById('last_trick');
    function callback() {
        toggleLastTrick();
        lastTrickButton();
    }
    if(!button) {
        createButton(label, "last_trick", callback);
    }
    else {
        button.innerHTML = label;
    }
}

function toggleLastTrick() {
    if(document.getElementById("last_trick0")) {
        for(var i = 0; i < last_trick.length; i++) {
            var card = document.getElementById("last_trick"+i);
            if(card) {
                card.remove();
            }
        }
    }
    else {
        for(var i = 0; i < last_trick.length; i++) {
            var card = createCard(last_trick[i]);
            card.id = "last_trick"+i;
            card.type = last_trick[i];
            card.style.position.top = "0px";
            card.style.left = i*0.4*w+"px";
            card.style.zIndex = 100;
            field.appendChild(card);
        }
    }
}

function showInitialPlayerCards(data) {
    if(data.skat) {
        removeCardsFromDeck(3);
        let skat = JSON.parse(data.skat);
        addBottomCardToDeck(skat[0]);
        addCardToDeck(skat[1]);
    }
    var player_list = JSON.parse(data.players);
    for(let i = 1; i < 5; ++i) {
        removeCardFrom(i, 100);
    }
    for(let i = 0; i < player_list.length; ++i) {
        var initial_cards = JSON.parse(data[player_list[i]+"_initial_hand"]);
        for(let j = 0; j < initial_cards.length; ++j) {
            addCardTo(players[player_list[i]], 1, initial_cards[j]);
        }
    }
}

function setUpNewRound(new_data, clickCallback) {
    clearStacks();
    if(new_data.active) {
        active = new_data.active;
    }
    last_trick = null;
    clickCallback(new_data);
}

function createNextRoundButton(new_data, clickCallback) {
    last_trick = null;
    deleteButton("last_trick");
    function callback() {
        deleteButton("next-round");
        clearStacks();
        setUpNewRound(new_data, clickCallback);
        removeScoreAlert();
    }
    createButton("Weiter", "next-round", callback);
    let button = document.getElementById("next-round");
    let field_width = document.querySelector('.game-field').offsetWidth;
    let score_alert = document.getElementById("score-alert");
    if(!score_alert) {
        score_alert = document.getElementById("info-alert");
    }
    button.style.right = (field_width - score_alert.offsetWidth - score_alert.offsetLeft) + "px";
    button.style.top = score_alert.offsetTop - button.offsetHeight - 5 + "px";
}

function clearStacksTimeoutCallback() {
    clearStacks();
    lastTrickButton();
}

function clearStacksSafety() {
    if(clearStacksTimeout) {
        clearTimeout(clearStacksTimeout);
        clearStacksTimeout = undefined;
        clearStacksTimeoutCallback();
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

function handleBidGuard(data) {
    let button = document.getElementById("next-round");
    if(button) {
        button.click();
        active = data.active;
    }
    else {
        removeScoreAlert();
    }
}
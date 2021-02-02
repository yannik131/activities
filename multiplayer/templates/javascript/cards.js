{% load static %}

var player1_cards = [];
var player2_cards = [];
var player3_cards = [];
var player4_cards = [];
var player_cards = {1: player1_cards, 2: player2_cards, 3: player3_cards, 4: player4_cards}
var players = {}; //username -> 1-4
var suit_values = {}, value_values = {};
var deck = [];
var trump_suit;
var stacks = [];
var buttons = [];
const field = document.querySelector(".game-field");
var scale, w, h;
var button_row = 0;

function getGridPosition(value, suit) {
    var x, y;
    switch(value) {
        case "rear": return {x: 2, y: 4};
        case "A": x = 0; break;
        case "J": x = 10; break;
        case "Q": x = 11; break;
        case "K": x = 12; break;
        default: x = parseInt(value)-1;
    }
    switch(suit) {
        case "c": y = 0; break;
        case "d": y = 1; break;
        case "h": y = 2; break;
        default: y = 3;
    }
    return {x: x, y: y};
}

function getVs(type) {
    var value, suit;
    if(type.length == 3) {
        value = "10";
        suit = type[2];
    }
    else if(type == "rear") {
        value = "rear";
    }
    else {
        value = type[0];
        suit = type[1];
    }
    return {value: value, suit: suit};
}

function createCard(type, clickable=false) {
    const vs = getVs(type);
    var value = vs.value, suit = vs.suit;
    const position = getGridPosition(value, suit);
    const card = document.createElement("div");
    card.style.background = "url('{% static 'cards.png' %}') no-repeat -" + (position.x*123) + "px -" + (position.y*192)+ "px";
    card.style.width = "123px"
    card.style.height = "192px";
    card.style.position = "absolute";
    card.style.transformOrigin = "top left";
    card.className = "card";
    card.style.transform = "scale("+scale+") ";
    if(clickable) {
        card.style.cursor = "pointer";
        card.onclick = function() {
            cardClicked(value, suit, this);
        }
    }
    return card;
}

function getOffsetForPlayer(player, n) {
    var offset;
    switch(player) {
        case 1: 
            offset = w-field.offsetWidth/n; 
            break;
        case 2: 
            offset = (2*h/3+w*n-field.offsetHeight+h+w)/n;
            break;
        case 3: 
            offset = (1.1*w+w*n-field.offsetWidth)/n; 
            break;
        case 4: 
            offset = (2*h/3+w*n-field.offsetHeight+h+w)/n;
            break;
    }
    if(offset < 0) {
        offset = 0;
    }
    return offset;
}


function getPlayerVariables(player) {
    var rotation;
    var cards;
    switch(player) {
        case 1:
            rotation = 0;
            cards = player1_cards;
            break;
        case 2:
            rotation = 90;
            cards = player2_cards;
            break;
        case 3:
            rotation = 0;
            cards = player3_cards;
            break;
        case 4:
            rotation = -90;
            cards = player4_cards;
            break;
    }
    return {rotation: rotation, cards: cards}
}

function positionCard(player, card, i, n) {
    const offset = getOffsetForPlayer(player, n);
    switch(player) {
        case 1:
            card.style.left = i*w-offset*i+"px";
            card.style.top = field.offsetHeight-h+"px";
            break;
        case 2:
            card.style.top = 2*h/3+w*i-offset*i+"px";
            card.style.left = 1/3*h+"px";
            break;
        case 3:
            card.style.left = w+10+w*i-offset*i+"px";
            card.style.top = -2/3*h+"px";
            break;
        case 4:
            card.style.top = w+h/2+w*i-offset*i+"px";
            card.style.right = -2/3*h-(123-h)+"px";
            break;
    }
}

function addCardTo(player, n, type) {
    var new_cards = [];
    const vars = getPlayerVariables(player);
    var card;
    for(var i = 0; i < n; i++) {
        if(type) {
            card = createCard(type, player == 1);
            card.id = type;
        }
        else {
            card = createCard("rear");
        }
        card.style.transform += "rotate("+vars.rotation+"deg)";
        vars.cards.push(card);
        new_cards.push(card);
    }
    updateCardsFor(player);
    for(var i = 0; i < new_cards.length; i++) {
        field.appendChild(new_cards[i]);
    }
}

function removePlayerCard(card) {
    card.remove();
    player1_cards.splice(player1_cards.indexOf(card), 1);
    updateCardsFor(1);
}

function defineSortValuesDefault() {
    var suits = ["d", "h", "s", "c"];
    var count = 100;
    for(var i = 0; i < suits.length; i++) {
        suit_values[suits[i]] = count;
        count += 100;
    }
    var values = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"];
    for(var i = 0; i < values.length; i++) {
        value_values[values[i]] = i;
    }
}

function getCardSortValueDefault(type) {
    const vs = getVs(type);
    const value = vs.value, suit = vs.suit;
    return suit_values[suit] + value_values[value];
}

function updateCardsFor(player) {
    const vars = getPlayerVariables(player);
    if(vars.cards.length && vars.cards[0].id) {
        vars.cards.sort(function(a, b) {
            return getCardSortValue(b.id)-getCardSortValue(a.id);
        });
    }
    for(var i = 0; i < vars.cards.length; i++) {
        const card = vars.cards[i];
        card.style.zIndex = i;
        positionCard(player, card, i, vars.cards.length);
    }
}

function removeCardFrom(player, n, type) {
    const vars = getPlayerVariables(player);
    if(type) {
        console.log("delete: ", type);
    }
    for(var i = 0; (i < n && vars.cards.length > 0) || type; i++) {
        if(type) {
            console.log("checking: ", vars.cards[i].id);
            if(vars.cards[i].id == type) {
                console.log("found: ", vars.cards[i].id);
                vars.cards[i].remove();
                vars.cards.splice(i, 1);
                for(var j = 0; j < vars.cards.length; j++) {
                    console.log(vars.cards[j].id);
                }
                break;
            }
            else if(i == vars.cards.length-1) {
                break;
            }
        }
        else {
            const card = vars.cards.pop();
            card.remove();
        }   
    }
    updateCardsFor(player);
}

function addBottomCardToDeck(type) {
    var card = createCard(type);
    card.style.top = -10-1/3*h+"px";
    card.style.left = 0+"px";
    card.id = "deck-0";
    card.zIndex = 0;
    field.appendChild(card);
    deck.splice(0, 0, card);
}

function addCardsToDeck(n, bottom_card) {
    if(bottom_card)
        addBottomCardToDeck(bottom_card);
    for(var i = 0; i < n; i++) {
        var card = createCard("rear");
        card.style.left = 0+"px";
        card.zIndex = i+1;
        deck.push(card);
    }
    updateDeck();
    for(var i = 0; i < 10 && i < deck.length-1; i++) {
        field.appendChild(deck[i+1]);
    }
}

function updateDeck() {
    var n = 10; //number of cards above the bottom card
    if(deck.length < 11) {
        n = deck.length-1;
    }
    for(var i = 0; i < n; i++) {
        const card = deck[i+1];
        card.style.top = -h+(1/3*h)/n*(n-i)+"px";
    }
}

function removeCardsFromDeck(n) {
    while(deck.length > 0 && n > 0) {
        const card = deck.pop();
        card.remove();
        n -= 1;
    }
    updateDeck();
}

function addStack(type) {
    const n = stacks.length;
    const padding = {x: 10, y: h/4};
    const top_left = {x: 1/3*h+10, y: 2/3*h+10};
    const row = Math.floor(n/3);
    const column = n % 3;
    const card = createCard(type);
    card.style.left = top_left.x+column*(w+padding.x)+"px";
    card.style.top = top_left.y+(h+padding.y)*row+"px";
    card.id = type;
    stacks.push([card]);
    field.appendChild(card);
}

function beatStack(n, type, right) {
    const stack = stacks[n-1];
    const card = createCard(type);
    
    if(right) {
        card.style.top = stack[stack.length-1].style.top;
        card.style.left = parseInt(stack[stack.length-1].style.left)+0.4*w+"px";
    }
    else {
        card.style.left = stack[0].style.left;
        card.style.top = parseInt(stack[stack.length-1].style.top)+0.8*h/4+"px";
    }
    
    card.id = type;
    stack.push(card);
    field.appendChild(card);
}

function refreshStacks(new_stacks, right) {
    for(var i = 0; i < new_stacks.length; i++) {
        if(typeof stacks[i] == "undefined") {
            addStack(new_stacks[i][0]);
        }
        for(var j = 1; j < new_stacks[i].length; j++) {
            if(typeof stacks[i][j] == "undefined") {
                beatStack(i+1, new_stacks[i][j], right);
            }
        }
    }
}

function getConvertedStack() {
    var converted = [];
    for(var i = 0; i < stacks.length; i++) {
        converted[i] = [];
        for(var j = 0; j < stacks[i].length; j++) {
            converted[i][j] = stacks[i][j].id;
        }
    }
    return converted;
}

function getConvertedHand() {
    var converted = [];
    for(var i = 0; i < player1_cards.length; i++) {
        converted.push(player1_cards[i].id);
    }
    return converted;
}

function createButton(text, id, callback, color) {
    if(document.getElementById(id)) {
        return;
    }
    var button = document.createElement("button");
    button.type = "button";
    if(field.offsetWidth < 600) {
        button.style.fontSize = "14pt";
    }
    else {
        button.style.fontSize = "24pt";
    }
    button.className = "game-button";
    button.innerHTML = text;
    button.onclick = callback;
    button.style.right = (buttons.length == 0? 0 : field.offsetWidth-buttons[buttons.length-1].offsetLeft+5) + "px";
    field.appendChild(button);
    if(button.offsetLeft < 0) {
        ++button_row;
        button.style.right = "0px";
    }
    button.style.top = "0px";
    if(buttons.length) {
        if(button_row == 0) {
            button.style.top = buttons[buttons.length-1].style.top;
        }
        else {
            button.style.top = button_row*(10+buttons[buttons.length-1].offsetHeight)+"px";
        }
    }
    
    button.id = id;
    if(color) {
        button.style.color = color;
    }
    
    buttons.push(button);
}

function deleteButton(id) {
    button = document.getElementById(id);
    if(!button) {
        return;
    }
    buttons.splice(buttons.indexOf(button), 1);
    button.remove();
    if(buttons.length > 0) {
        buttons[0].style.right = "0px";
        for(var i = 1; i < buttons.length; i++) {
            buttons[i].style.right = parseFloat(buttons[i-1].style.left)+"px";
        }
    }
}

function clearButtons() {
    for(var i = 0; i < buttons.length; i++) {
        buttons[i].remove();
    }
    buttons = [];
    button_row = 0;
}

function createInfoAlert(info, timeout) {
    if(document.getElementById("info-alert")) {
        return;
    }
    info = info.replace(/(?:\r\n|\r|\n)/g, '<br>');
    var info_alert = document.createElement("div");
    info_alert.className = "info-alert";
    info_alert.innerHTML = info;
    info_alert.id = "info-alert";
    if(timeout) {
        setTimeout(function() {
            document.getElementById("info-alert").remove();
        }, timeout);
    }
    else {
        var button = document.createElement("button");
        button.type = "button";
        button.onclick = function() {
            document.getElementById("info-alert").remove();
        }
        button.className = "info-alert-button";
        if(window.screen.width < 768) {
            button.style.fontSize = "10pt";
        }
        else {
            button.style.fontSize = "18pt";
        }
        button.innerHTML = "Okay";
        info_alert.appendChild(button);
    }
    field.appendChild(info_alert);
}

function next(el, arr) {
    return arr[((arr.indexOf(el)+1)%arr.length+arr.length)%arr.length];
}

function before(el, arr) {
    return arr[((arr.indexOf(el)-1)%arr.length+arr.length)%arr.length];
}

function getPlayerCards(value, suit, except_value) {
    var cards = [];
    for(var i = 0; i < player1_cards.length; i++) {
        const vs = getVs(player1_cards[i].id);
        if(vs.value == value || vs.suit == suit) {
            if(vs.value == except_value) {
                continue;
            }
            cards.push(vs);
        }
    }
    return cards;
}

function playerHandContains(value, suit, except_value) {
    return getPlayerCards(value, suit, except_value).length != 0;
}

function clearStacks() {
    for(var i = 0; i < stacks.length; i++) {
        for(var j = 0; j < stacks[i].length; j++) {
            stacks[i][j].remove();
        }
    }
    stacks = [];
}

function positionPlayers(player_list) {
    //fills players[username] in the right order
    players[this_user] = 1;
    var current = next(this_user, player_list);
    for(var i = 2; current != this_user; i++) {
        players[current] = i;
        current = next(current, player_list);
    }
}

function changeInfoFor(username, info, important) {
    var player = players[username];
    var player_info = document.getElementById("player"+player);
    player_info.innerHTML = (
        "<a href='/account/detail/" +
        username + 
        "/'>" +
        username +
        "</a> " +
        info
    );
    if(important) {
        player_info.style.fontWeight = "bold";
        player_info.style.color = "red";
    }
    else {
        player_info.style.fontWeight = "normal";
        player_info.style.color = "white";
    }
}

function displayCards(data, player_list, except) {
    for(var i = 0; i < player_list.length; i++) {
        var username = player_list[i];
        if(username == except) {
            continue;
        }
        var player_index = players[username];
        var hand = JSON.parse(data[username]);
        if(player_index == 1) {
            for(var j = 0; j < hand.length; j++) {
                addCardTo(player_index, 1, hand[j]);
            }
        }
        else {
            addCardTo(player_index, hand.length);
        }
    }
}

function resize() {
    /*To calculate the scale, we substract constant paddings which are
unaffected by the scale from the divs total width/height and
divide the result by the space requirements of the cards on the
durak game field. The smaller value is then used to prevent 
overlap of cards.*/
    var scale1 = (field.offsetWidth-40)/(123*3+192*2/3);
    var scale2 = (field.offsetHeight-10)/(192*3+192*2/3+192/4*2);
    scale = scale1 < scale2? scale1 : scale2;

    w = 123*scale;
    h = 192*scale;
    //TODO: MAYBE resize?
}

resize();
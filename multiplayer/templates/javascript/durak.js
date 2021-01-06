{% load static %}

var player1_cards = [];
var player2_cards = [];
var player3_cards = [];
var player4_cards = [];
var scale = 1;
const w = 123*scale;
const h = 192*scale;
const field = document.querySelector(".game-field");

function displayPlayers(n) {
    for(var i = 0; i < 4; i++) {
        const player = document.createElement("div");
        player.className = "player" + (i+1);
        document.querySelector(".game-field").appendChild(player);
    }
}

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

function createCard(type) {
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
    const position = getGridPosition(value, suit);
    const card = document.createElement("div");
    card.style.background = "url('{% static 'output.png' %}') no-repeat -" + (position.x*123) + "px -" + (position.y*192)+ "px";
    card.style.width = "123px"
    card.style.height = "192px";
    card.style.position = "absolute";
    card.style.transformOrigin = "top left";
    card.className = "card";
    return card;
}

function getOffsetForPlayer(player, n) {
    var offset;
    switch(player) {
        case 1: 
            offset = w-field.offsetWidth/n; break;
        case 2: 
            offset = (2*h/3+w*n-field.offsetHeight+h+w)/n;
            break;
        case 3: 
            offset = (1.1*w+w*n-field.offsetWidth)/n; break;
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
            card.style.left = 1.1*w+w*i-offset*i+"px";
            card.style.top = -2/3*h+"px";
            break;
        case 4:
            card.style.top = w+h/2+w*i-offset*i+"px";
            card.style.right = -2/3*h-(123-h)+"px";
            break;
    }
}

function addCardTo(player, type) {
    var card;
    if(type) {
        card = createCard(type);
    }
    else {
        card = createCard("rear");
    }
    const vars = getPlayerVariables(player);
    card.style.transform = "rotate("+vars.rotation+"deg) scale("+scale+")";
    vars.cards.push(card);
    for(var i = 0; i < vars.cards.length; i++) {
        const card = vars.cards[i];
        positionCard(player, card, i, vars.cards.length);
    }
    field.appendChild(card);
}

for(var i = 0; i < 10; i++) {
    addCardTo(1, "Ac");
}

for(var i = 0; i < 6; i++) {
    addCardTo(2);
}

for(var i = 0; i < 6; i++) {
    addCardTo(3);
}

for(var i = 0; i < 6; i++) {
    addCardTo(4);
}
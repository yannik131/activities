{% load static %}

var player1_cards = [];
var player2_cards = [];
var player3_cards = [];
var player4_cards = [];

function displayPlayers(n) {
    for(var i = 0; i < n; i++) {
        const player = document.createElement("div");
        player.className = "player" + (i+1);
        document.querySelector(".game-field").appendChild(player);
    }
}

function calculateOffset(n, player) {
    const element = document.querySelector(player);
    var length;
    if(player === ".player1" || player === ".player3") {
        length = parseInt(getComputedStyle(element).width, 10);
    }
    else {
        length = parseInt(getComputedStyle(element).height, 10);
    }
    const offset = length/n;
    if(offset < 123) {
        return offset;
    }
    return 123;
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

function setPosition(player, element, value) {
    switch(player) {
        case ".player1":
        case ".player3":
            element.style.left = value + "px";
            break;
        default:
            element.style.top = value + "px";
    }
}

function createCard(value, suit) {
    const position = getGridPosition(value, suit);
    const card = document.createElement("div");
    card.style.background = "url('{% static 'output.png' %}') no-repeat -" + (position.x*123) + "px -" + (position.y*192)+ "px";
    card.style.width = "123px"
    card.style.height = "192px";
    card.style.position = "absolute";
    card.className = "card";
    return card;
}

function addCard(value, suit) {
    const card = createCard(value, suit);
    card.style.cursor = "pointer";
    card.id = player1_cards.length;
    card.onclick = function() {
        player1_cards.splice(parseInt(this.id), 1);
        this.parentNode.removeChild(this);
        const offset = calculateOffset(player1_cards.length, ".player1");
        for(var j = 0; j < player1_cards.length; j++) {
            player1_cards[j].style.left = j*offset + "px";
            player1_cards[j].id = j;
        }
    }

    player1_cards.push(card);
    document.querySelector(".player1").appendChild(card);
    const offset = calculateOffset(player1_cards.length, ".player1");
    for(var i = 0; i < player1_cards.length; i++) {
        setPosition(".player1", player1_cards[i], i*offset);
    }
}

function getPlayerVariables(player) {
    var rotation;
    var cards;
    switch(player) {
        case ".player2":
            rotation = 90;
            cards = player2_cards;
            break;
        case ".player3":
            rotation = 180;
            cards = player3_cards;
            break;
        case ".player4":
            rotation = 270;
            cards = player4_cards;
            break;
    }
    var player = document.querySelector(player);
    return {rotation: rotation, cards: cards, player: player}
}

function addCardsTo(player, n) {
    const vars = getPlayerVariables(player);
    const offset = calculateOffset(n+vars.cards.length, player);
    for(var i = 0; i < n; i++) {
        const card = createCard("rear");
        card.style.transform = "rotate(" + vars.rotation + "deg)";
        card.id = i;
        setPosition(player, card, i*offset);
        vars.player.appendChild(card);
        vars.cards.push(card);
    }
}

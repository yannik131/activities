{% load static %}
{% load i18n %}

var player_cards = {1: [], 2: [], 3: [], 4: [],
                    5: [], 6: [], 7: [], 8: [],
                    9: [], 10: []};
var player1_cards = player_cards[1];
var players = {}; //username -> 1-10
var suit_values = {}, value_values = {};
var deck = [];
var stacks = [];
var buttons = [];
let field;
var scale, w, h;
var button_row = 0;
var summary;
var info_timeout;
var beat_right = false;
var is_poker = false;

const default_rotation = {1: 0, 2: 90, 3: 0, 4: -90};
const poker_rotation = {1: 0, 2: 90, 3: 90, 4: 0, 5: 0, 6: 0, 7: -90, 8: -90, 9: -90, 10: 0};

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

function getPlayerVariables(player) {
    if(is_poker) {
        return {rotation: poker_rotation[player], cards: player_cards[player]}
    }
    return {rotation: default_rotation[player], cards: player_cards[player]}
}

function getOffsetForPlayer(player, n) {
    var offset;
    if(is_poker) {
        const p1 = 20, p2 = 30;
        switch(player) {
            case 1:
                offset = w-((field.offsetWidth-1/3*h-p1)/2-p2)/n;
                break;
            case 2:
            case 3:
                offset = w-((field.offsetHeight-1/3*h-2*p1-h)/2-p2)/n;
                break;
            case 4:
            case 5:
            case 6:
                offset = w-(field.offsetWidth/3-p2)/(n+1);
                break;
            case 7:
            case 8:
            case 9:
                offset = w-((field.offsetHeight-h/3-p1)/3-p2)/n;
            break;
            case 10:
                offset = w-((field.offsetWidth-h/3-p1)/2-p2)/n;
                break;
        }
    }
    else {
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
        }
    }
    if(offset < 0) {
        offset = 0;
    }
    return offset;
}

function positionCard(player, card, i, n) {
    const offset = getOffsetForPlayer(player, n);
    if(is_poker) {
        const p1 = 20;
        const left_box_height = field.offsetHeight-h-2*p1-1/3*h;
        const right_box_height = field.offsetHeight-h/3-p1;
        const bottom_box_width = field.offsetWidth-h/3-p1;
        switch(player) {
            case 1:
                card.style.left = i*w-offset*i+"px";
                card.style.top = field.offsetHeight-h+"px";
                break;
            case 2:
                card.style.top = field.offsetHeight-h-p1-w-w*i+i*offset+"px";
                card.style.left = 1/3*h+"px";
                break;
            case 3:
                card.style.top = field.offsetHeight-h-p1-left_box_height/2-w-w*i+i*offset+"px";
                card.style.left = 1/3*h+"px";
                break;
            case 4:
            case 5:
            case 6:
                card.style.top = -2/3*h+"px";
                card.style.left = (player-4)*field.offsetWidth/3+w*i-i*offset+"px";
                break;
            case 7:
            case 8:
            case 9:
                card.style.right = -2/3*h-(123-h)+"px";
                card.style.top = h/3+p1+(player-6)*(right_box_height/3)-w*i+i*offset+"px";
                break;
            case 10:
                card.style.top = field.offsetHeight-1/3*h+"px";
                card.style.left = bottom_box_width-w-w*i+i*offset+"px";
                break;
        }
    }
    else {
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
}

function addCardTo(player, n, type, not_clickable) {
    var new_cards = [];
    const vars = getPlayerVariables(player);
    var card;
    for(var i = 0; i < n; i++) {
        if(type) {
            card = createCard(type, player == 1 && !not_clickable);
            card.id = type;
        }
        else {
            card = createCard("rear");
            card.id = "rear";
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
    for(var i = 0; (i < n && vars.cards.length > 0) || type; i++) {
        if(type) {
            if(vars.cards[i].id == type) {
                vars.cards[i].remove();
                vars.cards.splice(i, 1);
                break;
            }
            else if(i == vars.cards.length-1) {
                break;
            }
        }
        else {
            const card = vars.cards.splice(0, 1)[0];
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
    card.type = type;
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

function addStack(type, row, column) {
    const n = stacks.length;
    const padding = {x: 10, y: h/4};
    const top_left = {x: 1/3*h+10, y: 2/3*h+10};
    if(!row) {
        row = Math.floor(n/3);
        column = n % 3;
    }
    const card = createCard(type);
    card.style.left = top_left.x+column*(w+padding.x)+"px";
    card.style.top = top_left.y+(h+padding.y)*row+"px";
    card.id = type;
    stacks.push([card]);
    field.appendChild(card);
}

function beatStack(n, type) {
    const stack = stacks[n-1];
    const card = createCard(type);
    
    if(beat_right) {
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

function refreshStacks(new_stacks) {
    if(new_stacks.length < stacks.length) {
        while(stacks.length > new_stacks.length) {
            for(var i = 0; i < stacks[stacks.length-1].length; i++) {
                stacks[stacks.length-1][i].remove();
            }
            stacks.splice(stacks.length-1, 1);
        }
    }
    for(var i = 0; i < new_stacks.length; i++) {
        if(typeof stacks[i] == "undefined") {
            addStack(new_stacks[i][0]);
        }
        for(var j = 1; j < new_stacks[i].length; j++) {
            if(typeof stacks[i][j] == "undefined") {
                beatStack(i+1, new_stacks[i][j]);
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
    button.style.fontWeight = "bold";
    button.className = "game-button";
    button.innerHTML = text;
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
    button.onclick = callback;
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

function clearButtons(callback) {
    for(var i = 0; i < buttons.length; i++) {
        buttons[i].remove();
    }
    buttons = [];
    button_row = 0;
    if(callback) {
        callback();
    }
}

function createYesNoAlert(info, zIndex, callback) {
    var old_alert = document.getElementById("yesno-alert");
    if(old_alert) {
        old_alert.remove();
        return;
    }
    info = info.replace(/(?:\r\n|\r|\n)/g, '<br>');
    var info_alert = document.createElement("div");
    info_alert.className = "info-alert";
    info_alert.innerHTML = info + "<br>";
    info_alert.style.zIndex = zIndex;
    info_alert.style.border = "5px solid red";
    info_alert.id = "yesno-alert";
    var button = createInfoButton("{% trans 'Ja' %}", callback, info_alert);
    button.style.marginRight = "5px";
    var button = createInfoButton("{% trans 'Nein' %}", null, info_alert);
    button.style.marginLeft = "5px";
    field.appendChild(info_alert);
}

function createInfoAlert(info, timeout, no_button) {
    const old = document.getElementById("info-alert");
    if(old) {
        var button = document.querySelector('.info-alert-button');
        if(button) {
            button.dispatchEvent(new Event('click'));
        }
        old.remove();
        if(info_timeout) {
            clearTimeout(info_timeout);
        }
    }
    info = info.replace(/(?:\r\n|\r|\n)/g, '<br>');
    var info_alert = document.createElement("div");
    info_alert.className = "info-alert";
    info_alert.innerHTML = info;
    info_alert.id = "info-alert";
    if(timeout) {
        info_alert.style.zIndex = 1;
        info_alert.style.border = "1px solid gray";
        info_timeout = setTimeout(function() {
            document.getElementById("info-alert").remove();
        }, timeout);
    }
    else if(!no_button) {
        createInfoButton("Okay", null, info_alert);
    }
    field.appendChild(info_alert);
    return info_alert;
}

function createInputAlert(message, callback) {
    var info_alert = createInfoAlert(message, null, true);
    var input = document.createElement('input');
    input.addEventListener('keyup', function(event) {
        if(event.which == 13) {
            if(callback(input.value)) {
                input.parentElement.remove();
            }
        }
    });
    input.type = 'number';
    info_alert.appendChild(document.createElement('br'));
    info_alert.appendChild(input);
    createInfoButton('{% trans 'Senden' %}', function() {
        if(callback(input.value)) {
            input.parentElement.remove();
        }
    }, info_alert, true);
    createInfoButton('{% trans 'Abbrechen' %}', function() {
        input.parentElement.remove();
    }, info_alert, true);
}

function createInfoButton(text, button_callback, info_alert, no_auto_remove) {
    var button = document.createElement("button");
    button.type = "button";
    button.onclick = function() {
        if(!no_auto_remove) {
            info_alert.remove();
        }
        if(button_callback) {
            button_callback();
        }
    }
    button.className = "info-alert-button";
    if(window.screen.width < 768) {
        button.style.fontSize = "10pt";
    }
    else {
        button.style.fontSize = "18pt";
    }
    button.innerHTML = text;
    info_alert.appendChild(document.createElement('br'));
    info_alert.appendChild(button);
    return button;
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

function clearStacks(keep_last_trick) {
    for(var i = 0; i < stacks.length; i++) {
        for(var j = 0; j < stacks[i].length; j++) {
            stacks[i][j].remove();
        }
    }
    stacks = [];
    if(keep_last_trick) {
        return;
    }
    var card = document.getElementById("last_trick0");
    if(card) {
        deleteButton("last_trick");
    }
    for(var i = 1; card; i++) {
        card.remove();
        card = document.getElementById("last_trick"+i);
    }
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
    var info_div = document.getElementById("info-div-"+username);
    const content = (
        "<a href='/account/detail/"+username+"/'>"+
            username+
        "</a>"+
        "<div class='text'>"+
            info+
        "</div>"
    );
    if(info_div) {
        info_div.remove();
    }
    info_div = document.createElement('div');
    info_div.className = 'info-div';
    info_div.id = "info-div-"+username;
    info_div.innerHTML = content;
    player_info.appendChild(info_div);
    const rotation = getPlayerVariables(player).rotation;
    switch(rotation) {
        case 90:
            info_div.style.transform = 'rotate(90deg)';
            info_div.style.transformOrigin = 'bottom left';
            player_info.style.height = field.offsetHeight+"px";
            info_div.style.top = (field.offsetHeight-80-parseInt(window.getComputedStyle(info_div).width))/2+"px";
            break;
        case -90:
            info_div.style.transform = 'rotate(-270deg)';
            info_div.style.transformOrigin = 'bottom left';
            player_info.style.height = field.offsetHeight+"px";
            info_div.style.top = (field.offsetHeight-80-parseInt(window.getComputedStyle(info_div).width))/2+"px";
            break;
        default:
            info_div.style.left = (field.offsetWidth-parseInt(window.getComputedStyle(info_div).width))/2+"px";
    }
    if(important) {
        info_div.style.fontWeight = "bold";
        info_div.style.color = "red";
    }
    else {
        info_div.style.fontWeight = "normal";
        info_div.style.color = "white";
    }
    info_div.innerHTML = content;
}

function displayText(message) {
    var text = document.getElementById('game-text');
    if(!text) {
        text = document.createElement('div');
        text.id = "game-text";
        text.style.width = w+"px";
        text.style.height = h+"px";
        const padding = {x: 10, y: h/4};
        const top_left = {x: 1/3*h+10, y: 2/3*h+10};
        text.style.left = top_left.x+2*(w+padding.x)+"px";
        text.style.top = top_left.y+(h+padding.y)*1+"px";
        field.appendChild(text);
    }
    message = message.replace(/(?:\r\n|\r|\n)/g, '<br>');
    text.innerHTML = message;
}

function changePokerInfoFor(player, username, info) {
    var info_div = document.getElementById("info-div-"+username);
    var created = false;
    if(!info_div) {
        info_div = document.createElement('div');
        var length = w*2-getOffsetForPlayer(player, 2);
        info_div.style.width = length+"px";
        info_div.className = 'info-div';
        info_div.id = "info-div-"+username;
        created = true;
    }
    var player_info;
    switch(player) {
        case 1:
        case 10:
            player_info = document.getElementById('player1');
            info_div.style.left = player_cards[player][player == 1? 0 : 1].style.left;
            break;
        case 2:
        case 3:
            player_info = document.getElementById('player2');
            info_div.style.top = parseInt(player_cards[player][1].style.top)-40+"px";
            info_div.style.transformOrigin = "bottom left";
            info_div.style.transform = "rotate(90deg)";
            break;
        case 4:
        case 5:
        case 6:
            player_info = document.getElementById('player3');
            
            info_div.style.left = player_cards[player][0].style.left;
            break;
        case 7:
        case 8:
        case 9:
            player_info = document.getElementById('player4');
            info_div.style.transformOrigin = "bottom left";
            info_div.style.transform = "rotate(-270deg)";
            info_div.style.top = parseInt(player_cards[player][1].style.top)-110+"px";
            break;
    }
   info_div.innerHTML = (
    "<a href='/account/detail/"+username+"/'>"+
        username+
    "</a>"+(info != undefined? (
    ":<span class='text'>"+
        info+
    "</span>") : "")
    );
    if(created) {
        player_info.appendChild(info_div);
    }
    
    return info_div;
}

function displayCards(data, player_list, except) {
    for(var i = 0; i < player_list.length; i++) {
        var username = player_list[i];
        if(except && except.indexOf(username) != -1) {
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

function showScore(toggle) {
    var info_alert = document.getElementById("score-alert");
    if(info_alert) {
        if(toggle) {
            info_alert.remove();
        }
        return;
    }
    else if(summary) {
        info_alert = createInfoAlert(summary);
    }
    else {
       info_alert = createInfoAlert("{% trans 'Es wurde noch kein Spiel beendet.' %}");
    }
    info_alert.id = 'score-alert';
}

function game_resize() {
    /*To calculate the scale, we substract constant paddings which are
unaffected by the scale from the divs total width/height and
divide the result by the space requirements of the cards on the
durak game field. The smaller value is then used to prevent 
overlap of cards.*/
    var scale1 = (field.offsetWidth-40)/(123*3+192*2/3);
    var scale2 = (field.offsetHeight-10)/(192*3+192*2/3+192/4*2);
    scale = Math.min(scale1, scale2);

    w = 123*scale;
    h = 192*scale;
    //update player cards
    for(var i = 1; i < 11; i++) {
        var cards = player_cards[i];
        var types = [];
        var hidden = cards.length && cards[0].style.display == 'none';
        while(cards.length) {
            var card = cards.pop();
            card.remove();
            types.push(card.id);
        }
        while(types.length) {
            var type = types.pop();
            addCardTo(i, 1, type != "rear"? type : null, is_poker);
        }
        if(hidden) {
            hideCardsOf(i);
        }
    }
    //update deck
    var type = null;
    var n = deck.length;
    while(deck.length) {
        var card = deck.pop();
        card.remove();
        if(card.type) {
            type = card.type;
        }
    }
    if(type) { //durak
        addCardsToDeck(n-1, type);
    }
    else { //not durak
        if(n) { 
            addCardsToDeck(n);
        }
    }
    //update stacks
    var stack_copy = getConvertedStack();
    clearStacks(true);
    refreshStacks(stack_copy);
    //update last trick
    if(document.getElementById('last_trick0')) {
        toggleLastTrick();
        toggleLastTrick();
    }
    //update buttons
    var buttons_copy = [];
    while(buttons.length) {
        var button = buttons.pop();
        button.remove();
        buttons_copy.splice(0, 0, button);
    }
    button_row = 0;
    for(var i = 0; i <buttons_copy.length; i++) {
        var button = buttons_copy[i];
        createButton(button.innerText, button.id, button.onclick);
    }
    //update info in poker
    if(is_poker) {
        const info_divs = document.getElementsByClassName('info-div');
        for(var i = 0; i < info_divs.length; i++) {
            const username = info_divs[i].id.split('-')[2];
            var info = info_divs[i].getElementsByClassName('text')[0];
            var className = info_divs[i].className;
            info_divs[i].remove();
            info = changePokerInfoFor(players[username], username, info? info.innerText : undefined);
            info.className = className;
        }
        var text = document.getElementById('game-text');
        if(text) {
            const message = text.innerHTML;
            text.remove();
            displayText(message);
        }
    }
    else {
        const info_divs = document.getElementsByClassName('info-div');
        for(var i = 0; i < info_divs.length; i++) {
            const username = info_divs[i].id.split('-')[2];
            var info = info_divs[i].innerText.split(username)[1];
            const important = info_divs[i].style.color == 'red';
            info_divs[i].remove();
            changeInfoFor(username, info, important);
        }
    }
}

function leaveGame() {
    createYesNoAlert(
        "{% trans 'Verlassen Sie das Spiel bitte nur, wenn Sie es auch später nicht mehr fortführen wollen. Spiel verlassen und dadurch zurücksetzen?' %}", 
        2, 
        function() { 
            location.href = "{% url 'multiplayer:leave_match' match.activity.name match.id %}";
        }
    );
}

window.addEventListener('resize', game_resize);

if(window.document.documentMode) {
    alert("{% trans 'Internet Explorer wird nicht unterstützt!' %}");
}

window.addEventListener('load', function() {
    field = document.querySelector(".game-field");
    game_resize();
});
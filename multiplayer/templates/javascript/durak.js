var game_mode;
var this_user = '{{ user }}';
var played_cards = [];
var player_list;
var selected_card;

function processMultiplayerData(data) {
    switch(data.action) {
        case "load_data":
            loadGameField(data);
            break;
        case "play":
            handleMove(data);
            break;
        case "new_round":
            setupNewRound(data);
            break;
        case "transfer":
            handleTransfer(data);
    }
}

function loadGameField(data) {
    var deck = JSON.parse(data.deck);
    player_list = JSON.parse(data.players);
    determineGameMode(data.attacking, data.defending);
    addCardsToDeck(deck.length-1, deck[deck.length-1]);
    positionPlayers(data.attacking, data.defending);
    for(var i = 0; i < player_list.length; i++) {
        var username = player_list[i];
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
    var stacks = JSON.parse(data.stacks);
    refreshStacks(stacks);
    updateButtons();
}

function positionPlayers(attacking, defending) {
    var my_index = player_list.indexOf(this_user);
    var added_names = 0;
    while(added_names != player_list.length) {
        var username = player_list[my_index];
        var player_info = document.getElementById("player"+(added_names+1));
        player_info.innerHTML = (
            "<a href='/account/detail/" +
            username + 
            "/'>" +
            username +
            "</a>"
        );
        if(username == attacking) {
            player_info.innerHTML += " (ANGREIFER)";
        }
        else if(username == defending) {
            player_info.innerHTML += " (VERTEIDIGER)";
        }
        players[username] = added_names+1;
        my_index += 1;
        if(my_index == player_list.length)
            my_index = 0;
        added_names += 1;
    }
}

function determineGameMode(attacking, defending) {
    if(this_user == attacking) {
        game_mode = "attacking";
    }
    else if(this_user == defending) {
        game_mode = "defending";
    }
    else {
        if(this_user == next(data.defending, player_list)) {
            game_mode = "helping";
        }
        else {
            game_mode = "none";
        }
    }
}

function take() {
    sendAction("take");
}

function done() {
    sendAction("done");
    deleteButton("done");
}

function handleMove(data) {
    if(data.username == this_user) {
        return;
    }
    var player = players[data.username];
    removeCardFrom(player, data.n);
    var new_stacks = JSON.parse(data.stacks);
    refreshStacks(new_stacks);
    updateButtons();
}

function beatSingleCard(targets, card) {
    played_cards.push(card);
    beatStack(targets[0], card.id);
    removePlayerCard(card);
    sendMove();
}

function clearStackCallbacks() {
    for(var k = 0; k < stacks.length; k++) {
        stacks[k][0].onclick = null;
    }
}

function beatMultipleCards(targets, card) {
    card.style.top = (parseFloat(card.style.top)-10)+"px";
    for(var i = 0; i < targets.length; i++) {
        var t = targets[i];
        stacks[t][0].cursor = "pointer";
        stacks[t][0].onclick = function() {
            var j = 0;
            while(stacks[j][0].id != this.id) {
                j++;
            }
            beatStack(j+1, card.id);
            played_cards.push(card);
            removePlayerCard(card);
            game_mode = "defending";
            clearStackCallbacks();
        }
    }
    game_mode = "none";
}

function handlePlayerMove(value, suit, card) {
    switch(game_mode) {
        case "none":
            return;
        case "defending":
            var targets = stackTargetsFor(value, suit);
            var transfer_possible = transferPossible(value);
            if(transfer_possible && targets.length == 0) {
                //only transfer possible
                played_cards.push(card);
                removePlayerCard(card);
                addStack(card.id);
                if(cardsContain(value)) {
                    createButton("Fertig", "done", sendMove);
                }
                else {
                    sendMove(extra="transfer");
                }
            }
            else if(transfer_possible && targets.length > 0) {
                beatMultipleCards(targets, card);
                createButton("Schieben", "transfer", function() {
                    played_cards.push(card);
                    addStack(card.id);
                    removePlayerCard(card);
                    clearStackCallbacks();
                    if(!cardsContain(value)) {
                        sendMove("transfer");
                    }
                    else {
                        createButton("Fertig", "done", sendMove);
                        deleteButton("transfer");
                    }
                    game_mode = "defending";
                });
            }
            else if(targets.length == 1) {
                beatSingleCard(targets, card);
            }
            else if(targets.length > 1) {
                beatMultipleCards(targets, card);
            }
            else {
                return;
            }
            break;
        case "helping":
        case "attacking":
            var possible_move = stacks.length == 0;
            outer_loop:
            for(var i = 0; i < stacks.length; i++) {
                for(var j = 0; j < stacks[i].length; j++) {
                    const vs = getValueAndSuitFrom(stacks[i][j].id);
                    if(value == vs.value) {
                        possible_move = true;
                        break outer_loop;
                    }
                }
            }
            if(!possible_move) {
                return;
            }
            played_cards.push(card);
            addStack(card.id);
            removePlayerCard(card);
            if(cardsContain(value)) {
                createButton("Fertig", "done", sendMove);
            }
            else {
                sendMove();
            }
            break;
    }
    updateButtons();
}

function allDefended() {
    for(var i = 0; i < stacks.length; i++) {
        if(stacks[i].length != 2) {
            return false;
        }
    }
    return true;
}

function updateButtons() {
    const defended = allDefended();
    //take button
    if(game_mode == "defending" && !defended) {
        createButton("Schlucken", "take", take);
    }
    else {
        deleteButton("take");
    }
    
    //done button
    if(stacks.length > 0) {
        if(game_mode == "attacking" || game_mode == "helping") {
            createButton("Fertig", "done", done);
        }
        else if(game_mode == "defending" && defended) {
            sendAction("done");
        }
    }
    
}

function stackTargetsFor(value, suit) {
    var targets = [];
    for(var i = 0; i < stacks.length; i++) {
        if(stacks[i].length == 1) {
            const vs = getValueAndSuitFrom(stacks[i][0].id);
            const bigger = value_values[value] > value_values[vs.value];
            if(bigger && suit == vs.suit || 
                (suit == trump_vs.suit && (vs.suit != trump_vs.suit || bigger))) {
                targets.push(i+1);
            }
        }
    }
    return targets;
}

function transferPossible(value) {
    var left_username = next(this_user, player_list);
    var left_count = player_cards[players[left_username]].length;
    if(left_count < stacks.length+1) {
        return false;
    }
    for(var i = 0; i < stacks.length; i++) {
        if(stacks[i].length > 1 ||
            getValueAndSuitFrom(stacks[i][0].id).value != value) {
            return false;
        }
    }
    return true;
}

function cardClicked(value, suit, card) {
    handlePlayerMove(value, suit, card);
}

function cardsContain(value) {
    for(var i = 0; i < player1_cards.length; i++) {
        const vs = getValueAndSuitFrom(player1_cards[i].id);
        if(vs.value == value) {
            return true;
        }
    }
    return false;
}

function sendMove(action="play") {
    user_websocket.send(JSON.stringify({
        "type": "multiplayer",
        "match_id": "{{ match.id }}",
        "action": action,
        "stacks": JSON.stringify(getConvertedStack()),
        "hand": JSON.stringify(getConvertedHand()),
        "n": played_cards.length
    }));
    played_cards = [];
    clearButtons();
}

function clearButtons() {
    for(var i = 0; i < buttons.length; i++) {
        buttons[i].remove();
    }
    buttons = [];
}

function clearStacks() {
    for(var i = 0; i < stacks.length; i++) {
        for(var j = 0; j < stacks[i].length; j++) {
            stacks[i][j].remove();
        }
    }
    stacks = [];
}

function setupNewRound(data) {
    clearStacks();
    clearButtons();
    var new_deck = JSON.parse(data.deck);
    removeCardsFromDeck(deck.length-new_deck.length);
    determineGameMode(data.attacking, data.defending);
    for(var i = 0; i < player_list.length; i++) {
        var username = player_list[i];
        var player = players[username];
        if(username == this_user) {
            var old_hand = getConvertedHand();
            var new_hand = JSON.parse(data[username]);
            for(var j = 0; j < new_hand.length; j++) {
                if(!old_hand.includes(new_hand[j])) {
                    addCardTo(1, 1, new_hand[j]);
                }
            }
        }
        else {
            var old_count = player_cards[player].length;
            var new_count = JSON.parse(data[username]).length;
            const n = old_count-new_count;
            if(n > 0) {
                addCardTo(player, n);
            }
            else {
                removeCardFrom(player, -n);
            }
        }
    }
}

function handleTransfer(data) {
    clearButtons();
    determineGameMode(data.attacking, data.defending);
    updateButtons();
    refreshStacks(JSON.parse(data.stacks));
}

user_websocket.onopen = function() {
    sendAction("request_data");
}

function sendAction(action) {
    user_websocket.send(JSON.stringify({
        'type': 'multiplayer', 
        'match_id': '{{ match.id }}',
        'action': action
    }));
}

function next(el, arr) {
    return arr[((arr.indexOf(el)+1)%arr.length+arr.length)%arr.length];
}

function before(el, arr) {
    return arr[((arr.indexOf(el)-1)%arr.length+arr.length)%arr.length];
}


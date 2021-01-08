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
    
}

function done() {
    user_websocket.send(JSON.stringify({
        "type": "multiplayer",
        "match_id": "{{ match.id }}",
        "action": "done",
        "user_id": "{{ user.id }}"
    }));
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

function confirmBeating() {
    
}

function confirmTransfer() {
    
}

function handlePlayerMove(value, suit, card) {
    switch(game_mode) {
        case "none":
            return;
        case "defending":
            var targets = stackTargetsFor(value, suit);
            var transfer_possible = transferPossible(value);
            if(transfer_possible && targets.length == 0) {
                alert("only transfer");
                //only transfer possible
                played_cards.push(card);
                removePlayerCard(card);
                addStack(card.id);
            }
            else if(transfer_possible && targets.length > 0) {
                alert("both");
                //transfer and beating are both possible
                createButton("Schlagen", "beating", confirmBeating);
                createButton("Schieben", "transfer", confirmTransfer);
                game_mode = "none";
                played_cards.push(card);
                return;
            }
            else if(targets.length == 1) {
                alert("only one beating");
                //only beating possible, one card can be beaten
                played_cards.push(card);
                beatStack(targets[0], card.id);
                removePlayerCard(card);
                sendMove();
            }
            else if(targets.length > 1) {
                alert("only more beating");
                //only beating possible, more than one card can be beaten
                card.style.top = (parseFloat(card.style.top)-10)+"px";
                for(var i = 0; i < stacks.length; i++) {
                    if(stacks[i].length == 1) {
                        stacks[i][0].cursor = "pointer";
                        stacks[i][0].onclick = function() {
                            var j = 0;
                            while(stacks[j][0].id != this.id) {
                                j++;
                            }
                            beatStack(j+1, card.id);
                            played_cards.push(card);
                            removePlayerCard(card);
                            game_mode = "defending";
                        }
                    }
                }
                game_mode = "none";
                return;
            }
            else {
                return;
            }
            break;
        case "helping":
        case "attacking":
            if(played_cards.length == 0) {
                played_cards.push(card);
                addStack(card.id);
                removePlayerCard(card);
            }
            else {
                const old_vs = getValueAndSuitFrom(played_cards[0].id);
                if(old_vs.value != value) {
                    return;
                }
                played_cards.push(card);
                addStack(card.id);
                removePlayerCard(card);
            }
            sendMove();
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
    if(game_mode == "attacking" || game_mode == "helping") {
        createButton("Fertig", "done", done);
    }
}

function stackTargetsFor(value, suit) {
    var targets = [];
    for(var i = 0; i < stacks.length; i++) {
        if(stacks[i].length == 1) {
            const vs = getValueAndSuitFrom(stacks[i][0].id);
            if(value > vs.value && suit == vs.suit || 
                (suit == trump_vs.suit && (vs.suit != trump_vs.suit || vs.value < value))) {
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

function sendMove() {
    user_websocket.send(JSON.stringify({
        "type": "multiplayer",
        "match_id": "{{ match.id }}",
        "action": "play",
        "stacks": JSON.stringify(getConvertedStack()),
        "hand": JSON.stringify(getConvertedHand()),
        "n": played_cards.length
    }));
    played_cards = [];
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

user_websocket.onopen = function() {
    user_websocket.send(JSON.stringify({
        'type': 'multiplayer', 
        'action': 'request_data', 
        'match_id': '{{ match.id }}'
    }));
}

function next(el, arr) {
    return arr[((arr.indexOf(el)+1)%arr.length+arr.length)%arr.length];
}

function before(el, arr) {
    return arr[((arr.indexOf(el)-1)%arr.length+arr.length)%arr.length];
}


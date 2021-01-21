var game_mode = "none";
var this_user = '{{ user }}';
var played_cards = [];
var player_list;
var move_mode = "none";
var old_stacks = [];
var selected_card;
var defending;
var durak_websocket;

function processMultiplayerData(data) {
    var delayed = false;
    switch(data.action) {
        case "load_data":
            loadGameField(data);
            break;
        case "play":
            handleMove(data);
            break;
        case "new_round":
            delayedCall(setupNewRound, data.data);
            delayed = true;
            break;
        case "transfer":
            handleTransfer(data);
            break;
        case "take":
            move_mode = "take";
            changeInfoFor(defending, " (SCHLUCKT)");
            break;
        case "abort":
            location.href = data.url;
            break;
    }
    if(!delayed) {
        updateButtons();
    }
}

function delayedCall(callback, arg) {
    var timeout = 0;
    if(game_mode != "defending" && (!attackingIsPossible() || move_mode == "take")) {
        timeout = 500;
    }
    setTimeout(function() {
        callback(arg);
        updateButtons();
    }, timeout);
}

function cardClicked(value, suit, card) {
    switch(game_mode) {
        case "none":
            return;
        case "defending":
            var targets = stackTargetsFor(value, suit);
            var transfer_possible = transferPossible(value);
            if(transfer_possible && targets.length == 0) {
                createStackWith(card);
                move_mode = "transfer";
                game_mode = "attacking";
            }
            else if(transfer_possible && targets.length > 0) {
                createStackCallbacks(targets, card);
                move_mode = "transfer";
            }
            else if(targets.length == 1) {
                move_mode = "beating";
                beatStackWith(card, targets[0]);
            }
            else if(targets.length > 1) {
                createStackCallbacks(targets, card);
                move_mode = "beating";
            }
            else {
                return;
            }
            break;
        case "helping":
            if(!old_stacks.length) {
                return;
            }
        case "attacking":
            if(!attackingIsPossible() || (stacks.length && !stacksContainValue(value))) {
                return;
            }
            createStackWith(card);
            if(move_mode != "transfer") {
                move_mode = "attacking";
            }
            if(!playerHandContains(getVs(stacks[0][0].id).value) || old_stacks.length) {
                sendMove();
                sendAction("done");
            }
            break;
    }
    updateButtons();
}

function clear() {
    clearStacks();
    clearButtons();
    removeCardsFromDeck(100);
    for(var i = 1; i < 5; i++) {
        removeCardFrom(i, 100);
    }
    played_cards = [];
    no_cards = [];
    move_mode = "none";
}

function loadGameField(data) {
    clear();
    var deck = JSON.parse(data.deck);
    player_list = JSON.parse(data.players);
    positionPlayers(player_list);
    updatePlayerInfo(data);
    determineGameMode(data);
    trump_suit = data.trump;
    addCardsToDeck(deck.length-1, deck[deck.length-1]);
    defineSortValues(ten_high=false);
    displayCards(data, player_list);
    old_stacks = JSON.parse(data.stacks);
    refreshStacks(old_stacks);
}

function updatePlayerInfo(data) {
    for(var i = 0; i < player_list.length; i++) {
        var username = player_list[i];
        if(username == data.attacking) {
            changeInfoFor(username, "(ANGREIFER)");
        }
        else if(username == data.defending) {
            changeInfoFor(username, " (VERTEIDIGER)");
        }
        else {
            changeInfoFor(username, "");
        }
    }
    defending = data.defending;
}

function determineGameMode(data) {
    if(this_user == data.attacking) {
        game_mode = "attacking";
    }
    else if(this_user == data.defending) {
        game_mode = "defending";
    }
    else if(this_user == data.taking) {
        game_mode = "none";
    }
    else {
        if(this_user == next(data.defending, player_list)) {
            game_mode = "helping";
        }
        else {
            game_mode = "none";
        }
    }
    if(data.taking) {
        move_mode = "take";
        changeInfoFor(data.taking, " (SCHLUCKT)");
    }
}

function handleMove(data) {
    if(data.username == this_user) {
        return;
    }
    var player = players[data.username];
    removeCardFrom(player, data.n);
    old_stacks = JSON.parse(data.stacks);
    refreshStacks(old_stacks);
}

function clearStackCallbacks() {
    for(var k = 0; k < stacks.length; k++) {
        stacks[k][0].onclick = null;
    }
}

function createStackCallbacks(targets, card) {
    if(selected_card) {
        return;
    }
    card.style.top = (parseFloat(card.style.top)-10)+"px";
    selected_card = card;
    for(var i = 0; i < targets.length; i++) {
        var t = targets[i];
        stacks[t-1][0].cursor = "pointer";
        stacks[t-1][0].onclick = function() {
            var j = 0;
            while(stacks[j][0].id != this.id) {
                j++;
            }
            beatStackWith(card, j+1);
            selected_card = null;
            clearStackCallbacks();
            move_mode = "beating";
            game_mode = "defending";
            updateButtons();
        }
    }
}

function createStackWith(card) {
    played_cards.push(card);
    removePlayerCard(card);
    addStack(card.id);
}

function beatStackWith(card, stack) {
    beatStack(stack, card.id);
    played_cards.push(card);
    removePlayerCard(card);
    sendMove();
    if(player1_cards.length == 0 || game_mode == "defending" && allDefended()) {
        console.log("beatStackWith: no cards or defended, send done");
        sendAction("done");
    }
}

function stacksContainValue(value) {
    for(var i = 0; i < stacks.length; i++) {
        for(var j = 0; j < stacks[i].length; j++) {
            const vs = getVs(stacks[i][j].id);
            if(value == vs.value) {
                return true;
            }
        }
    }
    return false;
}

function attackingIsPossible() {
    if(game_mode != "attacking" && game_mode != "helping" || !player1_cards.length) {
        return false;
    }
    var count = player_cards[players[defending]].length;
    if(stacks.length == 6 || count == undefendedCardCount()) {
        return false;
    }
    
    return true;
}

function allDefended() {
    if(!stacks.length) {
        return false;
    }
    for(var i = 0; i < stacks.length; i++) {
        if(stacks[i].length != 2) {
            return false;
        }
    }
    return true;
}

function sendMove() {
    durak_websocket.send(JSON.stringify({
        "action": move_mode,
        "stacks": JSON.stringify(getConvertedStack()),
        "hand": JSON.stringify(getConvertedHand()),
        "n": played_cards.length
    }));
    played_cards = [];
    move_mode = "none";
    clearButtons();
}

function sendAction(action) {
    durak_websocket.send(JSON.stringify({
        'action': action
    }));
}

function transferCheck() {
    if(playerHandContains(getVs(stacks[0][0].id).value)) {
        createButton("Fertig", "done", sendMove);
    }
    else {
        sendMove();
    }
}

function updateButtons() {
    clearButtons();
    if(player1_cards.length == 0 || game_mode == "none") {
        console.log("updateButtons: no cards, send done");
        sendAction("done");
        return;
    }
    if(move_mode != "take" && game_mode == "defending" && undefendedCardCount()) {
        createButton("Schlucken", "take", function() {
            sendAction("take");
            deleteButton("take");
        });
    }
    if((game_mode == "defending" || game_mode == "attacking") && move_mode == "transfer") {
        if(played_cards.length) {
            transferCheck();
        }
        else {
            createButton("Schieben", "transfer", function() {
                createStackWith(selected_card);
                selected_card = null;
                deleteButton("transfer");
                transferCheck();
            });
        }
    }
    if(game_mode == "attacking" && played_cards.length && !old_stacks.length && playerHandContains(getVs(stacks[0][0].id).value)) {
        if(attackingIsPossible()) {
            createButton("Fertig", "done", sendMove);
        }
        else {
            sendMove();
        }
    }
    
    if((game_mode == "attacking" || game_mode == "helping") && (move_mode == "take" || allDefended())) {
        if(attackingIsPossible()) {
            createButton("Fertig", "done", function() {
                console.log("button pressed, send done");
                sendAction("done");
                deleteButton("done");
            });
        }
        else {
            console.log("updateButtons: attacking/helping, send done");
            sendAction("done");
        }
    }
}

function undefendedCardCount() {
    var count = 0;
    for(var i = 0; i < stacks.length; i++) {
        if(stacks[i].length == 1) {
            count++;
        }
    }
    return count;
}

function stackTargetsFor(value, suit) {
    var targets = [];
    for(var i = 0; i < stacks.length; i++) {
        if(stacks[i].length == 1) {
            const vs = getVs(stacks[i][0].id);
            const bigger = value_values[value] > value_values[vs.value];
            if(bigger && suit == vs.suit || 
                (suit == trump_suit && (vs.suit != trump_suit || bigger))) {
                targets.push(i+1);
            }
        }
    }
    return targets;
}

function transferPossible(value) {
    if(stacks.length == 0) {
        return false;
    }
    var left_username = next(this_user, player_list);
    while(player_cards[players[left_username]].length == 0 && left_username != this_user) {
        left_username = next(left_username, player_list);
    }
    if(left_username == this_user) {
        return false;
    }
    var left_count = player_cards[players[left_username]].length;
    if(left_count < stacks.length+1) {
        return false;
    }
    for(var i = 0; i < stacks.length; i++) {
        if(stacks[i].length > 1 ||
            getVs(stacks[i][0].id).value != value) {
            return false;
        }
    }
    return true;
}

function playerHandContains(value) {
    for(var i = 0; i < player1_cards.length; i++) {
        const vs = getVs(player1_cards[i].id);
        if(vs.value == value) {
            return true;
        }
    }
    return false;
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
    move_mode = "none";
    clearStacks();
    old_stacks = [];
    var new_deck = JSON.parse(data.deck);
    removeCardsFromDeck(deck.length-new_deck.length);
    determineGameMode(data);
    updatePlayerInfo(data);
    for(var i = 0; i < player_list.length; i++) {
        var username = player_list[i];
        var player = players[username];
        if(username == this_user) {
            var old_hand = getConvertedHand();
            var new_hand = JSON.parse(data[this_user]);
            for(var j = 0; j < new_hand.length; j++) {
                if(!old_hand.includes(new_hand[j])) {
                    addCardTo(1, 1, new_hand[j]);
                }
            }
        }
        else {
            var old_count = player_cards[player].length;
            var new_count = JSON.parse(data[username]).length;
            const n = new_count-old_count;
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
    determineGameMode(data);
    refreshStacks(JSON.parse(data.stacks));
    updatePlayerInfo(data);
    if(game_mode == "attacking") {
        return;
    }
    var attacking = players[data.attacking];
    removeCardFrom(attacking, player_cards[attacking].length-data.attacking_n)
}

function durakConnect() {
    durak_websocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/multiplayer/durak/'
        + '{{ match.id }}/'
        + '{{ user.username }}/'
    );

    durak_websocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if(data.action == "match_list") {
            updateMatchList(data);
        }
        else {
            processMultiplayerData(data);
        }
    }
    
    durak_websocket.onopen = function() {
        sendAction("request_data");
    }

    durak_websocket.onclose = function(e) {
        console.log('User socket closed unexpectedly. Attempting reconnect in 1 second. Code: ', e.code);
        setTimeout(function() {
            durakConnect();
        }, 1000);
    }

    durak_websocket.onerror = function(err) {
        console.error('User socket encountered error: ', err.message, 'Closing socket.');
        durak_websocket.close();
    }
}

durakConnect();

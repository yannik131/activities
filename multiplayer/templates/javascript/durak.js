{% load i18n %}

var game_mode = "none";
var played_cards = [];
var player_list;
var move_mode = "none";
var old_stacks = [];
var selected_card;
var defending;
var button_color = "white";
var trump_suit;
var is_taking;
var done_list = [];
var paused = false;

function defineSortValues(trump_suit) {
    var suits = ["d", "h", "s", "c"];
    for(var i = 0; i < suits.length; i++) {
        suit_values[suits[i]] = i+1;
    }
    suit_values[trump_suit] = 1000;
    var values= ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"];
    for(var i = 0; i < values.length; i++) {
        value_values[values[i]] = (i+1)*50;
    }
}

function getCardSortValue(type) {
    return getCardSortValueDefault(type);
}

function processMultiplayerData(data) {
    var delayed = false;
    if(data.done_list) {
        done_list = JSON.parse(data.done_list);
    }
    switch(data.action) {
        case "load_data":
            delayed = Boolean(player_list);
            if(delayed) {
                delayedCall(loadGameField, data);
            }
            else {
                loadGameField(data);
            }
            return;
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
            handleTake();
            break;
        case "abort":
            location.href = data.url;
            return;
        case 'done':
            updateDone();
            return;
    }
    if(!delayed) {
        updateButtons();
        if((player1_cards.length == 0 || game_mode == "none") && !(data.action == 'play' && data.username == this_user)) {
            console.log(new Date(), '2: done after', data.action);
            sendDone();
            return;
        }
        else if((game_mode == "attacking" || game_mode == "helping") && (allDefended() || is_taking)) {
            if(!attackingIsPossible()) {
                console.log(new Date(), '3: done after', data.action);
                sendDone();
                return;
            }
        }
    }
    updateDone();
    
}

function updateDone() {
    for(var i = 0; i < player_list.length; i++) {
        var username = player_list[i];
        makeYellow(username);
    }
}

function makeYellow(username) {
    var player_info = document.getElementById("info-div-"+username);
    if(done_list.indexOf(username) != -1) {
        player_info.className += " dealer";
    }
    else {
        player_info.className = 'info-div';
    }
}

function handleTake() {
    is_taking = true;
    changeInfoFor(defending, " ({% trans 'SCHLUCKT' %})");
}

function delayedCall(callback, arg) {
    var timeout = 0;
    if(game_mode != "defending" && (!attackingIsPossible() || is_taking)) {
        timeout = 1000;
    }
    setTimeout(function() {
        callback(arg);
        updateButtons();
    }, timeout);
}

function cardClicked(value, suit, card) {
    if(paused) {
        return;
    }
    switch(game_mode) {
        case "none":
            return;
        case "defending":
            var targets = stackTargetsFor(value, suit);
            var transfer_possible = transferPossible(value);
            if(transfer_possible && (targets.length == 0 || played_cards.length)) {
                clearStackCallbacks();
                createStackWith(card);
                move_mode = "transfer";
                transferCheck();
            }
            else if(transfer_possible && targets.length > 0) {
                if(move_mode != "transfer") {
                    createStackCallbacks(targets, card);
                    move_mode = "transfer";
                }
            }
            else if(targets.length == 1) {
                if(move_mode == "transfer") {
                    return;
                }
                clearStackCallbacks();
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
            if(!attackingIsPossible() || (stacks.length && !stacksContain(value))) {
                return;
            }
            move_mode = "attacking";
            createStackWith(card);
            if(!playerHandContains(getVs(stacks[0][0].id).value) || old_stacks.length) {
                sendMove();
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
    is_taking = Boolean(data.taking);
    positionPlayers(player_list);
    updatePlayerInfo(data);
    trump_suit = data.trump;
    defineSortValues(trump_suit);
    addCardsToDeck(deck.length-1, deck[deck.length-1]);
    displayCards(data, player_list);
    old_stacks = JSON.parse(data.stacks);
    refreshStacks(old_stacks);
    determineGameMode(data);
    updateDone();
    if(data.summary) {
        summary = "{% trans 'Spiel Nummer' %}: "+data.game_number+"\n"+data.summary;
        showScore();
    }
    updateButtons();
}

function updatePlayerInfo(data) {
    for(var i = 0; i < player_list.length; i++) {
        var username = player_list[i];
        if(username == data.attacking) {
            changeInfoFor(username, "({% trans 'ANGREIFER' %})");
        }
        else if(username == data.defending) {
            changeInfoFor(username, " ({% trans 'VERTEIDIGER' %})");
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
    else if(player_list.length == 4 && player_cards[players[data.attacking]].length == 0 && this_user == before(data.attacking, player_list) && player1_cards.length > 0) {
        game_mode = "helping";
    }
    else {
        var helping = next(data.defending, player_list);
        if(player_list.length == 4) {
            if(player_cards[players[helping]].length == 0) {
                helping = next(helping, player_list)
            }
        }
        if(this_user == helping) {
            game_mode = "helping";
        }
        else {
            game_mode = "none";
        }
    }
    if(data.taking) {
        is_taking = true;
        changeInfoFor(data.taking, " ({% trans 'SCHLUCKT' %})");
        makeYellow(data.taking);
    }
}

function handleNewCards(data, callback, pause) {
    paused = pause;
    var player = players[data.username];
    var cards = JSON.parse(data.played_cards);
    removeCardFrom(player, cards.length);
    for(var i = 0; i < cards.length; i++) {
        addCardTo(player, 1, cards[i], true);
    }
    setTimeout(function() { 
        callback(cards, player, data);
        for(var i = 0; i < cards.length; i++) {
            removeCardFrom(player, 1, cards[i]);
        }
        updateButtons();
        paused = false;
    }, 750);
}

function handleMove(data) {
    old_stacks = JSON.parse(data.stacks);
    if(data.username == this_user) {
        return;
    }
    function callback(cards, player, data) {
        var old_stacks = JSON.parse(data.stacks);
        if(move_mode == "transfer") {
            for(var i = 0; i < old_stacks.length; i++) {
                if(!stacksContain(null, getVs(old_stacks[i][0]).suit)) {
                    addStack(old_stacks[i][0]);
                }
            }
            return;
        }
        else {
            refreshStacks(old_stacks);
        }
        determineGameMode(data);
    }
    handleNewCards(data, callback);
}

function clearStackCallbacks() {
    if(selected_card) {
        selected_card.style.top = (parseFloat(selected_card.style.top)+10)+"px";
        selected_card = undefined;
    }
    for(var k = 0; k < stacks.length; k++) {
        stacks[k][0].onclick = null;
    }
}

function createStackCallbacks(targets, card) {
    if(card == selected_card) {
        return;
    }
    for(var i = 0; i < player1_cards.length; i++) {
        player1_cards[i].style.top = field.offsetHeight-h+"px";
    }
    card.style.top = field.offsetHeight-h-10+"px";
    selected_card = card;
    for(var i = 0; i < targets.length; i++) {
        var t = targets[i];
        stacks[t-1][0].cursor = "pointer";
        stacks[t-1][0].onclick = function() {
            var j = 0;
            while(stacks[j][0].id != this.id) {
                j++;
            }
            move_mode = "beating";
            game_mode = "defending";
            beatStackWith(card, j+1);
            selected_card = null;
            clearStackCallbacks();
            updateButtons();
        }
    }
}

function createStackWith(card) {
    played_cards.push(card.id);
    removePlayerCard(card);
    addStack(card.id);
}

function beatStackWith(card, stack) {
    beatStack(stack, card.id);
    played_cards.push(card.id);
    removePlayerCard(card);
    sendMove();
    if(player1_cards.length == 0 || game_mode == "defending" && allDefended()) {
        console.log(new Date(), '1: done');
        sendDone();
    }
}

function stacksContain(value, suit) {
    for(var i = 0; i < stacks.length; i++) {
        for(var j = 0; j < stacks[i].length; j++) {
            const vs = getVs(stacks[i][j].id);
            if(value == vs.value || suit == vs.suit) {
                return true;
            }
        }
    }
    return false;
}

function attackingIsPossible() {
    if(game_mode != "attacking" && game_mode != "helping") {
        return false;
    }
    var count = player_cards[players[defending]].length;
    if(move_mode != "transfer" && (stacks.length == 6 || count == undefendedCardCount())) {
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
    socket.send(JSON.stringify({
        "action": move_mode,
        "stacks": JSON.stringify(getConvertedStack()),
        "hand": JSON.stringify(getConvertedHand()),
        "played_cards": JSON.stringify(played_cards)
    }));
    played_cards = [];
    move_mode = "none";
    clearButtons();
}

function transferCheck() {
    if(playerHandContains(getVs(stacks[0][0].id).value)) {
        createButton("{% trans 'Fertig' %}", "done", sendMove, button_color);
    }
    else {
        sendMove();
    }
}

function updateButtons() {
    if(!player_list) {
        return;
    }
    clearButtons();
    if(player1_cards.length == 0 || game_mode == "none") {
        return;
    }
    if(!is_taking && game_mode == "defending" && undefendedCardCount()) {
        createButton("{% trans 'Schlucken' %}", "take", function() {
            sendAction("take");
            deleteButton("take");
        }, button_color);
    }
    if((game_mode == "defending" || game_mode == "attacking") && move_mode == "transfer") {
        if(played_cards.length) {
            transferCheck();
        }
        else if(!is_taking) {
            createButton("{% trans 'Schieben' %}", "transfer", function() {
                createStackWith(selected_card);
                deleteButton("transfer");
                transferCheck();
                clearStackCallbacks();
            }, button_color);
        }
    }
    if(game_mode == "attacking" && played_cards.length && !old_stacks.length && playerHandContains(getVs(stacks[0][0].id).value)) {
        if(attackingIsPossible()) {
            createButton("{% trans 'Fertig' %}", "done", sendMove, button_color);
        }
        else {
            sendMove();
        }
    }
    
    if((game_mode == "attacking" || game_mode == "helping") && (allDefended() || is_taking)) {
        if(attackingIsPossible()) {
            createDoneButton();
        }
    }
}

function createDoneButton() {
    if(done_list && done_list.indexOf(this_user) != -1) {
        return;
    }
    createButton("{% trans 'Fertig' %}", "done", function() {
        sendAction("done");
        deleteButton('done');
    }, button_color);
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

function setupNewRound(data) {
    move_mode = "none";
    is_taking = false;
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
    function callback(cards, player, data) {
        clearStacks();
        refreshStacks(JSON.parse(data.stacks));
        updatePlayerInfo(data);
        old_stacks = JSON.parse(data.stacks);
        determineGameMode(data);
    }
    handleNewCards(data, callback, true);
}

function sendDone() {
    if(done_list.indexOf(this_user) != -1) {
        return;
    }
    console.log(new Date(), 'sending done with list:', done_list);
    sendAction('done');
    done_list.push(this_user);
    updateDone();
}

window.addEventListener('load', function() {
    gameConnect('durak', '{{ match.id }}', '{{ user.username }}');
});


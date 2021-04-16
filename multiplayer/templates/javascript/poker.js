{% load i18n %}

//Test: First round, no raises: Big Blind can check or raise, check -> next round
//Test: Every round, raise: Only calls/folds -> next round
//Test: Second round or above, no raises: Dealer or right of him checks -> next round
is_poker = true;
var active, cards, my_bet, my_stack, highest_bet_value, highest_bet_user, previous_raise, pot, showdown;

HAND_TRANSLATIONS = {
    'high_card': "{% trans 'High Card' %}",
    'pair': "{% trans 'Ein Paar' %}",
    'two_pair': "{% trans 'Zwei Paare' %}",
    'three_of_a_kind': "{% trans 'Drilling' %}",
    'straight': "{% trans 'Straße' %}",
    'flush': "{% trans 'Flush' %}",
    'full_house': "{% trans 'Full House' %}",
    'four_of_a_kind': "{% trans 'Vierling' %}",
    'straight_flush': "{% trans 'Straight Flush' %}",
    'royal_flush': "{% trans 'Royal Flush' %}"
}

function processMultiplayerData(data) {
    switch(data.action) {
        case "load_data":
            loadGameField(data);
            break;
        case 'raise':
            handleRaise(data);
            break;
        case 'fold':
            handleFold(data);
            break;
        case 'call':
            handleCall(data);
            break;
        case 'check':
            handleCheck(data);
            break;
        case 'show':
            handleShow(data);
            break;
        case "abort":
            location.href = data.url;
            break;
    }
    if(data.new_round) {
        cards = JSON.parse(data.cards);
        highest_bet_user = undefined;
        showCommonCards(cards);
    }
    else if(data.forced) {
        handleShowdown(data);
    }
    updateActive(data);
    updateButtons();
    updateDisplayedText();
}

function updateDisplayedText() {
    displayText('Pot: '+pot+'\nBet: '+highest_bet_value+(!isNaN(my_bet)? '\n'+'\n'+'{% trans 'Sie' %}: '+my_bet : ""));
}

function handleShow(data) {
    if(!showdown) {
        return;
    }
    if(data.hand) {
        showCards(data.user, JSON.parse(data.hand));
    }
    if(data.new_game_data) {
        setTimeout(function() {
            var summary = data.summary;
            var hands = Object.keys(HAND_TRANSLATIONS);
            for(var i = 0; i < hands.length; i++) {
                var hand = 'HAND'+hands[i]+'HAND';
                summary = summary.replaceAll(hand, HAND_TRANSLATIONS[hands[i]]);
            }
            createInfoAlert(summary);
            var button = document.querySelector('.info-alert-button');
            button.addEventListener('click', function() {
                processMultiplayerData(data.new_game_data);
                updateButtons();
            });
        }, 1500);
    }
}

function showCards(username, cards) {
    removeCardFrom(players[username], 2);
    for(var i = 0; i < cards.length; i++) {
        addCardTo(players[username], 1, cards[i]);
    }
}

function handleShowdown(data) {
    showdown = true;
    showCards(data.forced, JSON.parse(data.hand));
}

function showCommonCards(cards) {
    clearStacks();
    for(var i = 0; i < cards.length; i++) {
        addStack(cards[i]);
    }
}

function updateActive(data) {
    if(active) {
        var div = document.getElementById('info-div-'+active);
        if(active == dealer) {
            div.className = 'info-div dealer';
        }
        else {
            div.className = 'info-div';
        }
    }
    active = data.active;
    if(!data.active) {
        return;
    }
    var div = document.getElementById('info-div-'+data.active);
    div.className = 'info-div active';
}

function handleRaise(data) {
    highest_bet_user = data.user;
    highest_bet_value += parseInt(data.value);
    var info = data.user+": raise: "+data.value+" -> "+highest_bet_value;
    if(parseInt(data.stack) == 0) {
        info += ' (all in)';
    }
    createInfoAlert(info, 1500);
    previous_raise = parseInt(data.value);
    changePokerInfoFor(players[data.user], data.user, data.stack);
    pot = parseInt(data.pot);
}

function handleFold(data) {
    createInfoAlert(data.user+': fold', 1500);
    hideCardsOf(data.user);
    if(data.new_game_data) {
        setTimeout(function() {
            createInfoAlert("{% trans 'Gewonnen: ' %}"+data.winner+"\nPot: "+data.pot, 1500);
            setTimeout(function() {
                processMultiplayerData(data.new_game_data);
                updateButtons();
            }, 1500);
        }, 1500);
    }
}

function handleCall(data) {
    if(parseInt(data.stack) == 0) {
        createInfoAlert(data.user+": all in ", 1500);
    }
    else {
        createInfoAlert(data.user+": call "+previous_raise, 1500);
    }
    pot = parseInt(data.pot);
    changePokerInfoFor(players[data.user], data.user, data.stack);
}

function handleCheck(data) {
    if(parseInt(data.stack) > 0) {
        createInfoAlert(data.user+": check", 1500);
    }
}

function getCardSortValue(type) {
    return getCardSortValueDefault(type);
}

function loadGameField(data) {
    if(data.winner) {
        alert('{% trans 'Gewinner: ' %}'+data.winner);
        location.href = '{{ match.lobby_url }}';
        return;
    }
    var player_list = JSON.parse(data.players);
    cards = JSON.parse(data.cards);
    highest_bet_user = data.highest_bet_user;
    highest_bet_value = parseInt(data.highest_bet_value);
    my_bet = parseInt(data[this_user+'_bet']);
    my_stack = parseInt(data[this_user+'_stack']);
    previous_raise = parseInt(data.previous_raise);
    pot = parseInt(data.pot);
    dealer = data.dealer;
    showdown = false;
    show_list = JSON.parse(data.show_list);
    clearStacks();
    clearButtons();
    positionPlayers(player_list);
    for(var i = 1; i < 11; i++) {
        removeCardFrom(i, 100);
    }
    cards = JSON.parse(data.cards);
    showCommonCards(cards);
    var all_players = JSON.parse(data.players);
    var alive = JSON.parse(data.alive);
    //TODO: durak, skat, doppelkopf should do this in a similar fashion to avoid cheating
    //TODO: add token to connection to avoid data grabbing
    //TODO: resize info
    for(var i = 0; i < all_players.length; i++) {
        var player = all_players[i];
        if(alive.indexOf(player) == -1) {
            addCardTo(players[player], 2);
            hideCardsOf(player);
            continue;
        }
        if(!showdown) {
            showdown = data[player+'_bet'] == 'show';
        }
        if(player == this_user || show_list.indexOf(player) != -1) {
            var hand = JSON.parse(data[player]);
            for(var j = 0; j < hand.length; j++) {
                addCardTo(players[player], 1, hand[j], true);
            }
        }
        else {
            addCardTo(players[player], 2);
        }
        if(data[player+'_bet'] == 'fold') {
            hideCardsOf(player);
        }
    }
    for(var i = 0; i < player_list.length; i++) {
        var info_div = changePokerInfoFor(players[player_list[i]], player_list[i], data[player_list[i]+'_stack']);
        if(player_list[i] == data.dealer) {
            info_div.className += " dealer";
        }
        if(player_list[i] == data.active) {
            info_div.className += " active";
        }
    }
    const blinds = JSON.parse(data.blinds);
    const level = parseInt(data.blind_level);
    var next_blinds;
    summary = "Small Blind: "+blinds[level][0]+"\nBig Blind: "+blinds[level][1];
    if(level < blinds.length-1) {
        next_blinds = blinds[level+1];
        summary += "\n{% trans 'Änderung um ' %}"+format_time_str(data.blind_time).split(', ')[1]+":\nSmall Blind: "+next_blinds[0]+"\nBig Blind: "+next_blinds[1];
    }
}

function hideCardsOf(player) {
    var cards = player_cards[players[player]];
    for(var i = 0; i < cards.length; i++) {
        cards[i].style.display = 'none';
    }
}

function call() {
    var value = highest_bet_value-my_bet;
    if(value > my_stack) {
        value = my_stack;
    }
    game_send({'action': 'call', 'value': value});
    my_stack -= value;
    my_bet += value;
    changePokerInfoFor(players[this_user], this_user, my_stack);
}

function raise() {
    if(this_user == highest_bet_user) {
        alert('{% trans 'Sie können nicht zweimal hintereinander raisen.' %}');
    }
    else {
        let minimum_bet = previous_raise;
        createInputAlert("{% trans 'Mindesteinsatz: ' %}"+minimum_bet, function(bet) {
            var value = parseInt(bet);
            var to_pay = highest_bet_value-my_bet+value;
            if(isNaN(value)) {
                alert("{% trans 'Geben Sie eine Zahl ein.' %}");
            }
            else if(value < minimum_bet && value != my_stack) {
                alert("{% trans 'Beachten Sie den Mindesteinsatz.' %}");
            }
            else if(to_pay > my_stack && value != my_stack) {
                alert("{% trans 'So viel Kohle haben Sie nicht.' %}");
            }
            else {
                game_send({'action': 'raise', 'to_pay': to_pay, 'value': value});
                my_stack -= to_pay;
                my_bet += to_pay;
                changePokerInfoFor(players[this_user], this_user, my_stack);
                return true;
            }
            return false;
        });
    }
}

function fold() {
    game_send({'action': 'fold'});
}

function check() {
    game_send({'action': 'check'});
}

function show() {
    game_send({'action': 'show', 'value': '1'});
}

function noshow() {
    game_send({'action': 'show', 'value': '0'});
}

function createRaiseButton() {
    if((my_stack-(highest_bet_value-my_bet) > 0)) {
        createButton('Raise', 'raise', raise);
    }
}

function createBetButtons() {
    createButton('Call '+(highest_bet_value-my_bet), 'call', call);
    createButton('Fold', 'fold', fold);
    createRaiseButton();
}

function updateButtons() {
    clearButtons();
    if(this_user == active) {
        if(showdown) {
            createButton('{% trans 'Zeigen' %}', 'show', show);
            createButton('{% trans 'Nicht zeigen' %}', 'noshow', noshow);
        }
        else if(my_stack == 0) {
            setTimeout(check, 500);
        }
        else if(cards.length == 0) {
            if(!highest_bet_user && my_bet == highest_bet_value) { //everyone called, i am big blind
                createButton('Check', 'check', check);
                createRaiseButton();
            }
            else {
                createBetButtons();
            }
            
        }
        else {
            if(my_bet == highest_bet_value) {
                createButton('Check', 'check', check);
                createRaiseButton();
            }
            else {
                createBetButtons();
            }
        }
    }
}

window.addEventListener('load', function() {
    gameConnect('poker', '{{ match.id }}', '{{ user.username }}');
});
{% load i18n %}

const ACTIONS = {
    updateTrick:              "updateTrick",
    updateTrickWithLastTrick: "updateTrickWithLastTrick",
    updateUserInfo:           "updateUserInfo",
    updatePlayerCards:        "updatePlayerCards",
    updateLastTrickButton:    "updateLastTrickButton",
    askForGuess:              "askForGuess",
    askForTrumpSuit:          "askForTrumpSuit",
    showStartNotification:    "showStartNotification",
    clear:                    "clear",
    sortPlayerCards:          "sortPlayerCards",
    initializeGUI:            "initializeGUI",
    updateDeck:               "updateDeck",
    sendMove:                 "sendMove",
    wait:                     "wait",
    initNextRound:            "initNextRound",
    showInitialPlayerCards:   "showInitialPlayerCards",
    waitForNextButton:        "waitForNextButton",
    removePlayerCards:        "removePlayerCards",
    removeNextButton:         "removeNextButton",
    removeLastTrickButton:    "removeLastTrickButton",
    sortPlayerCards:          "sortPlayerCards",
    trumpSuitNotification:    "trumpSuitNotification",
    waitingDummy:             "waitingDummy",
    showScore:                "showScore",
    updateScore:              "updateScore",
};

function defineSortValues(trump_suit) {
    let suits = ["d", "h", "s", "c"];
    for(let i = 0; i < suits.length; i++) {
        suit_values[suits[i]] = (i + 1) * 100;
    }
    suit_values[trump_suit] += 1000;
    value_values["A"] = -10000;
    value_values["J"] = -5000;
    let values= ["10", "9", "8", "7", "6", "5", "4", "3", "2"];
    for(let i = 0; i < values.length; i++) {
        value_values[values[i]] = i;
    }
}

function getCardSortValue(type) {
    return getCardSortValueDefault(type);
}

/**
 * Determines the winning card of the trick
 * @param {string} trump_suit 
 * @returns Index of the best card
 */
function getIndexOfHighestCard(trump_suit, trick) {
    let highest_vs;
    let index = null;
    
    for(let i = 0; i < trick.length; ++i) {
        const vs = getVs(trick[i]);

        //First wizard always wins
        if(vs.value === 'A') {
            return i;
        }
        
        //Joker always loses
        if(vs.value === 'J') {
            continue;
        }
        
        //First card that's neither joker nor wizard
        if(!highest_vs) {
            highest_vs = vs;
            index = i;
            continue;
        }
        
        //Somebody discarded a card
        if(highest_vs.suit !== trump_suit && vs.suit !== trump_suit && highest_vs.suit !== vs.suit ||
            highest_vs.suit === trump_suit && vs.suit !== trump_suit) {
            continue;
        }
        
        //Trump was not called
        if(highest_vs.suit === trump_suit && vs.suit !== trump_suit) {
            continue;
        }
        
        //There is a new card that is better than the previous one (higher values represent weaker cards since they are sorted in ascending order)
        if(highest_vs.suit !== trump_suit && vs.suit === trump_suit ||
             getCardSortValue(vs.value + vs.suit) < getCardSortValue(highest_vs.value + highest_vs.suit)) {
            highest_vs = vs;
            index = i;
        }
    }
    
    if(index === null) {
        return i - 1; //Only jokers, last player gets the trick
    }
    
    return index;
}

/**
 * Checks if a player still has trump cards
 * @param {string} trump_suit 
 * @returns 
 */
function playerHasTrump(trump_suit) {
    if(!trump_suit) {
        return false;
    }
    
    for(const card of player1_cards) {
        const vs = getVs(card.id);
        if(vs.suit === trump_suit) {
            return true;
        }
    }
    
    return false;
}

function cardCanBePlayed(value, suit, stack, trump_suit) {
    if(value === 'J' || value === 'A') {
        //jokers and wizards are always allowed
        return true;
    }
    let first_vs = getVs(stack[0].id);
    
    //If the first card is a joker, we'll try to find the first card that is neither joker nor wizard
    if(first_vs.value === 'J') {
        for(let i = 1; i < stack.length; ++i) {
            const card = stack[i];
            let vs = getVs(card.id);
            if(vs.value !== 'J' && vs.value !== 'A') {
                first_vs = vs;
                break;
            }
        }
        
        //If there is none, any card can be played
        if(first_vs.value === 'J') {
            return true;
        }
    }
    
    //If the first card is a wizard, any card can be played
    if(first_vs.value === 'A') {
        return true;
    }
    
    //Check if trump was not called
    if(first_vs.suit === trump_suit && playerHasTrump(trump_suit) && suit !== trump_suit) {
        return false;
    }
    
    //Check if suit was not called
    if(first_vs.suit !== trump_suit && suit != first_vs.suit) {
        let cards = getPlayerCards("x", first_vs.suit, ["J", "A"]);
        if(cards.length > 0) {
            return false;
        }
    }
    
    return true;
}

/**
 * Used for updateCards to see if a card was added to or removed from the player
 * @param {*} arr1 
 * @param {*} arr2 
 * @returns 
 */
function arrayDiff(arr1, arr2) {
    // Create a copy of arr2 to keep track of used elements
    let arr2Copy = arr2.slice();

    return arr1.filter(item => {
        const index = arr2Copy.indexOf(item);
        if (index !== -1) {
            arr2Copy.splice(index, 1); // Remove the element from arr2Copy
            return false; // Exclude the item from the result
        }
        return true; // Include the item in the result
    });
}

/**
 * Manages the data and game logic
 */
class Model {
    /**
     * Creates the model object
     */
    constructor() {
        this.players = []; //List of usernames
        this.active_player = null; //Username of currently active player
        this.cards = {}; //Current hand cards for every player. username : ["Ac", "2s", ...]
        this.initial_cards = {}; //Initial hand cards for every player
        this.trick_counts = {}; //Number of tricks each player has
        this.trick_guesses = {}; //Number of tricks each player has guessed he will get
        this.last_scores = {}; //Score change from the last game for each player
        this.points = {}; //Current scores for each player
        this.deck = []; //The remaining cards in the deck, top card is trump
        this.mode = null; //Current game state: guessing or playing
        this.game_number = null; //Current game number
        this.trump_suit = null; //Trump suit of the current game
        this.trick = []; //Current trick that is displayed
        this.last_trick = [];
        this.cant_add_up = false;
        
        this.commandQueue = [];
        this.next_round_data = null;
    }
    
    processServerData(data) {
        switch(data.action) {
            case "load_data":
                this.#loadData(data);
                break;
            case "set_trump_suit":
                this.handleTrumpSuit(data);
                break;
            case "guess":
                this.handleGuess(data);
                break;
            case "play":
                this.handlePlay(data);
                break;
            case "abort":
                location.href = data.url;
        }
    }
    

    #loadData(data) {
        this.players = JSON.parse(data.players);
        this.commandQueue.push(ACTIONS.initializeGUI);
        this.initRound(data);
    }
    
    initRound(data) {
        console.log("initRound");
        this.active_player = data.active;
        for(const player of this.players) {
            this.cards[player] = JSON.parse(data[player]);
            this.initial_cards[player] = JSON.parse(data[player + "_initial_hand"]);
            this.trick_counts[player] = JSON.parse(data[player + "_tricks"]);
            this.trick_guesses[player] = JSON.parse(data[player + "_guess"]);
            this.last_scores[player] = JSON.parse(data[player + '_last_score']);
            this.points[player] = JSON.parse(data[player + '_points']);
        }
        this.deck = JSON.parse(data.deck);
        console.log("setting trump");
        this.#setTrumpSuit(data);
        this.game_number = parseInt(data.game_number);
        this.mode = data.mode;
        this.trick = JSON.parse(data.trick);
        this.last_trick = JSON.parse(data['last_trick']);
        this.cant_add_up = JSON.parse(data.cant_add_up)
        console.log("Can't add up: " + this.cant_add_up);
        
        if(this.game_number > 0) {
            this.commandQueue.push(ACTIONS.updateScore);
        }
        this.commandQueue.push(ACTIONS.sortPlayerCards);
        this.commandQueue.push(ACTIONS.removeNextButton);
        this.commandQueue.push(ACTIONS.updateUserInfo);
        this.commandQueue.push(ACTIONS.updateTrick);
        this.commandQueue.push(ACTIONS.updatePlayerCards);
        this.commandQueue.push(ACTIONS.updateDeck);
        
        if(this.trump_suit === 'wizard' && this_user === this.active_player) {
            this.commandQueue.push(ACTIONS.askForTrumpSuit); //This will also ask for the guess after
            this.commandQueue.push(ACTIONS.sortPlayerCards);
            this.commandQueue.push(ACTIONS.askForGuess);
            this.trump_suit = undefined;
        }
        else if(this.mode === 'guessing' && this_user === this.active_player) {
            this.commandQueue.push(ACTIONS.askForGuess);
        }
        if(this.last_trick) {
            this.commandQueue.push(ACTIONS.updateLastTrickButton);
        }
        if(this.mode === 'playing') {
            this.commandQueue.push(ACTIONS.showStartNotification);
        }
    }
    
    initNextRound() {
        if(!this.next_round_data) {
            console.error("Called initNextRound without next round data");
            return;
        }
        this.initRound(this.next_round_data);
        this.next_round_data = null;
    }
    
    #setTrumpSuit(data) {
        if(data.trump_suit_wizard) {
            this.trump_suit = data.trump_suit_wizard;
            this.commandQueue.push(ACTIONS.trumpSuitNotification);
            return;
        }
        let top_card = getVs(this.deck[this.deck.length - 1]);
        if(top_card.value === 'A') {
            //Wizard, player needs to determine trump suit
            this.trump_suit = "wizard";
        }
        else if(top_card.value === 'J') {
            //Joker, no trump
            this.trump_suit = null;
        }
        else {
            this.trump_suit = top_card.suit;
        }
    }
    
    processClickedCard(value, suit, card) {
        if(this_user !== this.active_player || this.mode !== 'playing') {
            return;
        }
        
        if(stacks.length !== 0 && !cardCanBePlayed(value, suit, stacks[0], this.trump_suit)) {
            return;
        }
        
        let index = this.cards[this.active_player].indexOf(card.id);
        this.cards[this.active_player].splice(index, 1);
        this.trick.push(value + suit);
        
        this.active_player = undefined;
        
        this.commandQueue.push(ACTIONS.updatePlayerCards);
        this.commandQueue.push(ACTIONS.sendMove);
    }
    
    handleGuess(data) {
        this.trick_guesses[data['username']] = parseInt(data['guess']);
        this.active_player = data['active'];
        
        this.commandQueue.push(ACTIONS.updateUserInfo);
        
        if(data.mode === 'guessing' && this_user === data['active']) {
            this.commandQueue.push(ACTIONS.askForGuess);
        }
        else if(data.mode === 'playing') {
            this.mode = data.mode;
            this.commandQueue.push(ACTIONS.showStartNotification);
        }
    }
    
    handlePlay(data) {
        this.trick = JSON.parse(data['trick']);
        if(this_user !== data['username']) {
            this.cards[data['username']].pop();
        }
        this.active_player = data.active;

        this.commandQueue.push(ACTIONS.updateUserInfo);
        this.commandQueue.push(ACTIONS.updatePlayerCards);
        
        if(!data.next_trick && !data.next_round) {
            this.commandQueue.push(ACTIONS.updateTrick);
            return;
        }

        this.trick_counts[data.active] = parseInt(data[data.active + "_tricks"]);
        this.last_trick = this.trick;
        this.trick = [];
        
        this.commandQueue.push(ACTIONS.updateTrickWithLastTrick);
        this.commandQueue.push(ACTIONS.wait);
        
        if(data.next_trick) {
            this.commandQueue.push(ACTIONS.updateTrick);
            this.commandQueue.push(ACTIONS.updateLastTrickButton);
        }
        else if(data.next_round) {
            this.last_scores = JSON.parse(data.last_scores);
            this.points = JSON.parse(data.points);
            this.game_number++;
            this.commandQueue.push(ACTIONS.updateScore);
            this.commandQueue.push(ACTIONS.showScore);
            this.commandQueue.push(ACTIONS.showInitialPlayerCards);
            this.commandQueue.push(ACTIONS.removeLastTrickButton);
            
            if(data.game_over) {
                return;
            }
            
            this.next_round_data = data.round;
            this.commandQueue.push(ACTIONS.waitForNextButton);
            this.commandQueue.push(ACTIONS.removePlayerCards);
            this.commandQueue.push(ACTIONS.initNextRound);
        }
    }
    
    handleTrumpSuit(data) {
        this.trump_suit = data.trump_suit;
        defineSortValues(this.trump_suit);
        this.commandQueue.push(ACTIONS.sortPlayerCards);
        this.commandQueue.push(ACTIONS.trumpSuitNotification);
    }
}

class View {
    constructor() {
        this.suits = [["&clubs; {% trans 'Kreuz' %}", "c"],
                 ["&spades; {% trans 'Pik' %}", "s"],
                 ["&hearts; {% trans 'Herz' %}", "h"],
                 ["&diams; {% trans 'Karo' %}", "d"]];
        beat_right = true; //Unfortunate global variable from cards.js
    }
    
    updateUserInfo(players, active_player, trick_guesses, trick_counts) {
        for(const player of players) {
            let is_active = player === active_player;
            let info = is_active? " (*)" : "";
            if(trick_guesses[player] !== null) {
                info = " (" + trick_counts[player] + "/" + trick_guesses[player] + ")" + info;
            }
            else {
                info = " (?)" + info;
            }
            changeInfoFor(player, info, is_active);
        }
    }
    
    updatePlayerCards(players, cards, callback) {
        for(const player of players) {
            if(player === this_user) {
                if(player1_cards.length === 0) {
                    //Player has no cards, give them to him
                    console.log("Adding cards to player");
                    for(const card of cards[player]) {
                        addCardTo(player, 1, card);
                    }
                    
                    console.log("Setting callbacks");
                    for(const card of player1_cards) {
                        card.onclick = function() {
                            let vs = getVs(this.id);
                            callback(vs.value, vs.suit, this);
                        }
                    }
                    continue;
                }
                
                //cards[player] will contain one less card than the gui, we need to get and remove it
                let diff = arrayDiff(player1_cards.map((card) => card.id), cards[player]);
                while(diff.length > 0) {
                    console.log("Removing " + diff[0]);
                    removeCardFrom(player, 1, diff.shift());
                }
            }
            else {
                let playerIndex = window.players[player];
                let guiCards = player_cards[playerIndex];
                
                if(guiCards.length === 0) {
                    addCardTo(player, cards[player].length);
                    continue;
                }
                
                while(guiCards.length !== cards[player].length) {
                    //A card was removed
                    removeCardFrom(playerIndex, 1);
                }
            }
        }
    }
    
    updateDeck(deck) {
        removeCardsFromDeck(100);
        
        if(deck.length === 0) {
            return;
        }
        
        addCardsToDeck(deck.length - 1, deck[deck.length - 1]);
    }
    
    askForGuess(callback, max_value, cant_add_up, trick_guesses) { 
        let showScoreButton = document.getElementById('show-score-button');
        showScoreButton.onclick = null;
        let notAllowedValue = null;
        
        if(cant_add_up) {
            let undecided_count = 0;
            let total_guesses = 0;
            for(const player in trick_guesses) {
                if(trick_guesses[player] === null) {
                    undecided_count++;
                }
                else {
                    total_guesses += trick_guesses[player];
                }
            }
            if(undecided_count === 1) {
                notAllowedValue = max_value - total_guesses;
            }
        }
        
        let message = "{% trans 'Wie viele Stiche? Maximum: ' %}" + max_value;
        if(notAllowedValue !== null) {
            message += "</br>{% trans 'Verboten: ' %}" + notAllowedValue;
        }
        
        createInputAlert(message, function(value) {
            value = parseInt(value);
            if(isNaN(value)) {
                alert("{% trans 'Geben Sie eine Zahl ein.' %}");
                return false;
            }
            else if(value < 0) {
                alert("{% trans 'Kleinstmöglicher Wert: ' %}" + "0");
                return false;
            }
            else if(value > max_value) {
                alert("{% trans 'Größtmöglicher Wert: ' %}" + max_value);
                return false;
            }
            else if(value === notAllowedValue) {
                alert("{% trans 'Es darf nicht aufgehen' %}");
                return false;
            }
            
            showScoreButton.onclick = () => { window.showScore(true); }
            callback(value);
            return true;
        }, false);
    }
    
    askForTrumpSuit(callback) {
        for(const game of this.suits) {
            createButton(game[0], game[1], () => {
                game_send({'action': 'set_trump_suit', 'trump_suit': game[1]});
                for(const game of this.suits) {
                    deleteButton(game[1]);
                }
                callback();
            });
        }
    }
    
    updateTrick(trick) {
        if(trick.length === 0) {
            clearStacks();
            return;
        }
        
        if(stacks.length === 0) {
            addStack(trick[0]);
        }
        
        while(stacks[0].length < trick.length) {
            beatStack(1, trick[stacks[0].length]);
        }
    }
    
    showStartNotification(trick_guesses, active_player) {
        let notification = "{% trans 'Es spielt aus: '%}" + active_player + "</br>";
        for(const player in trick_guesses) {
            notification += player + ": " + trick_guesses[player] + "</br>";
        }
        createInfoAlert(notification, 2000);
    }
    
    showInitialPlayerCards(initial_cards) {
        //Assumes players have no cards
        for(const player in initial_cards) {
            for(const card of initial_cards[player]) {
                addCardTo(player, 1, card);
            }
        }
    }
    
    removePlayerCards(players) {
        for(const player of players) {
            removeCardFrom(player, 100);
        }
    }
    
    createNextButton(callback) {
        createButton("{% trans 'Weiter' %}", "next-round", () => { 
            callback(); 
            let scoreAlert = document.getElementById("score-alert");
            if(scoreAlert) {
                scoreAlert.remove();
            }
        });
    }
    
    removeNextButton() {
        deleteButton('next-round');
    }
    
    updateLastTrickButton(last_trick) {
        window.last_trick = last_trick;
        lastTrickButton();
    }
    
    removeLastTrickButton() {
        window.last_trick = null;
        lastTrickButton();
    }
    
    sortPlayerCards(trump_suit) {
        defineSortValues(trump_suit);
        updateCardsFor(1);
    }
    
    createTrumpSuitNotification(trump_suit) {
        for(const game of this.suits) {
            if(game[1] === trump_suit) {
                createInfoAlert("{% trans 'Trumpf ist: ' %}" + game[0], 1000);
            }
        }
    }
    
    updateScore(last_scores, points, game_number) {
        const scoresArray = Object.entries(points);
        scoresArray.sort((a, b) => b[1] - a[1]);
        
        summary = "{% trans 'Stand nach Spiel ' %}" + game_number + "/" + Math.floor(44 / scoresArray.length) + "</br>";
        for(const score of scoresArray) {
            const change = last_scores[score[0]];
            summary += score[0] + ": " + (change < 0? "" : "+") + change + " -> " + score[1] + "</br>";
        }
    }
    
    showScore() {
        window.showScore();
    }
}

class Controller {
    constructor() {
        this.model = new Model();
        this.view = new View();
        
        this.uiActionBindings = {
            [ACTIONS.updateTrick]:           () => { this.view.updateTrick(this.model.trick); },
            [ACTIONS.updateTrickWithLastTrick]: () => { this.view.updateTrick(this.model.last_trick); },
            [ACTIONS.updateUserInfo]:        () => { this.view.updateUserInfo(this.model.players, this.model.active_player, this.model.trick_guesses, this.model.trick_counts)},
            [ACTIONS.updatePlayerCards]:     () => { this.view.updatePlayerCards(this.model.players, this.model.cards, (a, b, c) => { this.cardClicked(a, b, c); }) },
            [ACTIONS.askForGuess]:           () => { this.view.askForGuess(this.askForGuessCallback, this.model.game_number + 1, this.model.cant_add_up, this.model.trick_guesses); },
            [ACTIONS.askForTrumpSuit]:       () => { this.view.askForTrumpSuit(() => { this.processEvents(); }); },
            [ACTIONS.showStartNotification]: () => { this.view.showStartNotification(this.model.trick_guesses, this.model.active_player); },
            [ACTIONS.sortPlayerCards]:       () => { this.view.sortPlayerCards(this.model.cards); },
            [ACTIONS.initializeGUI]:         () => { positionPlayers(this.model.players); durak_with_5 = this.model.players.length == 5; },
            [ACTIONS.updateDeck]:            () => { this.view.updateDeck(this.model.deck); },
            [ACTIONS.sendMove]:              () => { this.sendMove(); },
            [ACTIONS.updateLastTrickButton]: () => { this.view.updateLastTrickButton(this.model.last_trick); },
            [ACTIONS.removeLastTrickButton]: () => { this.view.removeLastTrickButton(); },
            [ACTIONS.wait]:                  null,
            [ACTIONS.initNextRound]:         () => { this.model.initNextRound(); }, 
            [ACTIONS.showInitialPlayerCards]: () => { this.view.showInitialPlayerCards(this.model.initial_cards); },
            [ACTIONS.waitForNextButton]:     () => { this.view.createNextButton(() => { this.processEvents(); }); },
            [ACTIONS.waitingDummy]:          () => {},
            [ACTIONS.removePlayerCards]:     () => { this.view.removePlayerCards(this.model.players); },
            [ACTIONS.removeNextButton]:      () => { this.view.removeNextButton(); },
            [ACTIONS.sortPlayerCards]:       () => { this.view.sortPlayerCards(this.model.trump_suit); },
            [ACTIONS.trumpSuitNotification]: () => { if(this.model.active_player === this_user) return; this.view.createTrumpSuitNotification(this.model.trump_suit); },
            [ACTIONS.updateScore]:           () => { this.view.updateScore(this.model.last_scores, this.model.points, this.model.game_number); },
            [ACTIONS.showScore]:             () => { this.view.showScore(); }
        }
        
        this.processEventsTimeout = null;
        this.processingEvents = false;
    }
    
    handleServerData(data) {
        console.log("received: " + JSON.stringify(data));
        if(this.model.commandQueue.indexOf(ACTIONS.waitingDummy) !== -1) {
            //If we are still waiting on the user to click next, we need to process the events first
            console.log("There are still items in the queue: " + this.model.commandQueue + ", processing them first..");
            this.processEvents();
            console.log("Done. Handling data");
        }
        this.model.processServerData(data);
        this.processEvents();
    }
    
    processEvents(endWait = false) {
        if(this.processingEvents) {
            console.error("Processing already in progress, aborting");
            return;
        }
        this.processingEvents = true;
        console.log("processing events: " + this.model.commandQueue);
        
        if(this.processEventsTimeout && endWait) {
            this.processEventsTimeout = null;
        }
        else if(this.processEventsTimeout) {
            return;
        }
        
        while(this.model.commandQueue.length > 0) {
            const action = this.model.commandQueue.shift();
            console.log("calling: " + action);
            if(action === ACTIONS.wait) {
                this.processEventsTimeout = setTimeout(() => { this.processEvents(true); }, 1000);
                break;
            }
            this.uiActionBindings[action]();
            if(action == ACTIONS.waitForNextButton) {
                this.model.commandQueue.unshift(ACTIONS.waitingDummy);
                break;
            }
            else if(action == ACTIONS.askForTrumpSuit) {
                break;
            }
        }
        
        this.processingEvents = false;
    }
    
    askForGuessCallback(guess) {
        game_send({'action': 'guess', 'guess': guess});
    }
    
    cardClicked(value, suit, card) {
        this.model.processClickedCard(value, suit, card);
        this.processEvents();
    }
    
    sendMove() {
        let response = {
            "action": "play",
            "trick": JSON.stringify(this.model.trick),
            "hand": JSON.stringify(this.model.cards[this_user])
        };
        if(this.model.trick.length === this.model.players.length) {
            response["index"] = getIndexOfHighestCard(this.model.trump_suit, this.model.trick);
        }
        game_send(response);
    }  
}

let controller = new Controller();

function processMultiplayerData(data) {
    controller.handleServerData(data);
}

window.addEventListener('load', function() {
    gameConnect('guess-the-tricks', '{{ match.id }}', '{{ user.username }}');
}); 

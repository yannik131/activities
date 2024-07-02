{% load i18n %}

//These numbers are not in order because I frequently edit this 
//Deal with it!
const ACTIONS = {
    updateTrick:            "updateTrick",
    removeTrick:            "removeTrick", //Also show last trick button
    updateUserInfo:         "updateUserInfo",
    updatePlayerCards:      "updatePlayerCards",
    updateLastTrickButton:  "updateLastTrickButton",
    askForGuess:            "askForGuess",
    askForTrumpSuit:        "askForTrumpSuit",
    showStartNotification:  "showStartNotification",
    clear:                  "clear",
    sortPlayerCards:        "sortPlayerCards",
    initializeGUI:          "initializeGUI",
    updateDeck:             "updateDeck",
    sendMove:               "sendMove",
    wait:                   "wait"
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
function getIndexOfHighestCard(trump_suit, trick) { //TODO buggy
    let highest_vs;
    let index;
    
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
        if(highest_vs.suit !== trump_suit && vs.suit !== trump_suit && highest_vs.suit !== vs.suit) {
            continue;
        }
        
        //There is a new card that is better than the previous one
        if(getCardSortValue(vs.value + vs.suit) < getCardSortValue(highest_vs.value + highest_vs.suit)) {
            highest_vs = vs;
            index = i;
        }
    }
    
    if(i === trick.length) {
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
    if(first_vs.suit === trump_suit && playerHasTrump() && suit !== trump_suit) {
        return false;
    }
    
    //Check if suit was not called
    if(first_vs.suit !== trump_suit && suit != first_vs.suit) {
        let cards = getPlayerCards("x", first_vs.suit);
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
        this.deck = []; //The remaining cards in the deck, top card is trump
        this.mode = null; //Current game state: guessing or playing
        this.game_number = null; //Current game number
        this.trump_suit = null; //Trump suit of the current game
        this.trick = []; //Current trick that is displayed
        
        this.commandQueue = [];
    }
    
    processServerData(data) {
        switch(data.action) {
            case "load_data":
                this.#loadData(data);
                break;
            case "guess":
                this.handleGuess(data);
                break;
            case "play":
                this.handlePlay(data);
                break;
            case "next_trick":
                this.handleNextTrick(data);
                break;
            case "next_round":
                this.handleNextRound(data);
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
        }
        this.deck = JSON.parse(data.deck);
        console.log("setting trump");
        this.#setTrumpSuit(data);
        console.log("defining sort values");
        defineSortValues(this.trump_suit);
        this.game_number = parseInt(data.game_number);
        this.mode = data.mode;
        this.trick = JSON.parse(data.trick);
        window.last_trick = JSON.parse(data['last_trick']);
        
        this.commandQueue.push(ACTIONS.updateUserInfo);
        this.commandQueue.push(ACTIONS.updateTrick);
        this.commandQueue.push(ACTIONS.updatePlayerCards);
        this.commandQueue.push(ACTIONS.updateDeck);
        
        if(this.trump_suit === 'wizard' && this_user === this.active_player) {
            this.commandQueue.push(ACTIONS.askForTrumpSuit); //This will also ask for the guess after
            this.trump_suit = undefined;
        }
        else if(this.mode === 'guessing' && this_user === this.active_player) {
            this.commandQueue.push(ACTIONS.askForGuess);
        }
        if(window.last_trick) {
            this.commandQueue.push(ACTIONS.updateLastTrickButton);
        }
        if(this.mode === 'playing') {
            this.commandQueue.push(ACTIONS.showStartNotification);
        }
    }
    
    #setTrumpSuit(data) {
        if(data.trump_suit_wizard) {
            this.trump_suit = data.trump_suit_wizard;
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
        this.commandQueue.push(ACTIONS.updateTrick);
        this.commandQueue.push(ACTIONS.updatePlayerCards);
    }
    
    handleNextTrick(data) {
        this.trick_counts[data.active] = parseInt(data[data.active + "_tricks"]);
        this.handlePlay(data);
        last_trick = this.trick;
        this.trick = [];
        
        this.commandQueue.push(ACTIONS.wait);
        this.commandQueue.push(ACTIONS.removeTrick);
        this.commandQueue.push(ACTIONS.updateLastTrickButton);
    }
    
    handleNextRound(data) {
        this.handlePlay(data);
        last_trick = null;
        this.commandQueue.push(ACTIONS.updateLastTrickButton);
        this.commandQueue.push(ACTIONS.wait);
        this.commandQueue.push(ACTIONS.removeTrick);
        
        this.initRound(data.round);
    }
}

class View {
    constructor() {
        this.askingForTrumpSuit = false;
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
                    for(const card of cards[player]) {
                        addCardTo(player, 1, card);
                    }
                    
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
    
    askForGuess(callback, min_value, max_value) { 
        if(this.askingForTrumpSuit) {
            return;
        }
        createInputAlert("{% trans 'Wie viele Stiche? ' %}", function(value) {
            value = parseInt(value);
            if(isNaN(value)) {
                alert("{% trans 'Geben Sie eine Zahl ein.' %}");
                return false;
            }
            else if(value < min_value) {
                alert("{% trans 'Kleinstmöglicher Wert: ' %}" + min_value);
                return false;
            }
            else if(value > max_value) {
                alert("{% trans 'Größtmöglicher Wert: ' %}" + max_value);
                return false;
            }
            
            callback(value);
            return true;
        }, false);
    }
    
    askForTrumpSuit(callback) {
        this.askingForTrumpSuit = true;
        
        let games = [["&clubs; {% trans 'Kreuz' %}", "c"],
                 ["&spades; {% trans 'Pik' %}", "s"],
                 ["&hearts; {% trans 'Herz' %}", "h"],
                 ["&diams; {% trans 'Karo' %}", "d"]];
        
        for(const game of games) {
            createButton(game[0], game[1], function() {
                game_send({'action': 'set_trump_suit', 'suit': game[1]});
                this.askingForTrumpSuit = false;
                callback();
            }.bind(this));
        }
    }
    
    updateTrick(trick) {
        if(stacks.length === 1 && trick.length > stacks[0].length) {
            //There is a stack and the new card has not been displayed yet
            beatStack(1, trick[trick.length - 1]);
        }
        else if(stacks.length === 1 && trick.length === 0) {
            //Next trick is already there, we want to display the old trick here
            beatStack(1, window.last_trick[window.last_trick.length - 1]);
        }
        else if(stacks.length === 0 && trick.length > 0) {
            addStack(trick[0]);
            for(let i = 1; i < trick.length; ++i) {
                beatStack(1, trick[i]);
            }
        }
    }
    
    showStartNotification(trick_guesses, active_player) {
        let notification = "{% trans 'Es spielt aus: '%}" + active_player + "</br>";
        for(const player in trick_guesses) {
            notification += player + ": " + trick_guesses[player] + "</br>";
        }
        createInfoAlert(notification, 2000);
    }
    
    removeTrick() {
        clearStacks();
    }
}

class Controller {
    constructor() {
        this.model = new Model();
        this.view = new View();
        
        this.uiActionBindings = {
            [ACTIONS.updateTrick]:           () => { this.view.updateTrick(this.model.trick); },
            [ACTIONS.removeTrick]:           () => { this.view.removeTrick(); },
            [ACTIONS.updateUserInfo]:        () => { this.view.updateUserInfo(this.model.players, this.model.active_player, this.model.trick_guesses, this.model.trick_counts)},
            [ACTIONS.updatePlayerCards]:     () => { this.view.updatePlayerCards(this.model.players, this.model.cards, (a, b, c) => { this.cardClicked(a, b, c); }) },
            [ACTIONS.askForGuess]:           () => { this.view.askForGuess(this.askForGuessCallback, 0, this.model.game_number + 1); },
            [ACTIONS.askForTrumpSuit]:       () => { this.askForTrumpSuit(); },
            [ACTIONS.showStartNotification]: () => { this.view.showStartNotification(this.model.trick_guesses, this.model.active_player); },
            [ACTIONS.sortPlayerCards]:       () => { this.view.sortPlayerCards(this.model.cards); },
            [ACTIONS.initializeGUI]:         () => { positionPlayers(this.model.players); },
            [ACTIONS.updateDeck]:            () => { this.view.updateDeck(this.model.deck); },
            [ACTIONS.sendMove]:              () => { this.sendMove(); },
            [ACTIONS.updateLastTrickButton]: () => { lastTrickButton(); },
            [ACTIONS.wait]:                  null,
        }
        
        this.processEventsTimeout = null;
    }
    
    handleServerData(data) {
        console.log("received: " + JSON.stringify(data));
        this.model.processServerData(data);
        this.processEvents();
    }
    
    processEvents(endWait = false) {
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
                return;
            }
            this.uiActionBindings[action]();
        }
    }
    
    askForTrumpSuit() {
        this.view.askForTrumpSuit(this.askForGuess);
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

/**
 * - 1. client or server input
 * - 2. the model takes the input and makes the necessary changes
 * - 3. the controller checks which UI elements need to be refreshed
 * - 4. the controller calls the appropriate UI methods to update the UI
 */
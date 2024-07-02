{% load i18n %}

//These numbers are not in order because I frequently edit this 
//Deal with it!
const ACTIONS = {
    updateTrick:            0,
    removeTrick:            2, //Also show last trick button
    updateUserInfo:         3,
    updatePlayerCards:      4,
    updateLastTrickButton:  5,
    askForGuess:            6,
    askForTrumpSuit:        7,
    showStartNotification:  8,
    clear:                  9,
    sortPlayerCards:        10,
    initializeGUI:          11,
    updateDeck:             12,
    sendMove:               13,
    wait:                   14
};

/**
 * Defines the card sort values based on the trump suit
 * @param {string} trump_suit 
 */
function defineSortValues(trump_suit) {
    var suits = ["d", "h", "s", "c"];
    for(var i = 0; i < suits.length; i++) {
        suit_values[suits[i]] = i+1; //These are global variabled from cards.js
    }
    if(trump_suit) {
        suit_values[trump_suit] += 1000;
    }
    var values= ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "A"];
    for(var i = 0; i < values.length; i++) {
        value_values[values[i]] = (i+1)*50;
    }
}

/**
 * Used for sorting the cards based on trump suit
 * @param {string} type 
 * @param {string} trump_suit 
 * @returns 
 */
function getCardSortValue(type, trump_suit) {
    const vs = getVs(type);
    const value = vs.value, suit = vs.suit;
    if(vs.suit === trump_suit && (value === 'J' || value === 'A')) {
        return value_values[value] + suit_values[suit] - 1000;
    }
    return getCardSortValueDefault(type);
}

/**
 * Determines the winning card of the trick
 * @param {string} trump_suit 
 * @returns Index of the best card
 */
function getIndexOfHighestCard(trump_suit) {
    const stack = stacks[0];
    let highest_vs;
    let index;
    
    for(let i = 0; i < stack.length; ++i) {
        const vs = getVs(stack[i].id);

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
        if(this.getCardSortValue(vs.value + vs.suit) > this.getCardSortValue(highest_vs.value + highest_vs.suit)) {
            highest_vs = vs;
            index = i;
        }
    }
    
    if(i === stack.length) {
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
        this.last_trick = null;
        
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
        this.active_player = data.active;
        for(const player of this.players) {
            this.cards[player] = JSON.parse(data[player]);
            this.initial_cards[player] = JSON.parse(data[player + "_initial_hand"]);
            this.trick_counts[player] = JSON.parse(data[player + "_tricks"]);
            this.trick_guesses[player] = JSON.parse(data[player + "_guess"]);
        }
        this.deck = JSON.parse(data.deck);
        this.#setTrumpSuit(data);
        defineSortValues(this.trump_suit);
        this.game_number = parseInt(data.game_number);
        this.mode = data.mode;
        this.trick = JSON.parse(data.trick);
        window.last_trick = data['last_trick'];
        
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
        if(this.last_trick) {
            this.commandQueue.push(ACTIONS.showLastTrickButton);
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
        console.log("Clicked: " + value + suit);
        
        if(this_user !== this.active_player || this.mode !== 'playing') {
            return;
        }
        
        if(stacks.length !== 0 && !cardCanBePlayed(value, suit, stacks[0], this.trump_suit)) {
            return;
        }
        
        let index = this.cards[this.active_player].indexOf(card.id);
        this.cards[this.active_player].splice(index, 1);
        
        this.active_player = undefined;
        
        this.commandQueue.push(ACTIONS.updatePlayerCards);
        this.commandQueue.push(ACTIONS.updateTrick);
        this.commandQueue.push(ACTIONS.sendMove);
    }
    
    handleGuess(data) {
        this.trick_guesses[data['username']] = parseInt(data['guess']);
        this.active_player = data['active'];
        
        this.commandQueue.push(ACTIONS.updateUserInfo);
        
        if(data.mode === 'guessing') {
            this.commandQueue.push(ACTIONS.askForGuess);
        }
        else {
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
        this.handlePlay(data);
        last_trick = this.trick;
        
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
    
    updateUserInfo(players, active_player, trick_guesses) {
        for(const player of players) {
            let is_active = player === active_player;
            let info = is_active? " (*)" : "";
            if(trick_guesses[player]) {
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
                        card.onclick = () => {
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
        if(stacks.length === 1) {
            //There is a stack, we just need to add a card
            beatStack(1, trick[trick.length - 1]);
        }
        else {
            addStack(trick[0]);
            for(let i = 1; i < trick.length; ++i) {
                beatStack(1, trick[i]);
            }
        }
    }
    
    showStartNotification(trick_guesses, active_player) {
        let notification = "{% trans 'Es spielt aus: '%}" + active_player + "</br>";
        for(const player of trick_guesses) {
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
            [ACTIONS.updateUserInfo]:        () => { this.view.updateUserInfo(this.model.players, this.model.active_player, this.model.trick_guesses)},
            [ACTIONS.updatePlayerCards]:     () => { this.view.updatePlayerCards(this.model.players, this.model.cards, this.cardClicked) },
            [ACTIONS.showLastTrickButton]:   () => { lastTrickButton(); },
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
    }
    
    handleServerData(data) {
        console.log(JSON.stringify(data));
        this.model.processServerData(data);
        this.processEvents();
    }
    
    processEvents() {
        while(this.model.commandQueue.length > 0) {
            const action = this.model.commandQueue.shift();
            if(action === ACTIONS.wait) {
                setTimeout(this.processEvents, 1000);
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
            "trick": JSON.stringify(getConvertedStack()[0]),
            "hand": JSON.stringify(getConvertedHand())
        };
        if(stacks[0].length == player_list.length) {
            response["index"] = getIndexOfHighestCard(this.model.trump_suit);
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
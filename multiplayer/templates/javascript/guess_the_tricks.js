{% load i18n %}

class Model {
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
    }
    
    /**
     * @brief Sets all member variables with data from the server
     * @param {*} data Data from the multiplayer match model instance
     */
    initialize(data) {
        this.players = JSON.parse(data.players);
        this.active_player = data.active;
        for(const player of this.players) {
            this.cards[player] = JSON.parse(data[player]);
            this.initial_cards[player] = JSON.parse(data[player + "_initial_hand"]);
            this.trick_counts[player] = JSON.parse(data[player + "_tricks"]);
            this.trick_guesses[player] = JSON.parse(data[player + "_guess"]);
        }
        this.deck = JSON.parse(data.deck);
        this.trump_suit = getVs(this.deck[this.deck.length - 1]).suit;
        this.game_number = parseInt(data.game_number);
        this.mode = data.mode;
    }
    
    handleGuess(data) {
        this.trick_guesses[data['username']] = parseInt(data['guess']);
        this.active_player = data['active'];
        this.mode = data['mode'];
    }
}

class View {
    updateUserInfo(players, active_player, trick_guesses) {
        for(const player of players) {
            let is_active = player === active_player;
            let info = is_active? " (*)" : "";
            if(trick_guesses[player]) {
                info = " (" + trick_guesses[player] + ")" + info;
            }
            else {
                info = " (?)" + info;
            }
            changeInfoFor(player, info, is_active);
        }
    }
    
    updateCards(players, cards) {
        for(const player of players) {
            if(player === this_user) {
                for(const card of cards[player]) {
                    addCardTo(player, 1, card);
                }
            }
            else {
                addCardTo(player, cards[player].length);
            }
        }
    }
    
    createDeck(deck) {
        if(deck.length === 0) {
            return;
        }
        addCardsToDeck(deck.length - 1, deck[deck.length - 1]);
    }
    
    askForGuess(callback, min_value, max_value) {
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
}

class Controller {
    constructor() {
        this.model = new Model();
        this.view = new View();
    }

    /**
     * callback to the loadData signal
     * @param {*} data 
     */
    loadData(data) {
        this.model.initialize(data);
        this.defineSortValues(this.model.trump_suit);
        positionPlayers(this.model.players);
        this.view.updateUserInfo(this.model.players, this.model.active_player, this.model.trick_guesses);
        this.view.updateCards(this.model.players, this.model.cards);
        this.view.createDeck(this.model.deck);
        
        this.askForGuess();
    }
    
    askForGuess() {
        if(this.model.mode !== 'guessing' || this_user !== this.model.active_player) {
            return;
        }
        
        this.view.askForGuess(this.askForGuessCallback, 0, this.model.game_number + 1);
    }
    
    handleGuess(data) {
        this.model.handleGuess(data);
        this.view.updateUserInfo(this.model.players, this.model.active_player, this.model.trick_guesses);
        
        if(this.model.mode === 'guessing') {
            this.askForGuess();
        }
        else {
            this.assignCallbacks();
        }
    }
    
    assignCallbacks() {
        for(const card of player1_cards) {
            card.onclick = function() {
                let vs = getVs(this.id);
                cardClicked(vs.value, vs.suit, this);
            }
        }
    }
    
    cardClicked(value, suit, card) {
        if(this_user !== this.model.active_player) {
            return;
        }
        
        if(stacks[0].length === 0) {
            addStack(card.id);
        }
        else {
            let first_vs = getVs(stacks[0][0].id);
            if(this.isTrump(first_vs.suit) && this.playerHasTrump() && !this.isTrump(value, suit)) {
                return;
            }
            else if(!this.isTrump(first_vs.suit) && (suit != first_vs.suit || this.isTrump(suit))) {
                let cards = getPlayerCards("x", first_vs.suit);
                for(const card of cards) {
                    if(!this.isTrump(card.suit)) {
                        return;
                    }
                }
            }
            beatStack(1, card.id, true);
        }
        
        active = undefined;
        removePlayerCard(card);
        
    }
    
    isTrump(suit) {
        return this.model.trump_suit === suit;
    }
    
    playerHasTrump() {
        for(const card of player1_cards) {
            const vs = getVs(card.id);
            if(vs.suit === this.model.trump_suit) {
                return true;
            }
        }
        
        return false;
    }
    
    askForGuessCallback(guess) {
        game_send({'action': 'guess', 'guess': guess});
    }
    
    //Functions for setting the card sort value. Does not really belong here but needs data from the model.
    
    defineSortValues(trump_suit) {
        var suits = ["d", "h", "s", "c"];
        for(var i = 0; i < suits.length; i++) {
            suit_values[suits[i]] = i+1; //These are global variabled from cards.js
        }
        suit_values[trump_suit] += 1000;
        var values= ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "A"];
        for(var i = 0; i < values.length; i++) {
            value_values[values[i]] = (i+1)*50;
        }
    }
    
    getCardSortValue(type) {
        const vs = getVs(type);
        const value = vs.value, suit = vs.suit;
        if(suit === this.model.trump_suit && (value === 'J' || value === 'A')) {
            return value_values[value] + suit_values[suit] - 1000;
        }
        return getCardSortValueDefault(type);
    }
}

let controller = new Controller();

function getCardSortValue(type) {
    return controller.getCardSortValue(type);
}

function processMultiplayerData(data) {
    console.log(JSON.stringify(data));
    switch(data.action) {
        case "load_data":
            controller.loadData(data);
            break;
        case "guess":
            controller.handleGuess(data);
            break;
        case "play":
            break;
        case "abort":
            location.href = data.url;
    }
}

window.addEventListener('load', function() {
    gameConnect('guess-the-tricks', '{{ match.id }}', '{{ user.username }}');
}); 
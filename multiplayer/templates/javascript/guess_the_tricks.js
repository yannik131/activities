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
            this.trick_guesses[player] = null;
        }
        this.deck = JSON.parse(data.deck);
        this.game_number = parseInt(data.game_number);
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
        addCardsToDeck(deck.length - 1, deck[0]);
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
        });
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
        positionPlayers(this.model.players);
        this.view.updateUserInfo(this.model.players, this.model.active_player, this.model.trick_guesses);
        this.view.updateCards(this.model.players, this.model.cards);
        this.view.createDeck(this.model.deck);

        if(this.model.mode === 'guessing' && this_user === this.model.active_player) {
            this.view.askForGuess(this.askForGuessCallback, 0, this.model.game_number + 1);
        }
    }
    
    askForGuessCallback(guess) {
        game_send({'action': 'guess', 'value': guess});
    }
}

let controller = new Controller();

function processMultiplayerData(data) {
    console.log(JSON.stringify(data));
    switch(data.action) {
        case "load_data":
            controller.loadData(data);
            return;
        case "play":
            break;
        case "abort":
            location.href = data.url;
    }
}

window.addEventListener('load', function() {
    gameConnect('guess-the-tricks', '{{ match.id }}', '{{ user.username }}');
}); 
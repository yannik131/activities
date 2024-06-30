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
        this.trick = []; //Current trick that is displayed
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
        this.trick = JSON.parse(data.trick);
        
        beat_right = true; //Unfortunate global variable from cards.js
    }
    
    handleGuess(data) {
        this.trick_guesses[data['username']] = parseInt(data['guess']);
        this.active_player = data['active'];
        this.mode = data['mode'];
    }
    
    handlePlay(data) {
        this.trick = JSON.parse(data['trick']);
        if(this_user !== data['username']) {
            this.cards[data['username']].pop();
        }
    }
}

class View {
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
    
    updateCards(players, cards) {
        for(const player of players) {
            if(player === this_user) {
                for(const card of cards[player]) {
                    addCardTo(player, 1, card);
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
    
    displayTrick(trick) {
        for(const card of trick) {
            beatStack(1, card);
        }
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
        
        if(this.model.mode === 'guessing') {
            this.askForGuess();
        }
        else {
            this.view.displayTrick(this.model.trick);
            this.assignCallbacks();
        }
    }
    
    askForGuess() {
        if(this_user !== this.model.active_player) {
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
    
    handlePlay(data) {
        this.model.handlePlay(data);
        this.view.updateCards(this.model.players, this.model.cards);
        this.view.updateUserInfo(this.model.players, this.model.active_player, this.model.trick_guesses);
    }
    
    assignCallbacks() {
        for(const card of player1_cards) {
            card.onclick = function() {
                let vs = getVs(this.id);
                cardClicked(vs.value, vs.suit, this);
            }
        }
    }
    
    cardCanBePlayed(value, suit, stack) {
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

        //There is actually a card that is neither a joker nor a wizard
        if(this.isTrump(first_vs.suit) && this.playerHasTrump() && !this.isTrump(value, suit)) {
            return false;
        }
        
        if(!this.isTrump(first_vs.suit) && (suit != first_vs.suit || this.isTrump(suit))) {
            let cards = getPlayerCards("x", first_vs.suit);
            for(const card of cards) {
                if(!this.isTrump(card.suit)) {
                    return false;
                }
            }
        }
        
        return true;
    }
    
    cardClicked(value, suit, card) {
        if(this_user !== this.model.active_player) {
            return;
        }
        
        const stack = stacks[0];
        
        if(stack.length === 0) {
            addStack(card.id);
        }
        else {
            if(!this.cardCanBePlayed(value, suit, stack)) {
                return;
            }
            beatStack(1, card.id);
        }
        
        this.model.active = undefined;
        removePlayerCard(card);
        this.sendMove();
    }
    
    sendMove() {
        let response = {
            "action": "play",
            "trick": JSON.stringify(getConvertedStack()[0]),
            "hand": JSON.stringify(getConvertedHand())
        };
        if(stacks[0].length == player_list.length) {
            response["index"] = this.getIndexOfHighestCard();
        }
        game_send(response);
    }
    
    getIndexOfHighestCard() {
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
            if(!this.isTrump(highest_vs.suit) && !this.isTrump(vs.suit) && highest_vs.suit !== vs.suit) {
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
            controller.handlePlay(data);
            break;
        case "next_trick":
            controller.handleNextTrick(data);
            break;
        case "next_round":
            controller.handleNextRound(data);
            break;
        case "abort":
            location.href = data.url;
    }
}

window.addEventListener('load', function() {
    gameConnect('guess-the-tricks', '{{ match.id }}', '{{ user.username }}');
}); 
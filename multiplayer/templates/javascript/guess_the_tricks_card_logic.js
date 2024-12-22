/**
 * Determines how the cards are sorted in the gui
 * @param {string} trump_suit 
 */
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
        
        //First card that's not a joker or wizard
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
        return 0; //Only jokers, first player gets the trick
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
        if(vs.value === 'J' || vs.value === 'A') {
            //jokers and wizards are not trump
            continue;
        }
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
let game_types = [
    "marriage", "diamonds", "clubs", "hearts", "spades", "queens", "jacks", "without"
]

let values = [
    "9", "10", "J", "Q", "K", "A"
]

let suits = [
    "d", "h", "s", "c"
]

function isTrump(value, suit, game_type) {
    switch(game_type) {
        case "marriage":
        case "diamonds":
        case "clubs":
        case "hearts":
        case "spades":
            if(value == "Q" || value == "J" || (value + suit) == "10h"
                || suit == "d" && game_type == "marriage"
                || suit == game_type[0]) {
                return true;
            }
            break;
        case "queens":
            return value == "Q";
        case "jacks":
            return value == "J";
        default:
            return false;
    }
    return false;
}

let always_trump = ["Jd", "Jh", "Js", "Jc", "Qd", "Qh", "Qs", "Qc", "10h"];

let expected_trumps = {
    "marriage": always_trump.concat(["9d", "10d", "Kd", "Ad"]),
    "diamonds": always_trump.concat(["9d", "10d", "Kd", "Ad"]),
    "clubs": always_trump.concat(["9c", "10c", "Kc", "Ac"]),
    "hearts": always_trump.concat(["9h", "Kh", "Ah"]),
    "spades": always_trump.concat(["9s", "10s", "Ks", "As"]),
    "queens": ["Qd", "Qh", "Qs", "Qc"],
    "jacks": ["Jd", "Jh", "Js", "Jc"],
    "without": []
}

let cards = [];

for(let i = 0; i < values.length; ++i) {
    for(let j = 0; j < suits.length; ++j) {
        cards.push([values[i], suits[j]]);
    }
}

let passed = true;
for(let i = 0; i < game_types.length; ++i) {
    let game_type = game_types[i];
    for(let j = 0; j < cards.length; ++j) {
        let value = cards[j][0];
        let suit = cards[j][1];
        let is_trump = isTrump(value, suit, game_type);
        if(is_trump && expected_trumps[game_type].indexOf(value + suit) === -1) {
            console.log("Is trump but should not be:", game_type, value+suit);
            passed = false;
        }
        else if(!is_trump && expected_trumps[game_type].indexOf(value + suit) !== -1) {
            console.log("Is not trump but should be:", game_type, value+suit);
            passed = false;
        }
    }
}

if(!passed) console.error("Test failed");

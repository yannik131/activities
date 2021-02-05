{% load i18n %}

function compare(vs1, vs2) {
    return getCardSortValue(vs1.value+vs1.suit, game_type != "n") > getCardSortValue(vs2.value+vs2.suit, game_type != "n");
}

function indexOfHighestCard() {
    var highest_vs = getVs(stacks[0][0].id);
    var index = 0;
    for(var i = 1; i < stacks[0].length; i++) {
        var vs = getVs(stacks[0][i].id);
        if(!isTrump(highest_vs.value, highest_vs.suit) && !isTrump(vs.value, vs.suit) && vs.suit != highest_vs.suit) {
            continue;
        }
        if(compare(vs, highest_vs)) {
            index = i;
            highest_vs = vs;
        }
    }
    console.log("stack:", getConvertedStack()[0], "highest:", highest_vs);
    return index;
}

function sendMove() {
    var response = {
        "action": "play",
        "trick": JSON.stringify(getConvertedStack()[0]),
        "hand": JSON.stringify(getConvertedHand())
    };
    if(stacks[0].length == player_list.length) {
        response["index"] = indexOfHighestCard();
    }
    socket.send(JSON.stringify(response));
}

function lastTrickButton() {
    if(!last_trick) {
        return;
    }
    createButton("{% trans 'Stich' %}", "last_trick", function() {
        if(document.getElementById("last_trick0")) {
            for(var i = 0; i < last_trick.length; i++) {
                var card = document.getElementById("last_trick"+i);
                if(card) {
                    card.remove();
                }
            }
            deleteButton("last_trick");
            lastTrickButton();
        }
        else {
            for(var i = 0; i < last_trick.length; i++) {
                var card = createCard(last_trick[i]);
                card.id = "last_trick"+i;
                card.style.position.top = "0px";
                card.style.left = i*0.4*w+"px";
                card.style.zIndex = 100;
                field.appendChild(card);
            }
            document.getElementById("last_trick").innerHTML = "{% trans 'Okay' %}";
        }
    });
}

var socket;

function processMultiplayerData(data) {
    console.log("received: " + data.action + " active: " + data.active);
    if(data.active) {
        active = data.active;
    }
    switch(data.action) {
        case "load_data":
            loadGameField(data);
            return;
        case "bid":
            handleBidding(data);
            return;
        case "take":
            handleTake(data);
            return;
        case "no_take":
            chooseGameMode();
            return;
        case "declare":
            chooseGameMode();
            return;
        case "start":
            handleStart(data);
            break;
        case "play":
            handlePlay(data);
            break;
        case "abort":
            location.href = data.url;
    }
    updateAllInfo();
}

gameConnect(socket, '{{ match.id }}', '{{ user.username }}');
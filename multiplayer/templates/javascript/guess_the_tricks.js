function processMultiplayerData(data) {
    console.log(JSON.stringify(data));
    switch(data.action) {
        case "load_data":
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
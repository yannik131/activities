{% load i18n %}

function updateMatchList(data) {
    const match_list = JSON.parse(data.match_list);
    old_tbody = document.getElementById('match-list');
    new_tbody = document.createElement('tbody');
    new_tbody.id = 'match-list';
    for(var i = 0; i < match_list.length; i++) {
        match_data = match_list[i];
        var new_row = new_tbody.insertRow();
        var new_cell = new_row.insertCell();
        new_cell.style.cursor = "pointer";
        var usernames = match_data[1];
        for(var j = 0; j < match_data[2]; j++) {
            if(j >= usernames.length) {
                new_cell.innerHTML += '{% trans "FREI" %} '
            }
            else {
                new_cell.innerHTML += (
                    usernames[j] + " "
                );
            }
        }
        new_cell.id = match_data[0]
        new_cell.onclick = function() {
            location.href = "/multiplayer/match/" + this.id + "/";
        }
    }
    old_tbody.parentNode.replaceChild(new_tbody, old_tbody);
}

function requestMatchList() {
    user_websocket.send(JSON.stringify({
        'type': 'multiplayer',
        'activity_id': '{{ activity.id }}',
        'action': 'match_list'
    }));
}

function openMatch(match_id) {
    location.href = "/multiplayer/match/" + match_id + "/";
}

user_websocket.onopen = function() {
    requestMatchList();
}
setInterval(requestMatchList, 5000);
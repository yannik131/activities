{% load i18n %}

function update() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            const data = JSON.parse(request.responseText);
            const user_list = data['members'];
            var old_tbody = document.getElementById('online-list');
            var new_tbody = document.createElement('tbody');
            new_tbody.id = "online-list";
            for(var i = 0; i < user_list.length; i++) {
                var new_row = new_tbody.insertRow();
                var new_cell = new_row.insertCell();
                new_cell.innerHTML = (
                    "<a href='/account/detail/" 
                    + user_list[i]
                    + "/'>"
                    + user_list[i]
                    + "</a>"
                );
            }  
            old_tbody.parentNode.replaceChild(new_tbody, old_tbody);
            
            const match_list = data['matches'];
            old_tbody = document.getElementById('match-list');
            new_tbody = document.createElement('tbody');
            new_tbody.id = 'match-list';
            for(var i = 0; i < match_list.length; i++) {
                match_data = match_list[i];
                var new_row = new_tbody.insertRow();
                var new_cell = new_row.insertCell();
                new_cell.style.cursor = "pointer";
                new_cell.innerHTML = (
                    "{% trans "Spieler" %}" + 
                    ": " + 
                    match_data[0] +
                    "/" +
                    match_data[1]
                );
                new_cell.onclick = function() {
                    location.href = "/multiplayer/match/" + match_data[2] + "/";
                }
            }
            old_tbody.parentNode.replaceChild(new_tbody, old_tbody);
        }
    }
    const url = "/multiplayer/get_online_list/" + {{ id }} + "/";
    request.open("GET", url, true);
    request.send();
}

update();
setInterval(update, 5000);
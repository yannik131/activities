{% load i18n %}
{% load static %}

function updateMatchList(data) {
    var list = document.getElementById('other-matches');
    list.innerHTML = "";
    const match_list = JSON.parse(data.match_list);
    for(var i = 0; i < match_list.length; i++) {
        match_data = match_list[i];
        var user_list = match_data[1];
        if(user_list.indexOf('{{ user }}') != -1) {
            continue;
        }
        var item = document.createElement('div');
        var img = document.createElement('img');
        var top = document.createElement('div');
        var middle = document.createElement('div');
        var bottom = document.createElement('div');
        var button = document.createElement('div');
        item.className = 'item';
        
        top.className = 'top';
        img.src = "{% static 'icons/match.png' %}";
        top.appendChild(img);
        top.innerHTML += user_list.length+"/"+match_data[2];
        item.appendChild(top);
        
        middle.className = 'middle';
        for(var j = 0; j < user_list.length; j++) {
            middle.innerHTML += user_list[j];
            if(j != user_list.length-1) {
                middle.innerHTML += ", ";
            }
        }
        item.appendChild(middle);
        
        bottom.className = 'bottom';
        button.className = 'button-like';
        button.id = match_data[0];
        button.onclick = function() {
            openLink("/multiplayer/enter_match/{{ activity.name }}/"+this.id+"/");
        }
        img = document.createElement('img');
        img.src = "{% static 'icons/join.png' %}";
        button.appendChild(img);
        button.innerHTML += "{% trans 'Beitreten' %}";
        bottom.appendChild(button);
        item.appendChild(bottom);
        list.appendChild(item);
    }
    resize();
}

function requestMatchList() {
    user_websocket.send(JSON.stringify({
        'type': 'multiplayer',
        'activity_id': '{{ activity.id }}',
        'action': 'match_list'
    }));
}

window.addEventListener('load', function() {
    user_websocket.onopen = function() {
        requestMatchList();
    }
    setInterval(requestMatchList, 5000);
});
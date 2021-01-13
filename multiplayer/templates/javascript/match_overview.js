{% load i18n %}

function updateMatchMembers(data) {
    var box = document.getElementById(data.match_id);
    if(!box) {
        return;
    }
    var user_box = document.querySelector(".user-box-" + data.position);
    switch(data.info) {
        case "joined":
            user_box.innerHTML = (
                data.position + 
                ": <a href='/account/detail/'" +
                data.username + 
                "/>" +
                data.username +
                "</a>"
            );
            break;
        case "left":
            user_box.innerHTML = data.position + ': {% trans "Frei" %}';
            break;
        case "start":
            location.href = "/multiplayer/game/" + data.match_id;
            break;
    }
}
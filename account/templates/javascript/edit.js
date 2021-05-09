{% load i18n %}

const msg = document.getElementById('message');
const msg_text = document.getElementById('msg-text');
var edits = {};


function saveMarker(id) {
    const value = document.getElementById(id).value;
    if(edits[id] == value) {
        return;
    }
    else {
        edits[id] = value;
    }
    send({'type': 'map', 'action': 'save_marker', 'id': id, 'description': value});
    msg_text.innerHTML = value;
    msg.style.display = 'block';
}

function deleteMarker(id) {
    var button = document.getElementById('delete-'+id);
    button.innerHTML = "{% trans 'Wirklich?' %}";
    button.onclick = function() {
        openLink("/account/delete_marker/"+id+"/");
    }
}
{% load static %}
{% load i18n %}

const like_img = "{% static 'icons/like.png' %}";
const dislike_img = "{% static 'icons/dislike.png' %}";
const remove_img = "{% static 'icons/remove.png' %}";

function shrink_to_two(post_id, is_liked) {
    const left = document.getElementById(post_id+'-left');
    const middle = document.getElementById(post_id+'-middle');
    const right = document.getElementById(post_id+'-right');
    left.style.width = "50%";
    middle.remove();
    right.style.width = "50%";
    const img = document.createElement('img');
    img.src = remove_img;
    right.onclick = function() {
        if(is_liked) {
            remove_like(post_id);
        }
        else {
            remove_dislike(post_id);
        }
    }
    right.innerHTML = "";
    right.appendChild(img);
    if(is_liked) {
        right.innerHTML += "{% trans 'Like zurücknehmen' %}";
    }
    else {
        right.innerHTML += "{% trans 'Dislike zurücknehmen' %}";
    }
}

function like(post_id) {
    send({'type': 'wall', 'action': 'like', 'id': post_id});
    shrink_to_two(post_id, true);
}

function dislike(post_id) {
    send({'type': 'wall', 'action': 'dislike', 'id': post_id});
    shrink_to_two(post_id, false);
}

function expand_to_three(post_id) {
    const left = document.getElementById(post_id+'-left');
    const right = document.getElementById(post_id+'-right');
    left.style.width = "50%";
    const middle = document.createElement('div');
    middle.className = "left";
    middle.style.width = "25%";
    right.style.width = "25%";
    middle.id = post_id+'-middle';
    var img = document.createElement('img');
    img.src = like_img;
    middle.onclick = undefined;
    setTimeout(function() {
        middle.onclick = function() {
            like(post_id);
        }
    }, 1000);
    
    middle.appendChild(img);
    right.innerHTML = "";
    img = document.createElement('img');
    img.src = dislike_img;
    right.appendChild(img);
    right.onclick = undefined;
    setTimeout(function() {
        right.onclick = function() {
            dislike(post_id);
        }
    }, 1000);
    
    const competitive = document.getElementById(post_id+'-comp');
    competitive.removeChild(right);
    competitive.appendChild(middle);
    competitive.appendChild(right);
}

function changeNumber(el, val) {
    if(typeof el == "string") {
        el = document.getElementById(el);
    }
    el.innerHTML = parseInt(el.innerText)+val;
}

function remove_like(post_id) {
    send({'type': 'wall', 'action': 'remove_like', 'id': post_id});
    expand_to_three(post_id);
}

function remove_dislike(post_id) {
    send({'type': 'wall', 'action': 'remove_dislike', 'id': post_id});
    expand_to_three(post_id);
}

function handleWallMessage(data) {
    //TODO: Wer soll das mitkriegen??
    const like_span = document.getElementById(data.post_id+"-likes");
    if(!like_span) {
        return;
    }
    const dislike_span = document.getElementById(data.post_id+"-dislikes");
    switch(data.action) {
        case 'like':
            changeNumber(like_span, 1);
            break;
        case 'dislike':
            changeNumber(dislike_span, 1);
            break;
        case 'remove_like':
            changeNumber(like_span, -1);
            break;
        case 'remove_dislike':
            changeNumber(dislike_span, -1);
            break;
    }
}
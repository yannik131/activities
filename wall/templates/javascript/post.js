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
    left.style.width = "33%";
    const middle = document.createElement('div');
    middle.className = "left";
    middle.style.width = "33%";
    right.style.width = "33%";
    middle.id = post_id+'-middle';
    var img = document.createElement('img');
    img.src = like_img;
    middle.onclick = function() {
        like(post_id);
    }
    middle.appendChild(img);
    right.innerHTML = "";
    img = document.createElement('img');
    img.src = dislike_img;
    right.appendChild(img);
    right.onclick = function() {
        dislike(post_id);
    }
    const competitive = document.getElementById(post_id+'-comp');
    competitive.removeChild(right);
    competitive.appendChild(middle);
    competitive.appendChild(right);
}

function remove_like(post_id) {
    send({'type': 'wall', 'action': 'remove_like', 'id': post_id});
    expand_to_three(post_id);
}

function remove_dislike(post_id) {
    send({'type': 'wall', 'action': 'remove_dislike', 'id': post_id});
    expand_to_three(post_id);
}
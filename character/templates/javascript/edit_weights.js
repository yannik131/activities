{% load i18n %}
{% load static %}

var weights = JSON.parse('{{ activity.weights_json|safe }}');

const save_button = document.getElementById('save');
const max_weight = 5;

function imgClick(event) {
    if(!this.state) {
        this.src = "{% static 'icons/checkmark.png' %}";
        this.state = 1;
        weights[this.trait] = [1, 1];
        this.parentElement.style.backgroundColor = "darkgreen";
    }
    else {
        this.src = "{% static 'icons/cross.png' %}";
        this.state = 0;
        delete weights[this.trait];
        this.parentElement.style.backgroundColor = "black";
    }
    update();
}

function positiveClick(event) {
    if(!weights[this.trait]) {
        return;
    }
    if(this.state) {
        this.innerHTML = "{% trans 'Niedrig' %}";
        this.state = 0;
        weights[this.trait][0] = 0;
    }
    else {
        this.innerHTML = "{% trans 'Hoch' %}";
        this.state = 1;
        weights[this.trait][0] = 1;
    }
    update();
}

function weightClick(event) {
    if(!weights[this.trait]) {
        return;
    }
    this.state++;
    if(this.state == max_weight+1) {
        this.state = 1;
    }
    weights[this.trait][1] = this.state;
    this.innerHTML = this.state+"x";
    update();
}

function addApplet(div, trait) {
    var title = document.createElement('h3');
    title.innerHTML = categories[trait];
    div.appendChild(title);
    var applet = document.createElement('div');
    applet.className = 'applet';
    var img = document.createElement('img');
    img.height = "30px";
    img.trait = trait;
    img.onclick = imgClick;
    applet.appendChild(img);
    var positive_button = document.createElement('div');
    positive_button.className = 'positive';
    positive_button.innerHTML = "{% trans 'Hoch' %}";
    positive_button.state = 1;
    positive_button.trait = trait;
    positive_button.onclick = positiveClick;
    applet.appendChild(positive_button);
    var weight_button = document.createElement('div');
    weight_button.className = 'weight';
    weight_button.innerHTML = "1x";
    weight_button.state = 1;
    weight_button.trait = trait;
    weight_button.onclick = weightClick;
    applet.appendChild(weight_button);
    if(!weights[trait]) {
        img.src = "{% static 'icons/cross.png' %}";
        img.state = 0;
    }
    else {
        weights[trait] = JSON.parse(weights[trait]);
        img.src = "{% static 'icons/checkmark.png' %}";
        img.state = 1;
        img.parentElement.style.backgroundColor = 'darkgreen';
        if(!weights[trait][0]) {
            positive_button.innerHTML = "{% trans 'Niedrig' %}";
        }
        weight_button.innerHTML = weights[trait][1]+"x";
    }
    div.appendChild(applet);
    //button farbe nach neurotizität oder nicht rot/grün machen
    //daneben gewichtung 1-3x
}

for(var i = 0; i < letters.length; i++) {
    var list = BIG_FIVE[letters[i]];
    var subtext = document.getElementById(letters[i]+"s");
    var left = document.createElement('div');
    var right = document.createElement('div');
    left.className = 'trait-left';
    right.className = 'trait-right';
    subtext.appendChild(left);
    subtext.appendChild(right);
    for(var j = 0; j < list.length; j++) {
        var trait = list[j];
        if(j < 3) {
            addApplet(left, trait);
        }
        else {
            addApplet(right, trait);
        }
    }
}

displayWeights(weights);

if(info.innerText.length == 0) {
    info.innerHTML += "{% trans 'Noch keine Gewichte verteilt!' %}";
    info.style.color = "yellow";
}

function save() {
    send({'type': 'character', 'action': 'weights', 'weights': JSON.stringify(weights), 'id': {{ activity.id }}});
    location.reload();
    window.scrollTo(0, 0);
    save_button.onclick = null;
    save_button.style.backgroundColor = "gray";
}

function update() {
    if(!save_button.onclick) {
        save_button.onclick = save;
        save_button.style.backgroundColor = 'darkgreen';
    }
}
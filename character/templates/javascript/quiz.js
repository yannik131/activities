{% load i18n %}

{% with limit=user.character.question_limit %}
const limit = {{ limit }};
{% if limit == 240 %}
    {% include 'javascript/question240.js' %}
{% elif limit == 120 %}
    {% include 'javascript/question120.js' %}
{% else %}
    {% include 'javascript/question60.js' %}
{% endif %}


var current_question = {{ user.character.current_question }};
var question_span = document.getElementById('current-question');
var slider = document.getElementById('slider');
const button = document.getElementById('send-button');
const back_button = document.getElementById('back-button');
const info = document.getElementById('info-box');
const counter = document.getElementById('counter');
const time = document.getElementById('time');
if(current_question == limit) {
    question_span.innerHTML = "{% trans 'Alle Fragen wurden beantwortet!' %}";
    button.onclick = null;
}
else {
    question_span.innerHTML = questions[current_question]+".";
}

var last_trait = null;
var last_value = null;

function update() {
    counter.innerHTML = (current_question+1)+"/{{ limit }}";
time.innerHTML = Math.ceil((limit-(current_question))*7/60)+" min";
    slider.value = 3;
}

function next() {
    var current_trait = traits[current_question];
    var key = current_trait[current_trait.length-1];
    current_trait = current_trait.substring(0, current_trait.length-1);
    var value = parseInt(slider.value);
    if(key == "+") {
        value = 6-value;
    }
    last_trait = current_trait;
    last_value = value;
    back_button.style.display = "flex";
    send({'type': 'character', 'action': 'next', 'trait': current_trait, 'value': value});
    current_question++;
    button.onclick = null;
    button.style.backgroundColor = "#8fc8f7";
    info.innerHTML = "+"+value+" "+categories[current_trait];
    if(current_question != limit) {
        question_span.innerHTML = questions[current_question]+".";
        update();
    }
    
    
    setTimeout(function() {
        button.onclick = next;
        button.style.backgroundColor = "#0087f7";
        info.innerHTML = "";
        if(current_question == limit) {
            openLink("{% url 'character:overview' %}");
        }

    }, 2000);
}

function back() {
    slider.value = 3;
    back_button.style.display = "none";
    current_question--;
    counter.innerHTML = (current_question+1)+"/{{ limit }}";
    question_span.innerHTML = questions[current_question]+".";
    send({'type': 'character', 'action': 'back', 'trait': last_trait, 'value': last_value});
}

update();
{% endwith %}
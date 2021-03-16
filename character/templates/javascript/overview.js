{% load i18n %}

const limit = {{ user.character.question_limit }};
const MAX_TRAIT_VALUE = 5*limit/30;
const MIN_TRAIT_VALUE = 1*limit/30;
var sum = 0;

const traits = JSON.parse('{{ user.character.traits_json|safe }}');
var list, title, subtext, trait, val, span, percent;

function reset() {
    var button = document.getElementById('reset');
    var text = document.getElementById('reset-text');
    text.innerHTML = "{% trans 'Klicke erneut zum Zurücksetzen.' %}";
    button.onclick = function() {
        openLink("{% url 'character:reset_quiz' %}");
    }
}

for(var i = 0; i < 5; i++) {
    sum = 0;
    list = BIG_FIVE[letters[i]];
    title = document.getElementById(letters[i]+'h');
    subtext = document.getElementById(letters[i]+"s");
    if(!subtext) {
        break;
    }
    for(var j = 0; j < 6; j++) {
        trait = list[j];
        val = parseInt(traits[trait]);
        sum += val;
        span = document.createElement('span');
        span.className = "three";
        percent = (val-MIN_TRAIT_VALUE)/(MAX_TRAIT_VALUE-MIN_TRAIT_VALUE);
        span.style.color = get_color(percent, i == 0);
        span.innerHTML += (categories[trait]+": "+Math.round(percent*100)+"% ");
        subtext.appendChild(span);
    }
    percent = (sum-MIN_TRAIT_VALUE*6)/(6*(MAX_TRAIT_VALUE-MIN_TRAIT_VALUE));
    title.style.color = get_color(percent, i == 0);
    title.innerHTML += Math.round(percent*100)+"%";
}
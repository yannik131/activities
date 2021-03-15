{% load i18n %}


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
        percent = (val-4)/16;
        span.style.color = get_color(percent, i == 0);
        span.innerHTML += (categories[trait]+": "+Math.round(percent*100)+"% ");
        subtext.appendChild(span);
    }
    percent = (sum-24)/96;
    title.style.color = get_color(percent, i == 0);
    title.innerHTML += Math.round(percent*100)+"%";
}
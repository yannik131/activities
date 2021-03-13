{% load i18n %}

const BIG_FIVE = {
    'n': ['anx', 'ang', 'dep', 'con', 'imm', 'vul'],
    'e': ['fri', 'gre', 'ass', 'act', 'exc', 'che'],
    'o': ['ima', 'art', 'emo', 'adv', 'int', 'lib'],
    'a': ['tru', 'mor', 'alt', 'coo', 'mod', 'sym'],
    'c': ['eff', 'ord', 'dut', 'ach', 'dis', 'cau']
}
const letters = ['n', 'e', 'o', 'a', 'c'];
var sum = 0;

const traits = JSON.parse('{{ user.character.traits_json|safe }}');
var list, title, subtext, trait, val, span, percent;

function get_color(percent, reverse) {
    if(!reverse) {
        return "rgb("+((1-percent)*255)+","+(percent*255)+",0)";
    }
    else {
        return "rgb("+(percent*255)+","+((1-percent)*255)+",0)";
    }
}

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
    for(var j = 0; j < 5; j++) {
        trait = list[j];
        val = parseInt(traits[trait]);
        sum += val;
        span = document.createElement('span');
        if(j < 3) {
            span.className = "three";
        }
        else {
            span.className = "two";
        }
        percent = (val-4)/16;
        span.style.color = get_color(percent, i == 0);
        span.innerHTML += (categories[trait]+": "+Math.round(percent*100)+"% ");
        subtext.appendChild(span);
    }
    percent = (sum-20)/80;
    title.style.color = get_color(percent, i == 0);
    title.innerHTML += Math.round(percent*100)+"%";
}
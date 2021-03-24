{% load i18n %}

const limit = {{ user.character.question_limit }};
const MAX_TRAIT_VALUE = 5*limit/30;
const MIN_TRAIT_VALUE = 1*limit/30;
var sum = 0;

const traits = JSON.parse('{{ user.character.traits_json|safe }}');
const normalized = JSON.parse('{{ normalized|safe }}');

function reset() {
    var button = document.getElementById('reset');
    var text = document.getElementById('reset-text');
    text.innerHTML = "{% trans 'Klicke erneut zum Zurücksetzen.' %}";
    button.onclick = function() {
        openLink("{% url 'character:reset_quiz' %}");
    }
}

function calc_score(score, reference) {
    var result;
    if(reference >= 50) {
        result = 50/(100-reference)*score+100-5000/(100-reference);
    }
    else {
        result = 50/reference*score;
    }
    if(result < 0) {
        result = 0;
    }
    else if(result > 100) {
        result = 100;
    }
    return result;
}

function displayResults() {
    var list, title, subtext, trait, val, span, percent, diff, score, prefix;

    for(var i = 0; i < 5; i++) {
        sum = 0;
        normalized_sum = 0;
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
            normalized_percent = parseInt(normalized[trait]);
            normalized_sum += normalized_percent;
            span = document.createElement('span');
            span.className = "three";
            percent = Math.round((val-MIN_TRAIT_VALUE)/(MAX_TRAIT_VALUE-MIN_TRAIT_VALUE)*100);
            score = calc_score(percent, normalized_percent);
            diff = Math.round(score-50);
            prefix = diff >= 0? "+" : "";
            span.style.color = get_color(score/100, i == 0);
            span.innerHTML += (categories[trait]+": "+prefix+diff+"% ");
            subtext.appendChild(span);
        }
        percent = (sum-MIN_TRAIT_VALUE*6)/(6*(MAX_TRAIT_VALUE-MIN_TRAIT_VALUE));
        score = calc_score(percent*100, normalized_sum/6);
        diff = Math.round(score-50);
        prefix = diff >= 0? "+" : "";
        title.style.color = get_color(score/100, i == 0);
        title.innerHTML += prefix+diff+"%";
    }
}

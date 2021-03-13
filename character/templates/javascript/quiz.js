{% load i18n %}

const traits = ["int+", "tru-", "gre-", "cau+", "dut-", "emo-", "gre+", "art+", "dep-", "ord-", "tru-", "che-", "gre-", "exc-", "mod+", "alt-", "che+", "ass-", "sym-", "adv+", "emo+", "vul-", "con-", "fri-", "mor-", "art-", "lib+", "ord+", "coo-", "lib+", "ang+", "imm-", "ang-", "emo-", "cau-", "act+", "eff+", "anx+", "act+", "ach-", "eff-", "sym+", "coo-", "gre+", "anx+", "sym+", "anx-", "art-", "ang+", "act-", "tru+", "alt+", "int-", "lib-", "ima-", "coo+", "ima+", "exc+", "fri+", "dis+", "dis+", "mor-", "dep+", "ass+", "dut+", "fri+", "con+", "int+", "imm-", "ang-", "mor+", "dut-", "vul+", "mod-", "con+", "adv-", "eff+", "che+", "ima+", "ach-", "cau-", "ima-", "vul+", "dep-", "ach+", "exc-", "dep+", "dut+", "cau+", "sym-", "dis-", "imm+", "che-", "con-", "mod+", "ach+", "art+", "exc+", "adv-", "eff-", "emo+", "act-", "imm+", "fri-", "mor+", "ord+", "mod-", "alt-", "dis-", "anx-", "alt+", "vul-", "coo+", "tru+", "ass-", "ord-", "ass+", "adv+", "int-", "lib-"];

const questions = "{% trans 'Ich kann mit viel Information auf einmal umgehen.Ich misstraue Menschen.Ich vermeide Menschenansammlungen.Ich vermeide Fehler.Ich breche Regeln.Ich habe selten emotionale Höhen oder Tiefen.Ich involviere andere in dem was ich tue.Ich liebe Blumen.Ich fühle mich wohl in meiner Haut.Ich lasse meine Sachen herumliegen.Ich bin anderen gegenüber argwöhnisch.Ich bin nicht leicht zu amüsieren.Ich mag keine überfüllten Veranstaltungen.Ich mag keine laute Musik.Ich lobe mich selten selbst.Ich kehre anderen den Rücken zu.Ich freue mich wie ein Kind.Ich bleibe im Hintergrund.Ich versuche mir nicht über Hilfsbedürftige Gedanken zu machen.Ich besuche gerne neue Orte.Ich fühle die Emotionen anderer.Ich bleibe unter Druck ruhig.Ich schäme mich nicht so leicht.Ich interessiere mich nicht wirklich für andere.Ich weiß, wie man Regeln umgehen kann.Ich mag keine Kunst.Ich denke, Kriminelle sollten eher Hilfe als Bestrafungen erhalten.Ich räume gerne auf.Ich beleidige andere Menschen.Ich denke nicht, dass es ein wirkliches richtig oder falsch gibt.Ich werde leicht wütend.Ich habe meine Bedürfnisse unter Kontrolle.Ich beschwere mich selten.Ich verstehe Menschen nicht, die emotional werden.Ich fange Dinge an ohne nachzudenken.Ich bin immer beschäftigt.Ich weiß, was ich kann.Ich mache mir Sorgen über Dinge.Ich reagiere schnell.Ich bin nicht hoch motiviert, Erfolg zu haben.Ich schätze Situationen falsch ein.Ich leide unter der Trauer anderer.Ich habe eine scharfe Zunge.Ich bin gerne Teil einer Gruppe.Ich verliere mich in meinen Problemen.Ich habe Mitleid mit Obdachlosen.Ich passe mich leicht neuen Situationen an.Ich schaue mir ungern Tanzvorstellungen an.Ich habe oft schlechte Laune.Ich lasse es gerne ruhig angehen.Ich denke, dass alles gut wird.Ich habe für jeden ein gutes Wort.Ich vermeide philosophische Diskussionen.Ich bevorzuge es, während der Nationalhymne aufzustehen.Ich verliere mich selten in Gedanken.Ich bin leicht zufriedenzustellen.Ich liebe Tagträume.Ich suche Abenteuer.Ich fühle mich bei anderen wohl.Ich fange mit Aufgaben direkt an.Ich erledige Hausarbeiten vernünftig.Ich behindere die Pläne anderer.Ich mag mich nicht.Ich übernehme das Kommando.Ich höre auf mein Gewissen.Ich muntere andere auf.Ich bin leicht eingeschüchtert.Ich liebe es, anspruchsvolle Lektüre zu lesen.Ich widerstehe leicht Versuchungen.Ich bin selten gereizt.Ich halte mich an die Regeln.Ich breche meine Versprechen.Ich werde von Gefühlen überwältigt.Ich bringe mich ins Zentrum der Aufmerksamkeit.Ich fühle mich nur bei Freunden wohl.Ich tue Dinge auf die konventionelle Art.Ich bin hervorragend in dem, was ich tue.Ich liebe das Leben.Ich verbringe Zeit damit, über Dinge zu reflektieren.Ich arbeite gerade genug, um zurechtzukommen. Ich handle gerne aus einer Laune heraus.Ich habe Schwierigkeiten, mir Dinge vorzustellen.Ich werde von Ereignissen überwältigt.Ich bin selten deprimiert.Ich arbeite hart.Ich würde niemals Drachenfliegen oder bungee jumping gehen.Ich fühle mich verzweifelt.Ich bezahle meine Rechnungen rechtzeitig.Ich wähle meine Worte mit Bedacht.Ich tendiere dazu, weichherzige Menschen nicht zu mögen.Ich verschwende meine Zeit.Ich tue Dinge, die ich später bereue.Ich bin selten albern.Ich störe mich nicht an schwierigen sozialen Situationen.Ich rede nicht gerne über mich.Ich setze Pläne in die Tat um.Ich sehe das Schöne in Dingen, die andere vielleicht nicht bemerken.Ich bin gerne Teil einer lauten Menge.Ich bin ein Gewohnheitsmensch.Ich habe wenig beizutragen.Ich untersuche gerne mich und mein Leben.Ich nehme mir gerne Zeit.Ich weiß nicht, warum ich einige Dinge tue, die ich tue.Ich bin schwer kennenzulernen.Ich würde niemals Steuern hinterziehen.Ich halte mich an den Plan.Ich denke, dass ich besser als andere bin.Ich befremde andere Menschen.Ich habe Schwierigkeiten, mit Aufgaben anzufangen.Ich lasse mich nicht leicht durch Ereignisse aus der Ruhe bringen.Ich sorge dafür, dass sich andere wohlfühlen.Ich komme leicht über Rückschläge hinweg.Ich mag keine Konfrontationen.Ich glaube an das Gute im Menschen.Ich warte darauf, dass andere die Richtung weisen.Ich störe mich nicht an Unordnung.Ich kann andere dazu überreden, Dinge zu tun.Ich bin an vielen Dingen interessiert.Ich habe kein Interesse an abstrakten Ideen.Ich denke, dass zu viel Steuergeld für die Unterstützung von Künstlern ausgegeben wird.' %}".split('.');

var current_question = {{ user.character.current_question }};
var question_span = document.getElementById('current-question');
var slider = document.getElementById('slider');
const button = document.getElementById('send-button');
const info = document.getElementById('info-box');
const counter = document.getElementById('counter');
if(current_question == 120) {
    question_span.innerHTML = "{% trans 'Alle Fragen wurden beantwortet!' %}";
    button.onclick = null;
}
else {
    question_span.innerHTML = questions[current_question]+".";
}
counter.innerHTML = (current_question+1)+"/120";

function next() {
    var current_trait = traits[current_question];
    var key = current_trait[current_trait.length-1];
    current_trait = current_trait.substring(0, current_trait.length-1);
    var value = parseInt(slider.value);
    if(key == "+") {
        value = 6-value;
    }
    send({'type': 'character', 'trait': current_trait, 'value': value});
    current_question++;
    button.onclick = null;
    button.style.backgroundColor = "#8fc8f7";
    info.innerHTML = "+"+value+" "+categories[current_trait];
    if(current_question != 120) {
        question_span.innerHTML = questions[current_question]+".";
    }
    slider.value = 3;
    setTimeout(function() {
        button.onclick = next;
        button.style.backgroundColor = "#0087f7";
        info.innerHTML = "";
        counter.innerHTML = (current_question+1)+"/120";
        
        if(current_question == 120) {
            openLink("{% url 'character:overview' %}");
        }

    }, 2000);
}
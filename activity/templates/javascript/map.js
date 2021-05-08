{% load i18n %}

let markers, population;
{% if markers %}
    markers = JSON.parse('{{ markers|safe }}');
{% elif population %}
    population = JSON.parse('{{ population|safe }}');
{% endif %}

const translations = {
    'here': "{% trans 'Sie sind hier.' %}",
    'total': "{% trans 'Total: ' %}",
    'members': "{% trans 'Mitglieder: ' %}"
}
let lat, lon;
const input_window = document.getElementById('input-window');
const send_button = document.getElementById('send');
const cancel_button = document.getElementById('cancel');
const input = document.getElementById('input');
input.addEventListener('keyup', function(event) {
    if(event.which == 13) {
        sendMarker();
    }
});
const msg = document.getElementById('django-message');
const msg_text = document.getElementById('loc');

send_button.addEventListener('click', sendMarker);
cancel_button.addEventListener('click', function() {
    input_window.style.display = 'none';
});

var map = L.map('mapid').setView([51.0834196, 10.4234469], 5);

// replace "toner" here with "terrain" or "watercolor" or 
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}).addTo(map);

navigator.geolocation.getCurrentPosition(
    function(position) {
        lat = position.coords.latitude;
        lon = position.coords.longitude;
        var marker = L.marker([lat, lon]).addTo(map);
        marker.bindPopup(translations.here);
        {% if component_index == 3 %}
            //map.setView([lat, lon], 13);
        {% endif %}
    },
    function(error) {
        alert("{% trans 'Ihre Position wird nur für die Zentrierung der Karte und zum Hinzufügen Ihrer eigenen Markierungen genutzt. Ortungsrechte können Sie in den Einstellungen Ihres Gerätes/Browsers ändern.' %}");
    }
);

function addMarker() {
    /*if(lat == undefined) {
        alert("{% trans 'Moment noch! Ihr Standort wird gerade bestimmt.' %}");
        return;
    }*/
    input_window.style.display = 'block';
}

function sendMarker() {
    if(input.value.length < 3) {
        return;
    }
    msg_text.innerHTML = input.value;
    msg.style.display = 'block';
    input_window.style.display = 'none';
    send({'type': 'map', 'lat': lat, 'lon': lon, 'description': input.value});
    input.value = '';
}

if(markers) {
    //[marker.description, marker.latitude, marker.longitude]
    var marker;
    map.setView([markers[0][0], markers[0][1]], 12);
    for(var i = 0; i < markers.length; i++) {
        data = markers[i];
        marker = L.marker([data[1], data[2]]).addTo(map);
        marker.bindPopup(data[0]);
    }
}
else if(population) {
    //[getattr(location, highest_component), total.count(), members.count(), location.latitude, location.longitude]
    var circle, percent;
    const zoom_levels = {
        0: 5, 1: 7, 2: 9
    };
    const radii = {
        0: 50000, 1: 25000, 2: 7000
    };
    map.setView([population[0][0], population[0][1]], zoom_levels[{{ component_index }}]);
    for(var i = 1; i < population.length; i++) {
        data = population[i];
        percent = Math.round(data[2]/data[1]*100);
        if(isNaN(percent)) {
            percent = 0;
        }
        circle = L.circle([data[3], data[4]], {
            color: get_color(percent/100.0),
            fillColor: get_color(percent/100.0),
            radius: radii[{{ component_index }}]
        }).addTo(map);
        circle.bindPopup(data[0]+"<br>"+translations.total+data[1]+"<br>"+translations.members+percent+"%");
    }
}

{% load i18n %}

let markers, population;
var marking = false;
const zoom_levels = {
    0: 5, 1: 7, 2: 9, 3: 12
};
const radii = {
    0: 50000, 1: 25000, 2: 7000
};
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

{% if chosen %}
    location.href = "#mapid";
{% endif %}

function dist(p1, p2) {
    const R = 6371e3; // metres
    const phi1 = p1[0] * Math.PI/180; 
    const phi2 = p2[0] * Math.PI/180;
    const dphi = (p2[0]-p1[0]) * Math.PI/180;
    const ds = (p2[1]-p1[1]) * Math.PI/180;

    const a = Math.sin(dphi/2) * Math.sin(dphi/2) + Math.cos(phi1) * Math.cos(phi2) * Math.sin(ds/2) * Math.sin(ds/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    return R * c; // in metres
}

function markCurrent(callback) {
    if(marking) {
        return;
    }
    marking = true;
    document.getElementById('where').innerHTML = "{% trans 'Standort bestimmen..' %}";
    navigator.geolocation.getCurrentPosition(
        function(position) {
            lat = position.coords.latitude;
            lon = position.coords.longitude;
            var marker = L.marker([lat, lon]).addTo(map);
            marker.bindPopup(translations.here);
            map.setView([lat, lon]);
            document.getElementById('where').innerHTML = "{% trans 'Wo bin ich?' %}";
            if(callback) {
                callback();
            }
            marking = false;
        },
        function(error) {
            alert("{% trans 'Ihre Position wird nur für die Zentrierung der Karte und zum Hinzufügen Ihrer eigenen Markierungen genutzt. Ortungsrechte können Sie in den Einstellungen Ihres Gerätes/Browsers ändern.' %}");
        }
    );
}

function addMarker() {
    if(lat == undefined) {
        markCurrent(addMarker);
        return;
    }
    var d;
    for(var i = 1; i < markers.length; i++) {
        d = dist([lat, lon], [markers[i][1], markers[i][2]]);
        if(d < 10) {
            alert("{% trans 'Diese Markierung ist zu nah an der Markierung ' %}\""+markers[i][0]+"\". {% trans 'Markierungen müssen mindestens 10m auseinanderliegen, hier sind es: ' %} "+Math.round(d)+"m");
            lat = undefined;
            lon = undefined;
            return;
        }
    }
    if(input_window.style.display == 'block') {
        input_window.style.display = 'none';
    }
    else {
        input_window.style.display = 'block';
    }
}

function sendMarker() {
    if(input.value.length < 3 || input.value.length > 100) {
        alert("{% trans 'Erlaubte Beschreibungslänge: 3-100 Zeichen. Derzeit: ' %}"+input.value.length);
        return;
    }
    msg_text.innerHTML = input.value;
    msg.style.display = 'block';
    markers.push([input.value, lat, lon]);
    input_window.style.display = 'none';
    send({'type': 'map', 'lat': lat, 'lon': lon, 'description': input.value, 'activity': {{ activity.id }}});
    input.value = '';
}

if(markers) {
    //[marker.description, marker.latitude, marker.longitude]
    var marker;
    map.setView([markers[0][0], markers[0][1]], 12);
    for(var i = 1; i < markers.length; i++) {
        data = markers[i];
        marker = L.marker([data[1], data[2]]).addTo(map);
        marker.bindPopup(data[0]);
    }
}
else if(population) {
    //[getattr(location, highest_component), total.count(), members.count(), location.latitude, location.longitude]
    var circle, percent;
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

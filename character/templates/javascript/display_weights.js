function displayWeights(activity_weights) {
    console.log(activity_weights);
    var info = document.getElementById('info');
    for(var i = 0; i < letters.length; i++) {
        var list = BIG_FIVE[letters[i]];
        for(var j = 0; j < list.length; j++) {
            var trait = list[j];
            if(activity_weights[trait]) {
                var weight = activity_weights[trait];
                if(typeof(weight) == "string") {
                    weight = JSON.parse(weight);
                }
                info.innerHTML += weight[1]+"x "+categories[trait];
                var span = document.createElement('span');
                span.style.fontSize = "24px";
                span.style.fontWeight = "bold"
                span.innerHTML += (weight[0]? "&uarr;" : "&darr;") + " ";
                info.appendChild(span);
            }
        }
    }
}
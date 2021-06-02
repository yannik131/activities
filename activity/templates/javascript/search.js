let input;

function search() {
    openLink("{{ url }}"+input.value);
}

window.addEventListener('load', function() {
    input = document.getElementById('search-input');

    input.addEventListener('keydown', function(e) {
        if(e.key === 'Enter') {
            e.preventDefault();
            search();
        }
    });
})
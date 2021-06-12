let input;

function search() {
    openLink('', 'search_string', input.value);
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
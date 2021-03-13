function position() {
    const items = document.getElementsByClassName('item');
    const list = document.querySelector('.list');
    list.style.marginLeft = 0+"px";

    var right_edge = -1;
    for(var i = 0; i < items.length; i++) {
        var item = items[i];
        if(item.getBoundingClientRect().right > right_edge) {
            right_edge = item.getBoundingClientRect().right;
        }
        else {
            break;
        }
    }

    const empty_space = list.getBoundingClientRect().right-right_edge;
    list.style.marginLeft = (empty_space/2)+"px";
}

position();

window.addEventListener('resize', position);
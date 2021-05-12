function position() {
    const list = document.querySelector('.list');
    var x = -10;
    var n = 0;
    for(; n < list.children.length; n++) {
        var child_x = list.children[n].getBoundingClientRect().x;
        if(child_x > x) {
            x = child_x;
        }
        else {
            break;
        }
    }
    const wl = list.offsetWidth;
    const wc = list.children[0].offsetWidth+20;
    const empty = wl-n*wc-10;
    list.style.marginLeft = (empty/2)+"px";
}

window.addEventListener('load', position);
function position() {
    const list = document.querySelector('.list');
    if(list.childElementCount == 0) {
        return;
    }
    var x = -10;
    var n = 0;
    for(; n < list.children.length; n++) {
        var child_x = list.children[n].getBoundingClientRect().right;
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
    list.style.paddingLeft = (empty/2)+"px";
    const inner = document.getElementById('inner-div');
    //list.style.marginRight = (inner.offsetWidth-x)+"px";
}

window.addEventListener('load', position);
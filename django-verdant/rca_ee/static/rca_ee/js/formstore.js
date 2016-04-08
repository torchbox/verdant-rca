/*
 * built on:
 * copyright Will Bradley, 2012, released under a CC-BY license
 * retrieved from: https://gist.github.com/zyphlar/3831934
 */

function setCookie(c_name, value, expireminutes) {
    var exdate = new Date();
    exdate.setMinutes(exdate.getMinutes() + expireminutes);
    document.cookie = c_name + "=" + encodeURI(value) +
        ((expireminutes == null) ? "" : ";expires=" + exdate.toUTCString());
}

function getCookie(c_name) {
    if (document.cookie.length > 0) {
        c_start = document.cookie.indexOf(c_name + "=");
        if (c_start != -1) {
            c_start = c_start + c_name.length + 1;
            c_end = document.cookie.indexOf(";", c_start);
            if (c_end == -1) c_end = document.cookie.length;
            return decodeURI(document.cookie.substring(c_start, c_end));
        }
    }
    return "";
}

function storeFormValuesOnSubmit() {
    var form = document.wt_form;
    var json = [];
    for (var i = 0; i < form.length; i++) {
        if (form.elements[i].name && (form.elements[i].checked
            || /select|textarea/i.test(form.elements[i].nodeName)
            || /text|password|email/i.test(form.elements[i].type))) {
            var entry = {};
            entry[form.elements[i].name] = form.elements[i].value;
            json.push(entry);
        }
    }
    setCookie("wt_form", JSON.stringify(json), 44640);
}

function loadFormValues() {
    var cookie = getCookie("wt_form");
    if (cookie.length > 10) {
        var retval = JSON.parse(cookie);
        for (var i = 0; i < retval.length; i++) {
            var obj = retval[i];
            for (var key in obj) {
                // note that checkboxes are not restored correctly, but that is fine for now
                document.wt_form.elements[key].value = obj[key];
            }
        }
    }
}
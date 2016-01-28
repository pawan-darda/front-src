/*
Created on 27 July 2011

@author: Amit.Rathi
*/

function urlDecoder(){
    /* return an serialized object from encoded url string */
    var obj = [];
    var url = window.location.hash.substring(1) == "" ? "" : window.location.href.split("#")[1];
    var params = url.split("?");
    for(var i=0; i<params.length; i++){
        var val = params[i].split("=");
        obj[decodeURIComponent(val.shift())]= decodeURIComponent(val[0]);
    }
    return obj;
};

function urlEncoder(obj){
        /* return an encoded url from a serliazed array */
        var params = [];
        for(var i=0; i<required_anchor.length;i++){
            if (obj[required_anchor[i]] != undefined){
                 params.push(encodeURIComponent(required_anchor[i]) + "=" + encodeURIComponent(obj[required_anchor[i]]));
            }
        };
        return params.join("?")
};

function getAnchorParameter (parameter_string){
    /* Give the value of the parameter requested. If not available then returns False */
    var value = "False";
    var urlData = urlDecoder();
    value = urlData[parameter_string];
    return value;
};

function setAnchorParameter (paramSet){
    /* Set the hash parameter of URL from the key value set of paramSet */
    var obj = urlDecoder();
    for (var key in paramSet) {
       obj[key] = paramSet[key];
    }
    var new_url = urlEncoder (obj);
    window.location.href = "#" + new_url;
};
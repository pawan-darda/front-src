// parseUri 1.2.2
// (c) Steven Levithan <stevenlevithan.com>
// MIT License

function parseUri (str) {
    var    o   = parseUri.options,
        m   = o.parser[o.strictMode ? "strict" : "loose"].exec(str),
        uri = {},
        i   = 14;

    while (i--) uri[o.key[i]] = m[i] || "";

    uri[o.q.name] = {};
    uri[o.key[12]].replace(o.q.parser, function ($0, $1, $2) {
        if ($1) uri[o.q.name][$1] = $2;
    });

    return uri;
};

parseUri.options = {
    strictMode: false,
    key: ["source","protocol","authority","userInfo","user","password","host","port","relative","path","directory","file","query","anchor"],
    q:   {
        name:   "queryKey",
        parser: /(?:^|&)([^&=]*)=?([^&]*)/g
    },
    parser: {
        strict: /^(?:([^:\/?#]+):)?(?:\/\/((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?))?((((?:[^?#\/]*\/)*)([^?#]*))(?:\?([^#]*))?(?:#(.*))?)/,
        loose:  /^(?:(?![^:@]+:[^:@\/]*@)([^:\/?#.]+):)?(?:\/\/)?((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/
    }
};

function escapeHtml (html) {
    var replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;'
    };
    return html.replace(/[&<>]/g, function ($0) {return replacements[$0];});
};
    
function getUrlParameter(parameter){
    /*
    Parse url to return value for the parameter name 
    */
    parameter = parameter.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
    var regexS = "[\\?&]"+parameter+"=([^&#]*)";
    var regex = new RegExp( regexS );
    var results = regex.exec( window.location.href );
    if( results == null )
        return "";
    else
        return results[1];
};

function setUrlParameter(parameter, value) {
    /*
    Set the key value pair for parameter specified.
    */
    var o = parseUri.options;
    var strictMode = $('strictMode').checked;
    o.strictMode = strictMode;
    var vars = window.location.href.split("?");
    try{
        if (vars[1][0] == "&"){
            url = vars[0] + "?" + vars[1].slice(1)
        }
        else{
            url = window.location.href
        }
    }
    catch (err){
        url = window.location.href
    }
    var items = parseUri(url);
    
    var query = items[o.q.name];
    var parameter_flag = 0;
    url_parameters = [];
    for (var p in query) {
        if (query.hasOwnProperty(p)) {
            query[p] = escapeHtml(query[p]);
            if (p==parameter){
                parameter_flag = 1;
                url_parameters.push (p + "=" + value);
            }
            else{
                 url_parameters.push (p + "=" + escapeHtml(query[p]));
            }
        }
    }
    if (parameter_flag == 0)
    {
        url_parameters.push (parameter + "=" + value);
    }
    new_url =  "?" + url_parameters.join("&") + "#" + items.anchor;
    return new_url
};
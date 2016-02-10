# -*- coding: latin-1 -*-
# This module is special module to fix the bug with AR server (not database)
# Right now AR server do not give proper results when LIKE keyword is used
# with parameterized query, hence simple patch is to convert the param query
# into the simple format.
# NOTE: This is not general module it is for special purpose as stated above,
# advice to use too... sparingly.
#
import re

def forname(modname, classname):
    ''' Returns a xyz class of a.b.xyz class format '''    
    mod = __import__(modname)
    components = modname.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)    
    
    classobj = getattr(mod, classname)
    return classobj

def format_paramsql_to_simple(query):
    
    # Getting query and parameters
    qs = str(query)
    params = query._params
    
    # Substitute the parameters to make query simple without external parameters
    for param in params:
        if isinstance(params[param], str):
            qs = qs.replace(':' + param  , '\'' +  params[param] + '\'')
        else:
            qs = qs.replace(':' + param  , params[param])
       
    # Creating the new query object from old one.
    session = query.session
    match = re.search('^.*\'(.*)\.([^\.]*)\'.*$',str(query._entity_zero().type))
        
    _class = forname(match.group(1),match.group(2))
    query =  session.query(_class).from_statement(qs)      
    return query


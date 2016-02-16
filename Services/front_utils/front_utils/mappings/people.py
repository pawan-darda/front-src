from unittest import TestCase
import codecs

class PeopleMapper (object):
    def __init__ (self, data):
        lines = data.readlines ()[1:] # not title
        while not len (lines [-1].strip ()) : #not last empty lines
            lines = lines [:-1]
        
        self.values = [[v.strip().strip ('"').lower() for v in l.split (",")] for l in lines]
        self.fromlogin = dict ([(v[0], 
                                dict (fullname=v[1], email=v[2])) for v in self.values])
        self.fromfullname = dict ([(v[1], 
                                dict (login=v[0], email=v[2])) for v in self.values])
        
    def login2email (self, login):
        return self.fromlogin [login.lower()]["email"]
    
    def login2fullname (self, login):
        return self.fromlogin [login.lower()]["fullname"]

mapper = None

def login2email (login):
    global mapper
    if not mapper : mapper = PeopleMapper (codecs.open (r"\\appsto03.internal.sungard.corp\scripts\users.csv", "r", "ISO-8859-1"))
    return mapper.fromlogin [login.lower()]["email"]

def login2fullname (login):
    global mapper
    if not mapper : mapper = PeopleMapper (codecs.open (r"\\appsto03.internal.sungard.corp\scripts\users.csv", "r", "ISO-8859-1"))
    return mapper.fromlogin [login.lower()]["fullname"]



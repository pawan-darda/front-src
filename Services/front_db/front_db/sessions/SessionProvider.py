'''
Created on 23 sep 2011

@author: laurent.ploix
'''

#Here create a session provider with the with statement
from sqlalchemy.orm import sessionmaker

class RollbackException (Exception):
    pass

class SessionWrapper (object):
    def __init__ (self, session_class):
        self.__session_class = session_class # the class that will help us create the actual session
        self.session = None
        
    def __getattr__ (self, attr):
        """The object reacts as a session when it has been opened"""
        if self.session is None : raise Exception ("Use the with statement to start the session first.") 
        return getattr (self.session, attr)
    
    def __enter__ (self): 
        """The object is meant to be used with the with statement"""
        self.session = self.__session_class ()
        return self
    
    def __exit__ (self, type, value, traceback):
        """The session is commited if no exception is raised, otherwise it is rolled back.
        The RollbackException makes a rollback but is swallowed (ie not propagated)"""
        try :
            if value is not None:
                self.session.rollback ()
                if type == RollbackException:
                    return True 
            else :
                self.session.commit ()
        finally :
            self.session.close ()
            self.session = None

class SessionProvider (object):
    def __init__ (self, engine):
        self.__Session = sessionmaker(bind=engine) 
        
    def get_session (self):
         return SessionWrapper (self.__Session)

"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# an Engine, which the Session will use for connection
# resources
some_engine = create_engine('postgresql://scott:tiger@localhost/')

# create a configured "Session" class
Session = sessionmaker(bind=some_engine)

# create a Session
session = Session()

# work with sess
myobject = MyObject('foo', 'bar')
session.add(myobject)
session.commit()
"""
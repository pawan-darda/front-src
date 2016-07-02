'''
Created on 27 sep 2011

@author: laurent.ploix
'''
from sqlalchemy import create_engine
import unittest
from front_db.sessions import SessionProvider, RollbackException

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from decimal import DivisionByZero

MY_TABLE = 'a_table'
Base = declarative_base()

class MyTable (Base):
    __tablename__ = MY_TABLE
    id = Column(Integer, primary_key = True)
    name = Column(String(255), nullable = False, unique = True)


class DbTestCase(unittest.TestCase):
    
    def setUp (self):
        engine = create_engine('sqlite:///:memory:', echo=False)
        self.session_provider = SessionProvider (engine)
        metadata = Base.metadata
        metadata.create_all(engine)

    def test_session_wrapper (self):
        with self.session_provider.get_session () as session :
            o = MyTable (name="pipo")
            session.add (o)
        with self.session_provider.get_session () as session :
            q = session.query (MyTable)
            self.assertEquals (1, q.count())
            
    def test_session_wrapper_with_error (self):
        def div ():
            with self.session_provider.get_session () as session :
                1/0
        
        self.assertRaises (ZeroDivisionError, div)
        
    def test_session_wrapper_with_rollback (self):
        def div ():
            with self.session_provider.get_session () as session :
                o = MyTable (name="pipo")
                session.add (o)
                raise RollbackException ()
        
        div ()
        with self.session_provider.get_session () as session :
            self.assertEquals (0, session.query (MyTable).count())
            
            
            
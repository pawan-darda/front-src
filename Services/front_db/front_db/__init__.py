import asgard_db, fast_db, magellan_db, sessions

# Following code is temp fix for the sqlalchemy bug to enable the hints.
import sqlalchemy

if sqlalchemy.__version__ in ['0.7.2', '0.7.4'] :

    from sqlalchemy.dialects.mssql import base
    def get_from_hint_text_front(self, table, text):
            return text
    base.MSSQLCompiler.get_from_hint_text = get_from_hint_text_front

else:
    raise Exception ("Please check if the sqla version we have contains the with_hint patch already") 
# Temp fix code is over. 


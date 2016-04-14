'''
Created on 17 maj 2010

@author: Laurent.Ploix
'''
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
# from sqlalchemy.interfaces import PoolListener
import sqlalchemy
from DjangoWebSite.settings import DEBUG, FAST_SERVER, FAST_SERVER_DEBUG
# from front_db.magellan_db import mag_db_wrapper
from front_db.sessions import SessionProvider

__session = None
__fast_session = None
__read_uncommitted_session = None
__read_uncommited_fast_test_session = None
__read_uncommited_cvc_session = None
__read_uncommited_mag_session = None
__write_commited_mag_session = None

asg_prod_uri = "mssql://magellan:magellan@kantele.tqa.corp/ASG_REP"
asg_test_uri = "mssql://magellan:magellan@kantele.tqa.corp/ASG_REP"

cvc_prod_uri = "mssql://cvc:foobar@kantele.tqa.corp/CVC"
cvc_test_uri = "mssql://cvc:foobar@kantele.tqa.corp/CVC"

fast_prod_uri = "mssql://Magellan:Magellan@%s/ARSystem"%FAST_SERVER
fast_test_uri = "mssql://Magellan:Magellan@%s/ARSystem"%FAST_SERVER_DEBUG

mag_prod_read_uri = "mssql://Mgl_read:magellanread@kantele.tqa.corp/MAGELLAN"
mag_prod_write_uri = "mssql://Mgl_Write:magellan@kantele.tqa.corp/MAGELLAN"
mag_test_read_uri = "mssql://Mgl_read:magellanread@kantele.tqa.corp/MAGELLAN"
mag_test_write_uri = "mssql://Mgl_Write:magellan@kantele.tqa.corp/MAGELLAN"
pool_size = 10

# Defining the listener which will get call every time engine connected to the# actual database using DB api.
class read_uc_listener(sqlalchemy.interfaces.PoolListener):        
    def connect(self, dbapi_con, con_record):
        dbapi_con.execute("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")        
ruc_listener = read_uc_listener()

asgard_read_uncommited_session_provider = SessionProvider (create_engine(asg_test_uri if DEBUG else asg_prod_uri, 
                                                       poolclass=sqlalchemy.pool.QueuePool, 
                                                       listeners=[ruc_listener], 
                                                       echo=False, 
                                                       pool_size=20,
                                                       connect_args={'unicode_results': True}))

asgard_read_commited_session_provider = SessionProvider (create_engine(asg_test_uri if DEBUG else asg_prod_uri, 
                                                       poolclass=sqlalchemy.pool.QueuePool, 
                                                       echo=False, 
                                                       pool_size=20,
                                                       connect_args={'unicode_results': True}))


fast_read_uncommited_session_provider = SessionProvider (create_engine(fast_test_uri if DEBUG else fast_prod_uri, 
                                poolclass=sqlalchemy.pool.QueuePool, 
                                listeners=[ruc_listener], 
                                echo=False, 
                                pool_size=20,
                                connect_args={'unicode_results': True}))

magellan_read_uncommited_session_provider = SessionProvider (create_engine(mag_test_read_uri if DEBUG else mag_prod_read_uri,
                               poolclass=sqlalchemy.pool.QueuePool, 
                               echo=False, 
                               pool_size=20,
                               connect_args={'unicode_results': True}))

magellan_write_session_provider = SessionProvider (create_engine(mag_test_write_uri if DEBUG else mag_prod_write_uri,                              
                              poolclass=sqlalchemy.pool.QueuePool, 
                              echo=False, 
                              pool_size=20,
                              connect_args={'unicode_results': True}))

cvc_read_uncommitted_db_session_provider = SessionProvider (create_engine( cvc_test_uri if DEBUG else cvc_prod_uri, 
                              poolclass=sqlalchemy.pool.QueuePool, 
                              echo=False, 
                              pool_size=20,
                              listeners=[ruc_listener], 
                              connect_args={'unicode_results': True}))


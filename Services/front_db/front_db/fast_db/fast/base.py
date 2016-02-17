# -*- coding: latin-1 -*-
#
# This is class overriding the base (compiler) for AR driver not doing much 
# at this moment just formatting the sql as per AR driver specification.
# However, there are several place holder are kept if we need more functionality
# for AR driver.
#

from sqlalchemy.sql import  compiler                          
from sqlalchemy.engine import default,  reflection

# Over riding the NE operator for the fast
compiler.OPERATORS.__setitem__(compiler.operators.ne, '<>')

# These are place holder if we need to add something specific to AR drivers
class FASTTypeCompiler(compiler.GenericTypeCompiler):   
    pass

# These are place holder if we need to add something specific to AR drivers
class FASTExecutionContext(default.DefaultExecutionContext): 
    pass

# These are place holder if we need to add something specific to AR drivers
class FASTSQLCompiler(compiler.SQLCompiler):
    pass

# These are place holder if we need to add something specific to AR drivers
class FASTSQLStrictCompiler(FASTSQLCompiler):
    pass

# These are place holder if we need to add something specific to AR drivers
class FASTDDLCompiler(compiler.DDLCompiler): 
    pass

class FASTIdentifierPreparer(compiler.IdentifierPreparer): 
    # Converting [] to "" as per AR driver specs.
    def __init__(self, dialect):
        super(FASTIdentifierPreparer, self).__init__(dialect, initial_quote='"', 
                                                   final_quote='"')

class FASTDialect(default.DefaultDialect):
    name = 'fast'
    supports_default_values = True
    supports_empty_insert = False
    execution_ctx_cls = FASTExecutionContext
    use_scope_identity = True
    max_identifier_length = 128
    schema_name = "dbo"
    
    supports_native_boolean = False
    supports_unicode_binds = True
    postfetch_lastrowid = True
    server_version_info = ()
    
    statement_compiler = FASTSQLCompiler
    ddl_compiler = FASTDDLCompiler
    type_compiler = FASTTypeCompiler
    preparer = FASTIdentifierPreparer

    def __init__(self,
                 query_timeout=None,
                 use_scope_identity=True,
                 max_identifier_length=None,
                 schema_name=u"dbo", **opts):
        self.query_timeout = int(query_timeout or 0)
        self.schema_name = schema_name

        self.use_scope_identity = use_scope_identity
        self.max_identifier_length = int(max_identifier_length or 0) or \
                self.max_identifier_length
        super(FASTDialect, self).__init__(**opts)

    def do_release_savepoint(self, connection, name): pass
    
    def initialize(self, connection): pass
        
    def _get_default_schema_name(self, connection): pass

    @reflection.cache
    def get_schema_names(self, connection, **kw): pass


# -*- coding: latin-1 -*-

""" This contains a sql alchemy mapper to the CVC database.
WARNING: on 2011-03-03, this is NOT the mapper that is used primarily to map the database
Look into database.py for that purpose instead.
"""
INS_UPDATE_TIME_ID = 'Instrument Update Time'


from sqlalchemy.orm.interfaces import MapperExtension, EXT_CONTINUE #, EXT_STOP
from front_utils.versions.prime_versions import PrimeVersion

class CvcDbAccessException (Exception):
    pass

class CvcMapperExtension (MapperExtension):
    """
    A class used to have hooks when the session tries to access the ojects/database.
    This is mainly used to prevent some actions. It could be used to implement faster queries too.  
    """
    def before_delete(self, mapper, connection, instance):
        if instance.__class__ == Report and len (instance.inherited_reports) <> 0 :
            raise CvcDbAccessException ("Can't delete a report which has a father.") 
            # return EXT_STOP # does not work
        return EXT_CONTINUE 

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy

Base = declarative_base()

class Build (Base):
    __tablename__ = 'build'
    id = Column(Integer, primary_key=True)
    platform = Column(String(10))
    platform_bits = Column(String(10))
    platform_variant = Column(String(50))
    exe_name = Column(String(20))
    exe_bits = Column(String(10))
    exe_version = Column(String(10))
    exe_branch = Column(String(10))
    exe_full_version = Column(String(100))
    exe_build = Column(Integer)
    reports = None

    def __repr__ (self):
        s = ", ". join ([str(k) + "=" + repr (getattr (self, k)) for k in ("platform",
                                                                           "platform_bits",
                                                                           "platform_variant",
                                                                           "exe_name",
                                                                           "exe_bits",
                                                                           "exe_version",
                                                                           "exe_branch",
                                                                           "exe_full_version",
                                                                           "exe_build"
                                                                           )])
        return "Build (" + s + ")"
    
class Setup (Base):
    __tablename__ = 'setup'
    id = Column(Integer, primary_key=True)
    taskdef = Column(String(10))
    reports = None
    
    def __repr__ (self):
        return "Setup (taskdef=%r)"%self.taskdef

class ColumnDefinition (Base):
    __tablename__ = "column_definition"
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    group_name = Column(String(200))
    subordinal = Column(Integer)
    prettyname = Column(String)
    reports = None
    result_associations = None
    rows_reports_association = None  
    reports = association_proxy('columns_reports_association', 'report')

class RowDefinition (Base):
    __tablename__ = "row_definition"
    id = Column(Integer, primary_key=True)
    parent_id = None
    name = Column(String(200))
    fullname = Column(String(1024))
    subordinal = Column(Integer)
    children = None
    
RowDefinition.parent_id = Column ('parent_id', ForeignKey(RowDefinition.id))
RowDefinition.parent = relationship (RowDefinition, backref=backref('children',
                                                 cascade="all",
                                                 lazy='lazy'), remote_side=[RowDefinition.id])

"""relationship(RowDefinition, backref=backref('children',
                                                 cascade="all, delete, delete-orphan",
                                                 lazy='lazy'))"""

class RowInstance (Base):
    __tablename__ = "row_instance"
    id = Column(Integer, primary_key=True)
    hash_value = Column(String(50))
    last_modified = Column(String(50))
    row_definition_id = Column ('row_definition_id', ForeignKey(RowDefinition.id))
    row_definition = relationship(RowDefinition, backref=backref('row_instances',
                                                 cascade="all, delete, delete-orphan",
                                                 lazy='dynamic'))
    reports = None
    result_associations = None
    rows_reports_association = None  
    reports = association_proxy('rows_reports_association', 'report')

    #results = association_proxy('result_associations', 'result')
    #column_definitions = association_proxy('result_associations', 'column_definition')

class Report (Base):
    __tablename__ = 'report'
    __mapper_args__ = {'extension': CvcMapperExtension()}
    
    id = Column(Integer, primary_key=True)
    base_report_id = None
    #inherited_reports = None
    time_elapsed = Column(Float)
    hash_value = Column(String(50))
    memory_usage = Column(Float)
    db_version = Column(String(80))
    failure = Column(Boolean, nullable=False)
    build_id = Column ('build_id', ForeignKey(Build.id), nullable=False)
    build = relationship(Build, backref=backref('reports',
                                                    cascade="all, delete",
                                                    lazy='dynamic'))
    
    setup_id = Column ('setup_id', ForeignKey(Setup.id), nullable=False)
    setup = relationship(Setup, backref=backref('reports',
                                                    cascade="all, delete",
                                                    lazy='dynamic'))
      
    row_instances = association_proxy('rows_reports_association', 'row_instance')
    column_definitions = association_proxy('columns_reports_association', 'column_definition')
    rows_reports_association = None  
    
    @staticmethod
    def from_report (report, platform, platform_variant, platform_bits, exe_full_version, exe_bits, exe_name, taskdef, session):
        prime_version = PrimeVersion (exe_full_version)
        q = session.query (Build).filter (Build.platform == platform)
        q = q.filter (Build.platform_variant == platform_variant)
        q = q.filter (Build.exe_name == exe_name)
        q = q.filter (Build.platform_bits == platform_bits)
        q = q.filter (Build.exe_full_version == exe_full_version) 
        q = q.filter (Build.exe_bits == exe_bits) 
        q = q.filter (Build.exe_version == "%s.%s" % (prime_version.main, prime_version.sub))
        q = q.filter (Build.exe_branch == prime_version.abn)
        q = q.filter (Build.exe_build == prime_version.bn)
        try :
            build = q.all()[0]
        except IndexError:
            build = Build (platform = platform,
                           platform_variant = platform_variant,
                           exe_name = exe_name,
                           platform_bits = platform_bits,
                           exe_full_version = exe_full_version,
                           exe_bits = exe_bits,
                           exe_version = "%s.%s" % (prime_version.main, prime_version.sub),
                           exe_branch = prime_version.abn,
                           exe_build = prime_version.bn)
            #session.add (build)
            #session.commit ()
        
        q_setup = session.query (Setup).filter_by (taskdef = taskdef) 
        try :
            setup = q_setup.all()[0]
        except IndexError:
            setup = Setup (taskdef = taskdef)
            #session.add (setup)
            #session.commit()
        # First, point to the right version
        
        db_report= Report (memory_usage=report.memory_usage,
                        time_elapsed=report.time_elapsed,
                        db_version=report.db_version,
                        failure=report.failure,
                        setup = setup,
                        build=build)
        session.add (db_report)
        # Here we need more values of course
        
        # Here we implement a slow insert. It would need a much faster one of course.
        position_of_ins_update_time = -1
        columns = []
        for i, col in enumerate(report.columns):
            try :
                db_col = session.query (ColumnDefinition).filter (ColumnDefinition.name == col.name)\
                                                .filter (ColumnDefinition.group_name == col.group)\
                                                .filter (ColumnDefinition.subordinal==col.subordinal).all()[0]
            except IndexError :
                db_col = ColumnDefinition (name=col.name, 
                                           group_name=col.group,
                                           prettyname = col.prettyname, 
                                           subordinal=col.subordinal)
                
            session.add (ReportColumnAssociation (report=db_report, column_definition = db_col))
            #db_report.column_definitions.append (db_col)
#                session.add (db_col)

            columns.append(db_col)
            if col.name == INS_UPDATE_TIME_ID:
                position_of_ins_update_time = i

#        self._store_rows(prime_report.rows, prime_report.columns,
#                         column_ids, db_report,
#                         position_of_ins_update_time)
            
        
        session.commit()

Report.base_report_id = Column ('base_report_id', ForeignKey(Report.id))
Report.base_report = relationship (Report, backref="inherited_reports", remote_side=[Report.id])

class ReportComparator (object):
    def __init__ (self, report_1, report_2):
        self.report_1 = report_1
        self.report_2 = report_2

class ReportColumnAssociation (Base):
    __tablename__ = 'report_x_column_definition'
    report_id = Column (Integer, ForeignKey(Report.id), primary_key=True)
    column_definition_id = Column (Integer, ForeignKey(ColumnDefinition.id), primary_key=True)
    report = relationship(Report, backref=backref('columns_reports_association',
                                                    cascade="all, delete, delete-orphan",
                                                    lazy='dynamic'))
    column_definition = relationship(ColumnDefinition, backref=backref('columns_reports_association',
                                                    cascade="all, delete, delete-orphan",
                                                    lazy='dynamic'))

class ReportRowAssociation (Base):
    __tablename__ = 'report_x_row_instance'
    report_id = Column (Integer, ForeignKey(Report.id), primary_key=True)
    row_instance_id = Column (Integer, ForeignKey(RowInstance.id), primary_key=True)
    report = relationship(Report, backref=backref('rows_reports_association',
                                                    cascade="all, delete",
                                                    lazy='dynamic'))
    row_instance = relationship(RowInstance, backref=backref('rows_reports_association',
                                                    cascade="all, delete",
                                                    lazy='dynamic'))
    
class Result (Base):
    __tablename__ = 'result'
    id = Column(Integer, primary_key=True)
    value_number = Column(Float)
    result_associations = None
    value_string = Column(String (100))
    #row_instances = association_proxy('result_associations', 'row_instance')
    #column_definitions = association_proxy('result_associations', 'column_definition')
    
    def __repr__ (self):
        return 'Result(value_number=%(value_number)f, value_string=%(value_string)s)' % self.__dict__ 
     
class RowColResultAssociation (Base):
    __tablename__ = 'row_ins_x_col_def_x_result'
    row_instance_id = Column(Integer, ForeignKey(RowInstance.id), primary_key=True)
    column_id = Column(Integer, ForeignKey(ColumnDefinition.id), primary_key=True)
    result_id = Column(Integer, ForeignKey(Result.id), nullable=False)
    result = relationship(Result, backref=backref('result_associations',
                                                    lazy='dynamic'))
    row_instance = relationship(RowInstance, backref=backref('result_associations',
                                                    lazy='dynamic'))
    column_definition = relationship(ColumnDefinition, backref=backref('result_associations',
                                                    lazy='dynamic'))
    

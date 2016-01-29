'''
Created on 11 apr 2011

@author: Laurent.Ploix
'''
from front_db.cvc_db import cvc_wrapper

try :
    import unittest2 as unittest
except ImportError:
    import unittest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from front_db.cvc_db.cvc_wrapper import Base, Build, Setup, Report, RowDefinition, \
    CvcDbAccessException, ColumnDefinition, RowInstance, ReportColumnAssociation, ReportRowAssociation,\
    Result, RowColResultAssociation, ReportComparator
#import sqlalchemy
import gzip
import cPickle as pickle
import os


class DbTestCase(unittest.TestCase):
    """
    Base class for all in memory database tests
    """
    def setUp (self):
        engine = create_engine('sqlite:///:memory:', echo=False)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        self.metadata = Base.metadata
        self.metadata.create_all(engine)

    def tearDown (self):
        self.session.close()

class TestSetupStructure (DbTestCase):
    """
    Basic tests for the Setup table mapper: creation, deletion, relations
    """
    def test_setup_creation (self):
        setup = Setup(taskdef="my description")
        self.assertEquals (0, self.session.query (Setup).count())
        self.session.add (setup)
        self.session.commit ()
        self.assertEquals (setup, self.session.query (Setup).one())
        self.assertEquals (1, self.session.query (Setup).count())
        self.assertEquals ([], setup.reports.all())

    def test_setup_delete (self):
        setup = Setup(taskdef="my description")
        self.session.add (setup)
        self.session.commit ()
        self.assertEquals (1, self.session.query (Setup).count())
        self.session.delete (setup)
        self.session.commit ()
        self.assertEquals (0, self.session.query (Setup).count())
        
    def test_setup_delete_deletes_reports (self):
        setup = Setup(taskdef="my description")
        setup.reports=[Report(failure=True, build=Build()), Report(failure=False, build=Build())]
        self.session.add (setup)
        self.session.commit ()
        self.assertEquals (1, self.session.query (Setup).count())
        self.assertEquals (2, self.session.query (Report).count())
        self.session.delete (setup)
        self.session.commit ()
        self.assertEquals (0, self.session.query (Setup).count())
        self.assertEquals (0, self.session.query (Report).count())
        
class TestBuildStructure (DbTestCase):
    """
    Basic tests for the Build table mapper: creation, deletion, relations
    """
    def test_build_creation_with_all_args (self):
        build = Build(    platform = "a platform",
                          platform_bits = "365",
                          platform_variant = "a variant",
                          exe_name = "a name",
                          exe_bits = "an exe bit",
                          exe_version = "a version",
                          exe_branch = "a branch",
                          exe_full_version = "a full version",
                          exe_build = 12541245)
        self.assertEquals (0, self.session.query (Build).count())
        self.session.add (build)
        self.session.commit ()
        self.assertEquals ([], build.reports.all())
        self.assertEquals (build, self.session.query (Build).one())
        self.assertEquals (1, self.session.query (Build).count())

    def test_build_delete (self):
        build = Build()
        self.session.add (build)
        self.session.commit ()
        self.assertEquals (1, self.session.query (Build).count())
        self.session.delete (build)
        self.session.commit ()
        self.assertEquals (0, self.session.query (Build).count())
        
    def test_build_delete_deletes_reports (self):
        build = Build()
        build.reports = [Report(setup=Setup(), failure=True), 
                         Report(setup=Setup(), failure=False)]
        self.session.add (build)
        self.session.commit ()
        self.assertEquals (1, self.session.query (Build).count())
        self.assertEquals (2, self.session.query (Report).count())
        self.session.delete (build)
        self.session.commit ()
        self.assertEquals (0, self.session.query (Build).count())
        self.assertEquals (0, self.session.query (Report).count())
        
class TestReportComparator (DbTestCase):
    def test_instanciate_comparator (self):
        report_1 = Report(build = Build (), 
                        setup=Setup(),
                        time_elapsed=2.1,
                        memory_usage=4.0,
                        db_version = "a version",
                        failure = False,
                        )
        report_2 = Report(build = Build (), 
                        setup=Setup(),
                        time_elapsed=1.0,
                        memory_usage=5.5,
                        db_version = "a version",
                        failure = False,
                        )
        ReportComparator (report_1, report_2)

class TestReportStructure (DbTestCase):
    """
    Basic tests for the Report table mapper: creation, deletion, relations
    """
    def test_report_creation (self):
        report = Report(build = Build (), 
                        setup=Setup(),
                        time_elapsed=1.234,
                        memory_usage=4.5678,
                        db_version = "a version",
                        failure = False,
                        )
        self.assertEquals (0, self.session.query (Build).count())
        self.assertEquals (0, self.session.query (Build).count()) # No build yet
        self.assertEquals (0, self.session.query (Setup).count()) # No setup yet
        self.session.add (report)
        self.session.commit ()
        self.assertEquals (report, self.session.query (Report).one())
        self.assertEquals (1, self.session.query (Report).count())
        self.assertEquals (1, self.session.query (Build).count())
        self.assertEquals (1, self.session.query (Setup).count())
        self.assertEquals (None, report.base_report)
        
    def test_cant_create_without_build (self):
        report = Report(build = None, 
                        setup=Setup(),
                        time_elapsed=1.234,
                        memory_usage=4.5678,
                        db_version = "a version",
                        failure = False,
                        )
        self.session.add (report)
        self.assertRaises(Exception, self.session.commit)

    def test_cant_create_without_setup (self):
        report = Report(build = Build(), 
                        setup=None,
                        time_elapsed=1.234,
                        memory_usage=4.5678,
                        db_version = "a version",
                        failure = False,
                        )
        self.session.add (report)
        self.assertRaises(Exception, self.session.commit)

    def test_cant_create_without_failure (self):
        report = Report(build = Build(), 
                        setup=Setup(),
                        time_elapsed=1.234,
                        memory_usage=4.5678,
                        db_version = "a version",
                        failure = None,
                        )
        self.session.add (report)
        self.assertRaises(Exception, self.session.commit)

    def test_report_creation_with_base_report (self):
        base_report = Report(build = Build (), 
                        setup=Setup(),
                        time_elapsed=1.234,
                        memory_usage=4.5678,
                        db_version = "a version",
                        failure = False,
                        )
        report = Report(build = Build (), 
                        setup=Setup(),
                        time_elapsed=1.0,
                        memory_usage=4.0,
                        db_version = "a version",
                        failure = True,
                        base_report=base_report
                        )
        self.assertEquals (0, self.session.query (Report).count())
        self.session.add (report)
        self.assertEquals (2, self.session.query (Report).count())
        self.assertEquals (base_report, report.base_report)
                
    def test_delete_base_report (self):
        base_report = Report(build = Build (), 
                        setup=Setup(),
                        time_elapsed=1.234,
                        memory_usage=4.5678,
                        db_version = "a version",
                        failure = False,
                        )
        report = Report(build = Build (), 
                        setup=Setup(),
                        time_elapsed=1.0,
                        memory_usage=4.0,
                        db_version = "a version",
                        failure = True,
                        base_report=base_report
                        )
        self.assertEquals (0, self.session.query (Report).count())
        self.session.add (report)
        self.assertEquals (2, self.session.query (Report).count())
        self.assertEquals (base_report, report.base_report)
        self.assertRaises(Exception, self.session.delete, (base_report,)) # Can't delete the father of reports
        self.assertEquals (2, self.session.query (Report).count())
                
    def test_2_reports_creation_with_same_builds (self):
        build = Build()
        report_1 = Report(build = build, 
                        setup=Setup(),
                        failure = False,
                        )
        report_2 = Report(build = build, 
                        setup=Setup(),
                        failure = False,
                        )
        self.session.add (report_1)
        self.session.add (report_2)
        self.session.commit ()
        self.assertEquals (2, self.session.query (Report).count())
        self.assertEquals (1, self.session.query (Build).count())
        self.assertEquals (2, self.session.query (Setup).count())

    def test_report_delete (self):
        report = Report(build = Build (), 
                        setup=Setup(),
                        time_elapsed=1.234,
                        memory_usage=4.5678,
                        db_version = "a version",
                        failure = False,
                        )
        self.session.add (report)
        self.session.commit ()
        self.assertEquals (1, self.session.query (Report).count())
        self.session.delete (report)
        self.session.commit ()
        self.assertEquals (0, self.session.query (Report).count())
        self.assertEquals (1, self.session.query (Build).count()) # We keep the build for later use, just in case there is a need for it
        self.assertEquals (1, self.session.query (Setup).count()) # We keep the setup for later use, just in case there is a need for it

class TestColumnDefinitionStructure (DbTestCase):
    """
    Basic tests for the Report table mapper: creation, deletion, relations
    """
    def test_coldef_creation (self):
        coldef = ColumnDefinition (name="foo",
                                subordinal = 1,
                                prettyname="bar", 
                                group_name="arg") 
        self.assertEquals (0, self.session.query (ColumnDefinition).count())
        self.session.add (coldef)
        self.session.commit ()
        self.assertEquals (coldef, self.session.query (ColumnDefinition).one())
        self.assertEquals (1, self.session.query (ColumnDefinition).count())
        self.assertEquals ([], coldef.reports)
        self.assertEquals ([], coldef.result_associations.all())

    def test_coldef_deletion (self):
        coldef = ColumnDefinition (name="foo",
                                subordinal = 1,
                                prettyname="bar", 
                                group_name="arg") 
        self.session.add (coldef)
        self.session.commit ()
        self.assertEquals (coldef, self.session.query (ColumnDefinition).one())
        self.session.delete (coldef)
        self.session.commit ()
        self.assertEquals (0, self.session.query (ColumnDefinition).count())

class TestRowDefinitionStructure (DbTestCase):
    """
    Basic tests for the Report table mapper: creation, deletion, relations
    """
    def test_rowdef_creation (self):
        rowdef = RowDefinition (parent = None, 
                                name="foo",
                                subordinal = 1,
                                fullname="bar") 
        self.assertEquals (0, self.session.query (RowDefinition).count())
        self.session.add (rowdef)
        self.session.commit ()
        self.assertEquals (rowdef, self.session.query (RowDefinition).one())
        self.assertEquals (1, self.session.query (RowDefinition).count())
        self.assertEquals ([], rowdef.row_instances.all())

    def test_rowdef_creation_with_parent (self):
        rowdef = RowDefinition (parent = RowDefinition(name="arg"), 
                                name="foo",
                                subordinal = 1,
                                fullname="bar") 
        self.assertEquals (0, self.session.query (RowDefinition).count())
        self.session.add (rowdef)
        self.session.commit ()
        self.assertEquals (2, self.session.query (RowDefinition).count())
        self.assertEquals ("arg", rowdef.parent.name)
        self.assertEquals ([rowdef], rowdef.parent.children)
        
    def test_rowdef_creation_delete_parent (self):
        parent = RowDefinition(name="arg")
        rowdef = RowDefinition (parent = parent, 
                                name="foo",
                                subordinal = 1,
                                fullname="bar") 
        self.assertEquals (0, self.session.query (RowDefinition).count())
        self.session.add (rowdef)
        self.session.commit ()
        self.assertEquals (2, self.session.query (RowDefinition).count())
        self.session.delete (parent)
        self.session.commit ()
        self.assertEquals (0, self.session.query (RowDefinition).count())
        
    def test_rowdef_delete_deletes_row_instances (self):
        rowdef = RowDefinition (parent = None, 
                                name="foo",
                                subordinal = 1,
                                fullname="bar")
        RowInstance (row_definition = rowdef) 
        RowInstance (row_definition = rowdef) 
        self.assertEquals (0, self.session.query (RowDefinition).count())
        self.session.add (rowdef)
        self.session.commit ()
        self.assertEquals (1, self.session.query (RowDefinition).count())
        self.assertEquals (2, self.session.query (RowInstance).count())
        self.session.delete (rowdef)
        self.session.commit ()
        self.assertEquals (0, self.session.query (RowDefinition).count())
        self.assertEquals (0, self.session.query (RowInstance).count())
        
    def test_rowdef_creation_delete_child (self):
        parent = RowDefinition(name="arg")
        rowdef = RowDefinition (parent = parent, 
                                name="foo",
                                subordinal = 1,
                                fullname="bar") 
        self.assertEquals (0, self.session.query (RowDefinition).count())
        self.session.add (rowdef)
        self.session.commit ()
        self.assertEquals (2, self.session.query (RowDefinition).count())
        self.session.delete (rowdef)
        self.session.commit ()
        self.assertEquals (1, self.session.query (RowDefinition).count())
        
class TestRowInstanceStructure (DbTestCase):
    def test_rowinst_creation (self):
        import datetime
        instance = RowInstance (
                                last_modified = datetime.datetime.now(),
                                hash_value="titi",
                                row_definition = RowDefinition(name="foo")
                                ) 
        self.assertEquals (0, self.session.query (RowInstance).count())
        self.session.add (instance)
        self.session.commit ()
        self.assertEquals (instance, self.session.query (RowInstance).one())
        self.assertEquals ("foo", instance.row_definition.name)
        self.assertEquals ([], instance.reports)
        self.assertEquals ([], instance.result_associations.all())
        self.assertEquals ([], instance.rows_reports_association.all())
        
class TestReportColumnAssociationStructure (DbTestCase):
    def test_association_creation (self):
        assoc = ReportColumnAssociation (column_definition = ColumnDefinition(),
                                         report = Report(build=Build(), failure=True, setup=Setup()))
        self.session.add (assoc)
        self.session.commit()
        self.assertEquals (1, self.session.query (ReportColumnAssociation).count())
        self.assertEquals (1, self.session.query (Report).count())
        self.assertEquals (1, self.session.query (ColumnDefinition).count())
        
    def test_delete_report (self):
        assoc = ReportColumnAssociation (column_definition = ColumnDefinition(),
                                         report = Report(build=Build(), failure=True, setup=Setup()))
        self.session.add (assoc)
        self.session.commit()
        self.session.delete (assoc.report)
        self.session.commit()
        self.assertEquals (0, self.session.query (Report).count())
        self.assertEquals (0, self.session.query (ReportColumnAssociation).count())
        self.assertEquals (1, self.session.query (ColumnDefinition).count()) # We keep the column definition
        
    def test_delete_coldef (self):
        assoc = ReportColumnAssociation (column_definition = ColumnDefinition(),
                                         report = Report(build=Build(), failure=True, setup=Setup()))
        self.session.add (assoc)
        self.session.commit()
        self.session.delete (assoc.column_definition)
        self.session.commit()
        self.assertEquals (1, self.session.query (Report).count()) # we keep the report
        self.assertEquals (0, self.session.query (ReportColumnAssociation).count())
        self.assertEquals (0, self.session.query (ColumnDefinition).count()) 
        
    def test_delete_assoc (self):
        assoc = ReportColumnAssociation (column_definition = ColumnDefinition(),
                                         report = Report(build=Build(), failure=True, setup=Setup()))
        self.session.add (assoc)
        self.session.commit()
        self.session.delete (assoc)
        self.session.commit()
        self.assertEquals (1, self.session.query (Report).count()) # We keep the report
        self.assertEquals (0, self.session.query (ReportColumnAssociation).count())
        self.assertEquals (1, self.session.query (ColumnDefinition).count()) # We keep the column definition
        
class TestReportRowAssociationStructure (DbTestCase):
    def test_association_creation (self):
        assoc = ReportRowAssociation (row_instance = RowInstance (row_definition = RowDefinition()),
                                         report = Report(build=Build(), failure=True, setup=Setup()))
        self.session.add (assoc)
        self.session.commit()
        self.assertEquals (1, self.session.query (ReportRowAssociation).count())
        self.assertEquals (1, self.session.query (Report).count())
        self.assertEquals (1, self.session.query (RowInstance).count())
        
    def test_delete_report (self):
        assoc = ReportRowAssociation (row_instance = RowInstance (row_definition = RowDefinition()),
                                         report = Report(build=Build(), failure=True, setup=Setup()))
        self.session.add (assoc)
        self.session.commit()
        self.session.delete (assoc.report)
        self.session.commit()
        self.assertEquals (0, self.session.query (Report).count())
        self.assertEquals (0, self.session.query (ReportRowAssociation).count())
        self.assertEquals (1, self.session.query (RowInstance).count()) 
        
    def test_delete_coldef (self):
        assoc = ReportRowAssociation (row_instance = RowInstance (row_definition = RowDefinition()),
                                         report = Report(build=Build(), failure=True, setup=Setup()))
        self.session.add (assoc)
        self.session.commit()
        self.session.delete (assoc.row_instance)
        self.session.commit()
        self.assertEquals (1, self.session.query (Report).count()) # we keep the report
        self.assertEquals (0, self.session.query (ReportRowAssociation).count())
        self.assertEquals (0, self.session.query (RowInstance).count()) 
        
    def test_delete_assoc (self):
        assoc = ReportRowAssociation (row_instance = RowInstance (row_definition = RowDefinition()),
                                         report = Report(build=Build(), failure=True, setup=Setup()))
        self.session.add (assoc)
        self.session.commit()
        self.session.delete (assoc)
        self.session.commit()
        self.assertEquals (1, self.session.query (Report).count()) # We keep the report
        self.assertEquals (0, self.session.query (ReportRowAssociation).count())
        self.assertEquals (1, self.session.query (RowInstance).count()) # We keep the column definition
        
class TestResultStructure (DbTestCase):
    def test_result_creation (self):
        result = Result ()
        self.session.add (result)
        self.session.commit()
        self.assertEquals (1, self.session.query (Result).count())
        
    def test_result_delete (self):
        result = Result ()
        self.session.add (result)
        self.session.commit()
        self.session.delete (result)
        self.session.commit()
        self.assertEquals (0, self.session.query (Result).count())

    def test_result_values_inserts (self):
        ins = getattr (Result, "__table__").insert()
        self.session.execute (ins, [dict (value_number=1, ), 
                                    dict(value_number=2, )])
        self.session.commit()
        self.assertEquals (2, self.session.query (Result).count())
        
class TestRowColResultAssociationStructure (DbTestCase):
    def test_assoc_creation (self):
        assoc = RowColResultAssociation (row_instance = RowInstance(row_definition = RowDefinition()),
                                         column_definition = ColumnDefinition (),
                                         result = Result())
        self.session.add (assoc)
        self.session.commit()
        self.assertEquals (1, self.session.query (RowColResultAssociation).count())

class TestInsertReport (DbTestCase):
    def test_can_read_small_compressed_pickle_and_create_reports (self):
        fp = gzip.GzipFile(os.path.join (os.path.split (__file__)[0], "files", "small.pgz"))
        reports = []
        for _ in range (4) :
            report, _, _, _, _, _, _, _ = pickle.load(fp)
            if report is None: break
            reports.append (report)
            #print len (report.rows), len(report.columns)
            
    def test_can_insert_report_in_db (self):
        fp = gzip.GzipFile(os.path.join (os.path.split (__file__)[0], "files", "small.pgz"))
        for _ in range (4):
            report, platform, platform_variant, platform_bits, exe_full_version, exe_bits, exe_name, taskdef = pickle.load(fp) # third one, with 28 columns and 1148 rows.
            db_report = Report.from_report(report, 
                                           platform, 
                                           platform_variant, 
                                           platform_bits, 
                                           exe_full_version, 
                                           exe_bits, 
                                           exe_name, 
                                           taskdef, 
                                           session=self.session)
        self.assertEquals (1, self.session.query (cvc_wrapper.Build).count())
        self.assertEquals (4, self.session.query (cvc_wrapper.Setup).count())
        self.assertEquals (4, self.session.query (cvc_wrapper.Report).count())
        self.assertEquals ([0, 0, 28, 58], 
                           [len ([ins for ins in rep.column_definitions])
                                 for rep in self.session.query (cvc_wrapper.Report).all()])
                
if __name__ == '__main__':
    unittest.main()
    
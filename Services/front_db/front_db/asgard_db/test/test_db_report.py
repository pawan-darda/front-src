import unittest
import time, sys
import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
#from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, MetaData

from front_db.asgard_db.db_wrapper import formatData, \
    BatchProperty, Step, Batch, Scenario, Version, RevLogs, \
    ScenarioProperty, Row, CellValue, Col, StepInit, RealCell, \
    StepProperty, AvgCellMap, Average, \
    TABLE_BATCH_RUN, TABLE_SCENARIO, TABLE_STEP_INIT, TABLE_BR_PROP, \
    TABLE_SC_PROP, TABLE_ST_PROP, TABLE_ROW, TABLE_COLUMN, TABLE_CELL, TABLE_CELL_VALUE, TABLE_STEP, TABLE_SOFT_VERSION, \
    SqlAlchemyBatchInserter, cell_dict_to_hashes, Base #, FastDeleter
from front_utils.versions.prime_versions import PrimeVersion
    
assert TABLE_CELL_VALUE
assert CellValue
    
timestamp = 1305883959 # 2011/05/20, 11:33
now = datetime.datetime.fromtimestamp(timestamp)

    
import cPickle as pickle
import zlib, gzip
import Utils
#from front_utils import rev_logs
#from sqlalchemy.dialects.sybase.base import SMALLMONEY
from front_db.asgard_db.db_wrapper import SqlAlchemyRevLogsInserter, \
    batch_to_dict, AsgardImportException

medium_br = pickle.load (gzip.GzipFile(Utils.colocated_name ("pickles/medium.asg")))
small_br = pickle.load (gzip.GzipFile(Utils.colocated_name ("pickles/small.asg")))


def context_almost_eq (first, second):
    try :
        return all([first[k] == second[k] for k in first.keys()]) and len(first) == len(second) 
    except KeyError:
        return False    

def batch_almost_eq (first, second):
    if first is second:
        return True
    if (not (context_almost_eq (first.context, second.context)) 
        or first.uid != second.uid):
        return False

    if not scenarios_almost_eq (first.scenarios, second.scenarios) : return False
    return True

def scenarios_almost_eq (first, second):
    def cmpKey(sc):
        return (sc.name, len(list(sc.steps)), sc.duration)

    scenarios1 = list(first)
    scenarios1.sort(lambda x, y: cmp(cmpKey(x), cmpKey(y)))

    scenarios2 = list(second)
    scenarios2.sort(lambda x, y: cmp(cmpKey(x), cmpKey(y)))
    
    if not len(scenarios1) == len (scenarios2) : return False
    for i in range (len(scenarios1)):
        if not scenario_almost_eq (scenarios1 [i], scenarios2[i]) : return False
    return True 

def float_almost_eq (f1, f2):
    return abs (f1 - f2) < 1e-10

def scenario_almost_eq (first, second):
    return (first is second or
            (first.name == second.name
        and context_almost_eq (first.context, second.context)
        and first.status == second.status
        and float_almost_eq(first.duration, second.duration)
        and list (first.steps) == list(second.steps)
        ))

if sys.version_info < (2, 4):
    class TestCase(unittest.TestCase):
        assertTrue = getattr (unittest.TestCase.failUnless, "im_func")
else:
    TestCase = unittest.TestCase
    
class TestHashes (TestCase):
    def test_can_create_hash (self):
        d = dict (status=None,
                  exception=None,
                  exc_info=None,
                  f_actual=None,
                  s_actual=None,
                  f_expected=None,
                  s_expected=None,
                  )
        cell_dict_to_hashes (d)

    def test_hashes_differ (self):
        "Check for basic non conflicting hashes, just to make sure the algorithm is not entirely broken"
        i_values = (None, 0, 1)
        s_values = (None, "None", "a")
        hashes_set = set ()
        for status in i_values:
            for exception in s_values:
                for exc_info in s_values:
                    for f_actual in i_values:
                        for s_actual in s_values:
                            for f_expected in i_values:
                                for s_expected in s_values:
                                    d = dict (status=status,
                                              exception=exception,
                                              exc_info=exc_info,
                                              f_actual=f_actual,
                                              s_actual=s_actual,
                                              f_expected=f_expected,
                                              s_expected=s_expected,
                                              )
                                    hashes = cell_dict_to_hashes (d)
                                    self.assertTrue (hashes not in hashes_set)
                                    hashes_set.add (hashes)

class DbTestCase (TestCase):
    
    def create_empty_average(self, commit=False):
        """
        Helper methods for tests
        """
        a = Average(avg=0.0, cell_id=1)
        self.session.add(a)
        if commit:
            self.session.commit()
        return a
    
    def create_empty_avg_cell_map(self, commit=False):
        avg_map = AvgCellMap(avg_id=1,
                             cell_id = 1)
        self.session.add(avg_map)
        if commit:
            self.session.commit()
        return avg_map
    
    def create_empty_soft_version (self, commit=False):
        """
        Helper function for tests
        """
        class FakeVersion (object):
            main = 4
            sub = 3
            bn = 541
            component = "PRIME"
            name = "4.3"
            nice = "4.3.541"
        
        v = Version(FakeVersion(), 'PRIME')
        self.session.add (v)
        if commit :
            self.session.commit ()
        return v
       
    def create_empty_batch_run (self, commit=False):
        """
        Helper function for tests
        """
        b = Batch (uid="",
                 start=now,
                 version=self.create_empty_soft_version(commit=commit),
                 #softVersion=v,
                 name="empty")
        self.session.add (b)
        if commit: self.session.commit ()
        return b
    
    def create_empty_scenario (self, batch_run=None, commit=False):
        if batch_run is None:
            batch_run = self.create_empty_batch_run(commit=commit)
        sc = Scenario (batch=batch_run,
                                      name="",
                                      duration=0,
                                      status=0)
        self.session.add (sc)
        if commit: self.session.commit ()
        return sc
    
    def create_empty_step (self, scenario=None, commit=False):
        if scenario is None :
            scenario = self.create_empty_scenario (commit=commit)
        st = Step (status=0,
                                      duration=0,
                                      exception="",
                                      fixture="",
                                      kind="f",
                                      scenario=scenario,
                                      line=0,
                                      ordinal=0)
        self.session.add (st)
        if commit: self.session.commit ()
        return st
        
    def create_empty_row (self, step=None, commit=False):
        if step is None:
            step = self.create_empty_step(commit=commit)
        row = Row (step=step,
                    exception="",
                    duration=0,
                    kind="a",
                    status=0,
                    ordinal=0)
        self.session.add (row)
        if commit : self.session.commit ()
        return row
        
    def create_empty_column (self, step=None, commit=False):
        if step is None:
            step = self.create_empty_step(commit=commit)
        col = Col (step=step,
                    kind="a",
                    name="",
                    ordinal=0,
                    tolerance=0
                    )
        self.session.add (col)
        if commit : self.session.commit ()
        return col
    
    def setUp (self):
        super (DbTestCase, self).setUp()
        
        self.session = get_session ()
        self.session.query(AvgCellMap).delete()
        self.session.query(Average).delete()
        self.session.query(RevLogs).delete ()
        self.session.query(RealCell).delete ()
        self.session.query(CellValue).delete()
        self.session.query(Row).delete ()
        self.session.query(Col).delete ()
        self.session.query(StepInit).delete ()
        self.session.query(StepProperty).delete ()
        self.session.query(Step).delete ()
        self.session.query(ScenarioProperty).delete ()
        self.session.query(Scenario).delete ()
        self.session.query(BatchProperty).delete ()
        self.session.query(Batch).delete ()
        self.session.query(Version).delete()
        self.session.commit()
        
        self.assertEquals (0, self.session.query(Batch).count())
        self.assertEquals (0, self.session.query(Version).count())
        self.assertEquals (0, self.session.query(BatchProperty).count())
        self.assertEquals (0, self.session.query(Scenario).count())
        self.assertEquals (0, self.session.query(Step).count())
        self.assertEquals (0, self.session.query(Row).count())
        self.assertEquals (0, self.session.query(Col).count())
        self.assertEquals (0, self.session.query(CellValue).count())
        self.assertEquals (0, self.session.query(RealCell).count())
        self.assertEquals (0, self.session.query(RevLogs).count())
        self.assertEquals (0, self.session.query(Average).count())
        self.assertEquals (0, self.session.query(AvgCellMap).count())
        
        self.__start = now
        self.session.commit()
        

    def tearDown (self):
        self.session.rollback () # Just in case there is something left
        super (DbTestCase, self).tearDown()

        
class TestSqlAlchemyInstancesCreationFromDict (DbTestCase):
        
    def test_new_batch_run_from_dict (self):
        "One can create a new Batch out of a dictionary, then output it as Batch object with correct data"
        version = self.create_empty_soft_version()

        class FakeBatch (object):
            uid = ""
            start = now
            name = "whatever"
            scenarios = []
            context = {"primebuildname": version.name}

        d = dict (
            uid="",
            start_stamp=timestamp,
            name="whatever",
            scenarios=[],
            context={"primebuildname": version.name},
            )
        br = Batch.from_dict (d, session=self.session)
        self.session.add (br)
        self.session.commit ()
        self.assertEquals (1, self.session.query(Batch).count())
        
        self.assertEquals (d, self.session.query(Batch).one().as_dict ())
        br_test = self.session.query(Batch).one ()
        self.assertEquals (FakeBatch.uid, br_test.uid)
        self.assertEquals (FakeBatch.name, br_test.name)
        self.assertEquals (FakeBatch.start, br_test.start)
        self.assertEquals (FakeBatch.scenarios, br_test.scenarios.all())
        
        self.session.delete (br)
        self.session.commit ()
        self.assertEquals (0, self.session.query(Batch).count())
        
    def test_new_scenario_from_dict (self):
        version = self.create_empty_soft_version()
        d = dict (
            uid="",
            start_stamp=timestamp,
            name="whatever",
            context={"primebuildname": version.name},
            )
        d["scenarios"] = [dict (name="bar",
                                duration=1,
                                status=0,
                                context={},
                                steps=[],
                                exception=None,
                                exc_info=None
                            ),
                          dict (name="foo",
                                duration=2.0,
                                status=1,
                                context={"far":"boo"},
                                steps=[],
                                exception=None,
                                exc_info=None
                            )
                          ]
        br = Batch.from_dict (d, session=self.session)
        self.session.add (br)
        self.session.commit ()
        self.assertEquals (1, self.session.query(Batch).count())
        self.assertEquals (2, self.session.query(Scenario).count())
        self.assertEquals (d, self.session.query(Batch).one().as_dict()) # Note: it works only because "bar" comes before "foo" in alphabetical order
        sc = self.session.query(Scenario).order_by (Scenario.name).first()
        self.assertEquals (sc.as_dict (),
                           self.session.query(Batch).one().as_dict()["scenarios"][0])
        self.assertEquals (sc.name, d["scenarios"][0]["name"])
        self.assertEquals (sc.duration, d["scenarios"][0]["duration"])
        self.assertEquals (sc.status, d["scenarios"][0]["status"])
        self.assertEquals (sc.context, d["scenarios"][0]["context"])
        self.assertEquals (sc.steps.all(), d["scenarios"][0]["steps"])
        
    def test_new_step_from_dict (self):
        version = self.create_empty_soft_version()
        d = dict (
            uid="",
            start_stamp=timestamp,
            name="whatever",
            context={"primebuildname": version.name},
            )
        d["scenarios"] = [dict (name="bar",
                                duration=1,
                                status=0,
                                context={},
                                steps=[],
                                exception=None,
                                exc_info=None
                            ),
                          dict (name="foo",
                                duration=2.0,
                                status=1,
                                context={"far":"boo"},
                                steps=[],
                                exception=None,
                                exc_info=None
                            )
                          ]
        d["scenarios"][0]["steps"] = [dict (fixture="a fixture",
                                           status=1,
                                           duration=1.1,
                                           context={},
                                           lineno=111,
                                           ordinal=0,
                                           label="a label",
                                           exception="an exception",
                                           exc_info=None,
                                           kind="r",
                                           init_params={},
                                           columns=[],
                                           all_rows=[]
                                           )]
        
        d["scenarios"][1]["steps"] = [dict (fixture="another fixture",
                                           status=2,
                                           duration=1.2,
                                           context={},
                                           lineno=222,
                                           ordinal=0,
                                           label="a label",
                                           exception="an exception",
                                           exc_info=None,
                                           kind="r",
                                           init_params={"a key": "another value"},
                                           columns=[],
                                           all_rows=[]
                                           ),
                                     
                                     dict(fixture="a third fixture",
                                           status=3,
                                           duration=1.3,
                                           context={"a context key": "a value"},
                                           lineno=333,
                                           ordinal=1, # Note: the ordinals need to be in the right order
                                           label="a label",
                                           exception="an exception",
                                           exc_info=None,
                                           kind="r",
                                           init_params={},
                                           columns=[],
                                           all_rows=[]
                                          )]
        br = Batch.from_dict (d, session=self.session)
        self.session.add (br)
        self.session.commit ()
        self.assertEquals (1, self.session.query(Batch).count())
        self.assertEquals (2, self.session.query(Scenario).count())
        self.assertEquals (3, self.session.query(Step).count())
        self.assertEquals (d, self.session.query(Batch).one().as_dict()) # Note: it works only because "bar" comes before "foo" in alphabetical order
        st = self.session.query(Step).all()[-1] # last one
        self.assertEquals (d["scenarios"][1]["steps"][1]["fixture"], st.fixture) 
        self.assertEquals (d["scenarios"][1]["steps"][1]["status"], st.status) 
        self.assertEquals (d["scenarios"][1]["steps"][1]["context"], st.context) 
        self.assertEquals (d["scenarios"][1]["steps"][1]["lineno"], st.lineno) 
        self.assertEquals (d["scenarios"][1]["steps"][1]["ordinal"], st.ordinal) 
        self.assertEquals (d["scenarios"][1]["steps"][1]["label"], st.label) 
        self.assertEquals (d["scenarios"][1]["steps"][1]["exception"], st.exception) 
        self.assertEquals (d["scenarios"][1]["steps"][1]["kind"], st.kind) 
        self.assertEquals (d["scenarios"][1]["steps"][1]["init_params"], st.init_params) 
        self.assertEquals (d["scenarios"][1]["steps"][1]["columns"], st.columns.all()) 
        self.assertEquals (d["scenarios"][1]["steps"][1]["all_rows"], st.all_rows.all()) 
        
    def test_new_column_from_dict (self):
        version = self.create_empty_soft_version()
        d = dict (
            uid="",
            start_stamp=timestamp,
            name="whatever",
            context={"primebuildname": version.name},
            )
        d["scenarios"] = [dict (name="bar",
                                duration=1,
                                status=0,
                                context={},
                                steps=[]
                            ),
                          dict (name="foo",
                                duration=2.0,
                                status=1,
                                context={"far":"boo"},
                                steps=[]
                            )
                          ]
        d["scenarios"][0]["steps"] = [dict (fixture="a fixture",
                                           status=1,
                                           duration=1.1,
                                           context={},
                                           lineno=111,
                                           ordinal=0,
                                           label="a label",
                                           exception="an exception",
                                           kind="r",
                                           init_params={},
                                           columns=[],
                                           all_rows=[]
                                           )]
        d["scenarios"][0]["steps"][0]["columns"] = [dict (name="a",
                                                         kind="i",
                                                         ordinal=0,
                                                         ),
                                                   dict (name="b",
                                                         kind="o",
                                                         ordinal=1, # There is a tolerance of 0.0 by default
                                                         ),
                                                   dict (name="c",
                                                         kind="o",
                                                         tolerance=1.5,
                                                         ordinal=2,
                                                         ),
                                                   dict (name="d",
                                                         kind="i",
                                                         ordinal=3,
                                                         )
                                                   ]
        br = Batch.from_dict (d, session=self.session)
        self.session.add (br)
        self.session.commit ()
        self.assertEquals (1, self.session.query(Batch).count())
        self.assertEquals (2, self.session.query(Scenario).count())
        self.assertEquals (1, self.session.query(Step).count())
        self.assertEquals (4, self.session.query(Col).count())
        
        columns = self.session.query(Col).all ()
        self.assertEquals (["a", "b", "c", "d"], [c.name for c in columns])
        self.assertEquals (["i", "o", "o", "i"], [c.kind for c in columns])
        self.assertEquals ([0, 1, 2, 3], [c.ordinal for c in columns])
        self.assertEquals ([0, 0, 1.5, 0], [c.tolerance for c in columns])
        
    def test_new_row_from_dict (self):
        version = self.create_empty_soft_version()
        d = dict (
            uid="",
            start_stamp=timestamp,
            name="whatever",
            context={"primebuildname": version.name},
            )
        d["scenarios"] = [dict (name="bar",
                                duration=1,
                                status=0,
                                context={},
                                steps=[]
                            ),
                          dict (name="foo",
                                duration=2.0,
                                status=1,
                                context={"far":"boo"},
                                steps=[]
                            )
                          ]
        d["scenarios"][0]["steps"] = [dict (fixture="a fixture",
                                           status=1,
                                           duration=1.1,
                                           context={},
                                           lineno=111,
                                           ordinal=0,
                                           label="a label",
                                           exception="an exception",
                                           kind="r",
                                           init_params={},
                                           columns=[],
                                           all_rows=[]
                                           )]
        d["scenarios"][0]["steps"][0]["columns"] = [dict (name="a",
                                                         kind="i",
                                                         ordinal=0,
                                                         ),
                                                   dict (name="c",
                                                         kind="o",
                                                         tolerance=1.5,
                                                         ordinal=1,
                                                         )
                                                   ]
        d["scenarios"][0]["steps"][0]["all_rows"] = [dict (# surplus
                                                          duration=0.5,
                                                          exception="an exception",
                                                          ordinal=0,
                                                          status=1,
                                                          kind="m",
                                                          cells=[],
                                                          ),
                                                    dict (# normal
                                                          duration=2.0,
                                                          exception="",
                                                          ordinal=1,
                                                          status=2,
                                                          kind="s",
                                                          cells=[],
                                                          )
                                                    ]

        br = Batch.from_dict (d, session=self.session)
        self.session.add (br)
        self.session.commit ()
        self.assertEquals (1, self.session.query(Batch).count())
        self.assertEquals (2, self.session.query(Scenario).count())
        self.assertEquals (1, self.session.query(Step).count())
        self.assertEquals (2, self.session.query(Col).count())
        self.assertEquals (2, self.session.query(Row).count())
        
        rows = self.session.query(Row).all ()
        self.assertEquals (["m", "s"], [r.kind for r in rows])
        self.assertEquals (["an exception", ""], [r.exception for r in rows])
        self.assertEquals ([0, 1], [r.ordinal for r in rows])
        self.assertEquals ([1, 2], [r.status for r in rows])
        self.assertEquals ([0.5, 2], [r.duration for r in rows])
        
    def test_unit_tests_dicts (self):
        d = {'scenarios': 
             [{'status': 1,
               'duration': 0,
               'steps': [{'ordinal': 0,
                          'status': 1,
                          'exception': None,
                          'fixture': 'fixture.unittest',
                          'kind': 'r',
                          'label': None,
                          'lineno':-1,
                          'context': {},
                          'duration': 0,
                          'all_rows': [{'ordinal': 0,
                                        'status': 1,
                                        'exception': None,
                                        'cells': [{'expected': 'test_acm.TestAcmBasicsWhenNotConnected.test_FFalse_gives_false',
                                                   'status': 1,
                                                   'exception': None,
                                                   'actual': 'test_acm.TestAcmBasicsWhenNotConnected.test_FFalse_gives_false'},
                                                  {'expected': 1, 'status': 1, 'exception': None, 'actual': 1},
                                                  {'expected': None, 'status': 1, 'exception': None, 'actual': None}
                                                  ],
                                        'kind': 's',
                                        'duration': 0
                                        },
                                       {'ordinal': 1, 'status': 1, 'exception': None,
                                        'cells': [
                                                  {'expected': 'test_acm.TestAcmBasicsWhenNotConnected.test_FTrue_gives_true', 'status': 1, 'exception': None, 'actual': 'test_acm.TestAcmBasicsWhenNotConnected.test_FTrue_gives_true'},
                                                  {'expected': 1, 'status': 1, 'exception': None, 'actual': 1},
                                                  {'expected': None, 'status': 1, 'exception': None, 'actual': None}
                                                  ],
                                        'kind': 's',
                                        'duration': 0
                                        },
                                       {'ordinal': 2,
                                        'status': 1,
                                        'exception': None,
                                        'cells': [
                                                  {'expected': 'test_version.TestAcmVersions.test_short_version_starts_with_numbers', 'status': 1, 'exception': None, 'actual': 'test_version.TestAcmVersions.test_short_version_starts_with_numbers'},
                                                  {'expected': 1, 'status': 1, 'exception': None, 'actual': 1},
                                                  {'expected': None, 'status': 1, 'exception': None, 'actual': None}
                                                  ],
                                        'kind': 's',
                                        'duration': 0
                                        },
                                       {'ordinal': 3, 'status': 1, 'exception': None,
                                        'cells': [
                                                  {'expected': 'test_collections.TestCollections.test_can_create_FArray_instance', 'status': 1, 'exception': None, 'actual': 'test_collections.TestCollections.test_can_create_FArray_instance'},
                                                  {'expected': 1, 'status': 1, 'exception': None, 'actual': 1},
                                                  {'expected': None, 'status': 1, 'exception': None, 'actual': None}],
                                        'kind': 's', 'duration': 0
                                        },
                                       {'ordinal': 4, 'status': 1, 'exception': None,
                                        'cells': [
                                                  {'expected': 'test_unitsystem.TestUnitSystem.test_DenominatedBasket_Collapsing_on_create', 'status': 1, 'exception': None, 'actual': 'test_unitsystem.TestUnitSystem.test_DenominatedBasket_Collapsing_on_create'},
                                                  {'expected': 1, 'status': 1, 'exception': None, 'actual': 1},
                                                  {'expected': None, 'status': 1, 'exception': None, 'actual': None}
                                                  ],
                                        'kind': 's', 'duration': 0},
                                       ],
                          'init_params': {},
                          'columns': [{'ordinal': 0, 'kind': 'o', 'tolerance': None, 'name': 'name'},
                                      {'ordinal': 1, 'kind': 'o', 'tolerance': None, 'name': 'status'},
                                      {'ordinal': 2, 'kind': 'o', 'tolerance': None, 'name': 'exception'}
                                      ]
                          }
                         ],
               'name': 'UnitTests_Sol32', 'context': {}
               }
              ],
             'start_stamp': 0.0, 'name': 'UnitTests',
             'context': {'platform_version': 'Generic_120011-14',
                         'platform_arch': "('32bit', 'ELF')",
                         'platform_system': 'SunOS',
                         'platform_release': '5.10',
                         'primebuildname': '2009.2.21-4.4.794.0-20110526',
                         'buildnumber': '7'},
             'uid': '403679fa-8b89-11e0-801d-510f8a3f56e4'}
        br = Batch.from_dict (d, session=self.session)
        self.session.add (br)
        self.session.commit ()
        self.assertEquals (1, self.session.query(Batch).count())
        self.assertEquals (1, self.session.query(Scenario).count())
        self.assertEquals (1, self.session.query(Step).count())
        self.assertEquals (3, self.session.query(Col).count())
        self.assertEquals (15, self.session.query(RealCell).count())
        self.assertEquals (7, self.session.query(CellValue).count())
        for row in self.session.query(Step).one().all_rows:
            self.assertEquals (3, row.unordered_cells.count())
            


    def test_new_cells_from_dict_slow (self):
        self.check_new_cells_from_dict(False)
    def test_new_cells_from_dict_fast (self):
        self.check_new_cells_from_dict(True)

    def check_new_cells_from_dict (self, fast=False):
        if fast:return
        version = self.create_empty_soft_version()
        d = dict (
            uid="",
            start_stamp=timestamp,
            name="whatever",
            context={"primebuildname": version.name},
            )
        d["scenarios"] = [dict (name="bar",
                                duration=1,
                                status=0,
                                context={},
                                exception=None,
                                exc_info=None,
                                steps=[dict (fixture="a fixture",
                                           status=1,
                                           duration=1.1,
                                           context={},
                                           lineno=111,
                                           ordinal=0,
                                           label="a label",
                                           exception="an exception",
                                           exc_info="A formated\ntraceback\n",
                                           kind="r",
                                           init_params={},
                                           columns=[dict (name="a",
                                                         kind="i",
                                                         ordinal=0,
                                                         ),
                                                   dict (name="b",
                                                         kind="o",
                                                         tolerance=1.5,
                                                         ordinal=1,
                                                         ),
                                                   dict (name="c",
                                                         kind="i",
                                                         ordinal=2,
                                                         )
                                                   ],
                                           all_rows=[dict (# surplus
                                                          duration=0.5,
                                                          exception="an exception",
                                                          exc_info="A formated\ntraceback\n",
                                                          ordinal=0,
                                                          status=1,
                                                          kind="m",
                                                          cells=[dict (input="foo",
                                                                         exception=None,
                                                                         exc_info=None,
                                                                         status=0),
                                                                   dict (actual="foo2",
                                                                         status=2,
                                                                         exception="aa except",
                                                                         exc_info="A formated\ntraceback\n",
                                                                         expected="foo3"),
                                                                   dict (input=2.4,
                                                                         exception=None,
                                                                         exc_info=None,
                                                                         status=0),
                                                                   ],
                                                          ),
                                                    dict (# normal
                                                          duration=2.0,
                                                          exception="",
                                                          exc_info=None,
                                                          ordinal=1,
                                                          status=2,
                                                          kind="s",
                                                          cells=[dict (input="bar",
                                                                         exception=None,
                                                                         exc_info=None,
                                                                         status=0),
                                                                   dict (actual=232,
                                                                         expected=654,
                                                                         exception=None,
                                                                         exc_info=None,
                                                                         status=0),
                                                                   dict (input=0,
                                                                         exception=None,
                                                                         exc_info=None,
                                                                         status=0),
                                                                   ],
                                                          ),
                                                    dict (# we put the same row twice
                                                          duration=2.0,
                                                          exception="",
                                                          exc_info=None,
                                                          ordinal=2,
                                                          status=2,
                                                          kind="s",
                                                          cells=[dict (input="bar",
                                                                         exception=None,
                                                                         exc_info=None,
                                                                         status=0),
                                                                   dict (actual=232,
                                                                         expected=654,
                                                                         exception=None,
                                                                         exc_info=None,
                                                                         status=0),
                                                                   dict (input=0,
                                                                         exception=None,
                                                                         exc_info=None,
                                                                         status=0),
                                                                   ],
                                                          ),
                                                    ],
                                           )]
                            ),
                          dict (name="foo",
                                duration=2.0,
                                status=1,
                                context={"far":"boo"},
                                steps=[]
                            )
                          ]

        if not fast:
            br = Batch.from_dict (d, session=self.session, fast=False)
            self.session.add (br)
            self.session.commit ()
        else :
            br = Batch.from_dict (d, session=self.session, fast=True)
            self.session.commit ()
            
        self.assertEquals (1, self.session.query(Batch).count())
        self.assertEquals (2, self.session.query(Scenario).count())
        self.assertEquals (1, self.session.query(Step).count())
        self.assertEquals (3, self.session.query(Col).count())
        self.assertEquals (3, self.session.query(Row).count())
        #self.assertEquals (9, self.session.query(Cell).count())
        self.assertEquals (9, self.session.query(RealCell).count())
        self.assertEquals (6, self.session.query(CellValue).count())
        self.assertEquals (3, len (self.session.query(Row).all()[0].as_dict()["cells"]))
        self.assertEquals (3, len (self.session.query(Row).all()[1].as_dict()["cells"]))
        self.assertEquals (dict (input="foo", status=0, exception=None, exc_info=None),
                           self.session.query(RealCell).join(Row).join(Col).order_by (Row.ordinal, Col.ordinal).all()[0].as_dict())
        self.assertEquals (dict (actual="foo2", expected="foo3", status=2, exception="aa except", exc_info='A formated\ntraceback\n'),
                           self.session.query(RealCell).join(Row).join(Col).order_by (Row.ordinal, Col.ordinal).all()[1].as_dict())
        for coli, column in enumerate (self.session.query(Col).order_by (Col.ordinal)):
            for rowi, row in enumerate (self.session.query(Row).order_by (Row.ordinal)):
                cell_d = d["scenarios"][0]["steps"][0]["all_rows"][rowi]["cells"][coli]
                self.assertEquals (coli, column.ordinal)
                self.assertEquals (rowi, row.ordinal)
                self.assertEquals (cell_d,
                                   self.session.query(Row).order_by (Row.ordinal).all()[rowi].as_dict()["cells"][coli]) 
                self.assertEquals (cell_d,
                                   self.session.query(Row).filter (Row.ordinal == rowi).one().as_dict()["cells"][coli]) 
                self.assertEquals (cell_d,
                                   self.session.query(Col).order_by (Col.ordinal).all()[coli].as_dict(with_cells=True)["cells"][rowi]) 
                self.assertEquals (cell_d,
                                   self.session.query(Col).filter (Col.ordinal == coli).one().as_dict(with_cells=True)["cells"][rowi]) 
                self.assertEquals (cell_d,
                                   self.session.query(RealCell).join (Row).join (Col).filter(Row.ordinal == rowi).filter(Col.ordinal == coli).one().as_dict()) 
                self.assertEquals (self.session.query(Col).filter (Col.ordinal == coli).one().cells[rowi],
                                   self.session.query(Row).filter (Row.ordinal == rowi).one().cells[coli]) 
                

class TestDqlAlchemyInstancesCreationFromFakeClasses (DbTestCase):
    def test_no_objects_at_beginning (self):
        self.assertEquals (0, self.session.query(Batch).count())
        
    def test_new_batch_run_from_fake_batch (self):
        "One can create a new Batch out of a class with attributes (mimic the structure.py one), then extract it as Batch or dict"
        version = self.create_empty_soft_version()
        class FakeBatch (object):
            uid = "a uid"
            start = now
            name = "whatever"
            scenarios = []
            context = {"primebuildname": version.name}
        br = Batch.from_batch(FakeBatch, session=self.session)
        br.version = version
        self.session.commit()
        self.assertEquals (1, self.session.query(Batch).count())
        
        d = self.session.query(Batch).one().as_dict ()
        
        self.assertEquals (br.name, d["name"])
        self.assertEquals (br.name, "whatever")
        self.assertEquals (br.uid, d["uid"])
        self.assertEquals (br.uid, "a uid")
        self.assertEquals (timestamp, d["start_stamp"])
        self.assertEquals (br.context, d["context"])
        self.assertEquals (br.context, {"primebuildname": version.name})        
        
        self.session.delete (br)
        self.session.commit ()
        self.assertEquals (0, self.session.query(Batch).count())
        
class TestDqlAlchemyInstancesCreationAndDeletion (DbTestCase):
    

    def test_no_objects_at_beginning (self):
        self.assertEquals (0, self.session.query(Batch).count())
        self.assertEquals (0, self.session.query(Average).count())
        self.assertEquals (0, self.session.query(AvgCellMap).count())
    
    def test_average(self):
        """
        Test adding and deleting Average and AvgCellMap objects
        """
        c = CellValue (exception="exc",
                       status=0,
                       f_actual=2,
                       s_actual="3",
                       f_expected=1,
                       s_expected="4",
                       hash_value_low=5,
                       hash_value_high=6)
        self.session.add(c)
        self.session.commit()
        self.assertEquals (1, self.session.query(CellValue).count())
        self.assertEquals (0, self.session.query(Average).count())
        self.assertEquals (0, self.session.query(AvgCellMap).count())

        avg = Average(avg=0.0, cell_id=c.id)
        self.session.add(avg)
        self.session.commit()
        m = AvgCellMap(avg_id=avg.id, cell_id=c.id)
        self.session.add(m)
        self.session.commit()
        
        self.assertEquals (1, self.session.query(CellValue).count())
        self.assertEquals (1, self.session.query(Average).count())
        self.assertEquals (1, self.session.query(AvgCellMap).count())

        self.session.delete(m)
        self.session.delete(avg)    
        self.session.delete(c)

        self.assertEquals (0, self.session.query(CellValue).count())
        self.assertEquals (0, self.session.query(Average).count())
        self.assertEquals (0, self.session.query(AvgCellMap).count())
        
    def test_new_soft_version (self):
        """One can create a new Version directly against the wrapper class"""
        v = Version (PrimeVersion ("4.3"), 'PRIME')
        self.session.add (v)
        self.session.commit ()
        self.assertEquals (1, self.session.query(Version).count())
        self.session.delete (v)
        self.session.commit ()
        self.assertEquals (0, self.session.query(Version).count())
        
    def test_new_batch_run (self):
        "One can create a new batch directly against the Batch class"
        br = Batch (uid="",
                                    start=now,
                                    version=self.create_empty_soft_version(),
                                    name="whatever")
        self.session.add (br)
        self.session.commit ()
        self.assertEquals (1, self.session.query(Batch).count())
        self.session.delete (br)
        self.session.commit ()
        self.assertEquals (0, self.session.query(Batch).count())
        
        
    def test_new_version_and_batch_runs (self):
        v = self.create_empty_soft_version(commit=False)
        v.batch_runs = [Batch (uid="", start=now, name="whatever"),
                        Batch (uid="", start=now, name="whatever")]
        self.session.add (v)
        self.session.commit()
        
        v2 = self.session.query(Version)[0]
        self.assertTrue (v2 is v)
        self.assertEquals (2, v.batch_runs.count())
        
        v.batch_runs.append (Batch (uid="", start=now, name="whatever"))
        self.session.rollback()
        self.assertEquals (2, self.session.query (Batch).count())
        self.assertEquals (2, v.batch_runs.count())
        
        v.batch_runs.append (Batch (uid="", start=now, name="whatever"))
        self.session.commit()
        self.assertEquals (3, self.session.query (Batch).count())
        
    def test_new_scenario (self):
        br = self.create_empty_batch_run()
        sc = Scenario (batch=br, name="", duration=12345.67, status=0)
        self.session.add(sc)
        self.session.commit()
        self.assertEquals (1, self.session.query(Scenario).count())
        self.session.query(Scenario).one()
        
        self.session.query(Scenario).one().batch.name = "foo"
        self.assertEquals ("foo", self.session.query(Scenario).join (Batch).filter (Batch.name == "foo").one().batchRun.name)
        
        self.assertEquals (datetime.time (3, 25, 45, 670000), self.session.query(Scenario).first().duration_time)
        self.session.delete(sc)
        self.session.commit()
        self.assertEquals (0, self.session.query(Scenario).count())
                
    def test_new_scenario_destroy_batchrun (self):
        br = self.create_empty_batch_run()
        sc = Scenario (batch=br, name="", duration=0, status=0)
        self.session.add (sc)
        self.session.commit()
        self.assertEquals (1, self.session.query(Scenario).count())
        self.assertEquals (1, self.session.query(Batch).count())
        self.session.delete (br)
        self.session.commit()
        self.assertEquals (0, self.session.query(Scenario).count())
        self.assertEquals (0, self.session.query(Batch).count())
        
    def test_new_scenario_delete_fast_batchrun (self):
        br = self.create_empty_batch_run()
        sc = Scenario (batch=br, name="", duration=0, status=0)
        self.session.add (sc)
        self.session.commit()
        self.assertEquals (1, self.session.query(Scenario).count())
        self.assertEquals (1, self.session.query(Batch).count())
        br.fast_delete ()
        self.session.commit()
        self.assertEquals (0, self.session.query(Scenario).count())
        self.assertEquals (0, self.session.query(Batch).count())
        
    def test_new_step (self):
        sc = self.create_empty_scenario()
        st = Step (scenario=sc,
                    exception="",
                    duration=0,
                    fixture="",
                    kind="f",
                    status=0,
                    line=0,
                    ordinal=0)
        self.session.add (st)
        self.session.commit()
        
        self.assertEquals (1, self.session.query(Scenario).count())
        self.assertEquals (1, self.session.query(Step).count())
        
        self.session.delete(st)
        self.session.commit()

        self.assertEquals (1, self.session.query(Scenario).count())
        self.assertEquals (0, self.session.query(Step).count())
        
    def test_new_step_destroy_scenario (self):
        sc = self.create_empty_scenario()
        st = Step (scenario=sc,
                    exception="",
                    duration=0,
                    fixture="",
                    kind="f",
                    status=0,
                    line=0,
                    ordinal=0)
        self.session.add (st)
        self.session.commit()
        
        self.assertEquals (1, self.session.query(Scenario).count())
        self.assertEquals (1, self.session.query(Step).count())
        
        self.session.delete(sc)
        self.session.commit()

        self.assertEquals (0, self.session.query(Scenario).count())
        self.assertEquals (0, self.session.query(Step).count())
        
    def test_new_row (self):
        st = self.create_empty_step ()
        r = Row (step=st,
                exception="",
                duration=0,
                kind="a",
                status=0,
                ordinal=0
                )
        self.session.add(r)
        self.session.commit()
        self.assertEquals (1, self.session.query(Row).count())
        self.assertEquals (1, self.session.query(Step).count())
        self.assertEquals (1, self.session.query(Scenario).count())
        self.session.delete(r)
        self.session.commit()
        self.assertEquals (0, self.session.query(Row).count())
        self.assertEquals (1, self.session.query(Step).count())
        self.assertEquals (1, self.session.query(Scenario).count())
        
    def test_new_row_destroy_step (self):
        st = self.create_empty_step ()
        r = Row (step=st,
                exception="",
                duration=0,
                kind="a",
                status=0,
                ordinal=0
                )
        self.session.add(r)
        self.session.commit()
        self.assertEquals (1, self.session.query(Row).count())
        self.assertEquals (1, self.session.query(Step).count())
        self.assertEquals (1, self.session.query(Scenario).count())
        self.session.delete(st)
        self.session.commit()
        self.assertEquals (0, self.session.query(Row).count())
        self.assertEquals (0, self.session.query(Step).count())
        self.assertEquals (1, self.session.query(Scenario).count())
        
    def test_new_column (self):
        st = self.create_empty_step ()
        c = Col (step=st,
                kind="a",
                name="",
                ordinal=0,
                tolerance=0.0
                )
        self.session.add(c)
        self.session.commit()
        self.assertEquals (1, self.session.query(Col).count())
        self.assertEquals (1, self.session.query(Step).count())
        self.assertEquals (1, self.session.query(Scenario).count())
        self.session.delete(c)
        self.session.commit()
        self.assertEquals (0, self.session.query(Col).count())
        self.assertEquals (1, self.session.query(Step).count())
        self.assertEquals (1, self.session.query(Scenario).count())
        
    def test_new_column_destroy_step (self):
        st = self.create_empty_step ()
        c = Col (step=st,
                kind="a",
                name="",
                ordinal=0,
                tolerance=0.0
                )
        self.session.add(c)
        self.session.commit()
        self.assertEquals (1, self.session.query(Col).count())
        self.assertEquals (1, self.session.query(Step).count())
        self.assertEquals (1, self.session.query(Scenario).count())
        self.session.delete(st)
        self.session.commit()
        self.assertEquals (0, self.session.query(Col).count())
        self.assertEquals (0, self.session.query(Step).count())
        self.assertEquals (1, self.session.query(Scenario).count())
        
    def test_new_cell_value (self):
        c = CellValue (
                exception="exc",
                status=0,
                f_actual=2,
                s_actual="3",
                f_expected=1,
                s_expected="4",
                hash_value_low=5,
                hash_value_high=6,
                 )
        
        self.assertEquals ("exc", c.exception)
        self.assertEquals (0, c.status)
        self.assertEquals (2, c.f_actual)
        self.assertEquals ("3", c.s_actual)
        self.assertEquals (1, c.f_expected)
        self.assertEquals ("4", c.s_expected)
        self.session.add (c)
        self.session.commit()
        self.assertEquals (1, self.session.query (CellValue).count ())
        self.assertEquals (2, self.session.query (CellValue).one ().f_actual)
        self.assertEquals (2, self.session.query (CellValue).filter_by (f_actual=2).one ().f_actual)
        
        try :
            c.f_actual = 3
            raise Exception ("Should have failed as it is forbidden")
        except AsgardImportException:
            pass
        
        self.session.commit () # That must fail and not update
        self.assertEquals (2, self.session.query (CellValue).one ().f_actual)
        
        self.session.delete (c)
        self.session.commit()
        self.assertEquals (0, self.session.query (CellValue).count ())
        
#    def test_all_rows_with_cells_is_empty_without_cells (self):
#        st = self.create_empty_step ()
#        col = self.create_empty_column (step = st)
#        row = self.create_empty_row (step = st)
#        self.assertEquals ([], st.all_rows_with_cells)
#        
    def test_new_real_cell_destroy_step (self):
        st = self.create_empty_step ()
        col = self.create_empty_column (step=st)
        row = self.create_empty_row (step=st)
        
        v = CellValue (
                 exception="",
                 status=0,
                 f_actual=0,
                 s_actual="",
                 f_expected=0,
                 s_expected="",
                 )
        c = RealCell (column=col,
                 row=row,
                 cell_value = v
                 )
        self.session.add (c)
        self.session.commit ()
        
        self.assertEquals (1, self.session.query (CellValue).count())
        self.assertEquals (1, self.session.query (RealCell).count())
        self.session.delete (st)
        self.session.commit()
        self.assertEquals (1, self.session.query (CellValue).count()) # kept forever, for now
        self.assertEquals (0, self.session.query (RealCell).count())
        
    def test_new_cells_fast_delete_batch (self):
        st = self.create_empty_step ()
        col = self.create_empty_column (step=st)
        row1 = self.create_empty_row (step=st)
        row2 = self.create_empty_row (step=st)
        
        v1 = CellValue (
                 exception="",
                 status=1,
                 f_actual=0,
                 s_actual="",
                 f_expected=0,
                 s_expected="",
                 )
        v2 = CellValue(
                 exception="",
                 status=0,
                 f_actual=0,
                 s_actual="",
                 f_expected=0,
                 s_expected="",
                 )
        c1 = RealCell (column=col,
                 row=row1,
                 cell_value=v1
                 )
        c2 = RealCell (column=col,
                 row=row2,
                 cell_value=v2
                 )
        self.session.add (c1)
        self.session.add (c2)
        self.session.commit ()
        
        self.assertEquals (2, self.session.query (RealCell).count())
        st.scenario.batch.fast_delete ()
        self.session.commit()
        self.assertEquals (0, self.session.query (RealCell).count())
        
    def test_new_step_init (self):
        s = self.create_empty_step()
        si = StepInit (step=s, name="", value="")
        self.session.add (si)
        self.session.commit ()
        self.assertEquals (1, self.session.query (StepInit).count())
        self.assertEquals (1, self.session.query(Step).count())
        self.session.delete (si)
        self.session.commit ()
        self.assertEquals (0, self.session.query (StepInit).count())
        self.assertEquals (1, self.session.query(Step).count())

    def test_new_step_init_destroy_step (self):
        s = self.create_empty_step()
        si = StepInit (step=s, name="", value="")
        self.session.add (si)
        self.session.commit ()
        self.assertEquals (1, self.session.query(StepInit).count())
        self.assertEquals (1, self.session.query(Step).count())
        self.session.delete (s)
        self.session.commit ()
        self.assertEquals (0, self.session.query(StepInit).count())
        self.assertEquals (0, self.session.query(Step).count())

    def test_new_br_prop (self):
        br = self.create_empty_batch_run()
        prop = BatchProperty (
                 value="me",
                 name="empty",
                 batch=br)
        self.session.add (prop)
        self.session.commit ()
        
        self.assertEquals (1, self.session.query(BatchProperty).count())
        self.assertEquals (1, self.session.query(Batch).count())
        self.assertEquals (prop.batch, br)
        
        self.session.delete(prop)
        self.session.commit ()
        self.assertEquals (0, self.session.query(BatchProperty).count())
        self.assertEquals (1, self.session.query(Batch).count())
        self.assertEquals (0, len(list(br.properties)))

    def test_new_br_prop_destroy_br (self):
        br = self.create_empty_batch_run()
        prop = BatchProperty (
                 value="me",
                 name="empty",
                 batch=br)
        self.session.add (prop)
        self.session.commit ()
        self.assertEquals (1, self.session.query(BatchProperty).count())
        self.assertEquals (1, self.session.query(Batch).count())
        
        self.session.delete (br)
        self.session.commit ()
        self.assertEquals (0, self.session.query(BatchProperty).count())
        self.assertEquals (0, self.session.query(Batch).count())

    def test_new_sc_prop (self):
        sc = self.create_empty_scenario(self.create_empty_batch_run())
        prop = ScenarioProperty (
                 value="me",
                 name="empty",
                 scenario=sc)
        self.session.add (prop)
        self.session.commit ()
        
        self.assertEquals (1, self.session.query(ScenarioProperty).count())
        self.assertEquals (1, self.session.query(Scenario).count())
        self.assertEquals (prop.scenario, sc)
        
        self.session.delete(prop)
        self.session.commit ()
        self.assertEquals (0, self.session.query(ScenarioProperty).count())
        self.assertEquals (1, self.session.query(Scenario).count())
        self.assertEquals (0, sc.properties.count())

    def test_new_sc_prop_destroy_sc (self):
        sc = self.create_empty_scenario(self.create_empty_batch_run())
        prop = ScenarioProperty (
                 value="me",
                 name="empty",
                 scenario=sc)
        self.session.add (prop)
        self.session.commit ()
        self.assertEquals (1, self.session.query(ScenarioProperty).count())
        self.assertEquals (1, self.session.query(Scenario).count())
        
        self.session.delete (sc)
        self.session.commit ()
        self.assertEquals (0, self.session.query(ScenarioProperty).count())
        self.assertEquals (0, self.session.query(Scenario).count())

    def test_new_st_prop (self):
        st = self.create_empty_step()
        sp = StepProperty (step=st, name="", value="")
        self.session.add(sp)
        self.session.commit()
        self.assertEquals (1, self.session.query (StepProperty).count())
        self.assertEquals (1, self.session.query (Step).count())
        self.session.delete(sp)
        self.session.commit()
        self.assertEquals (0, self.session.query (StepProperty).count())
        self.assertEquals (1, self.session.query (Step).count())

    def test_new_st_prop_destroy_st (self):
        st = self.create_empty_step()
        sp = StepProperty (step=st, name="", value="")
        self.session.add(sp)
        self.session.commit()
        self.assertEquals (1, self.session.query (StepProperty).count())
        self.assertEquals (1, self.session.query (Step).count())
        self.session.delete(st)
        self.session.commit()
        self.assertEquals (0, self.session.query (StepProperty).count())
        self.assertEquals (0, self.session.query (Step).count())

            
class TestCanReadPickles (TestCase):
    def test_can_read_pickle_1 (self):
        f = open (Utils.colocated_name ("pickles/pickle1.dbasg"), "rb")
        pickle.loads (zlib.decompress (f.read()))
        f.close ()

    def test_can_read_pickle_2 (self):
        f = open (Utils.colocated_name ("pickles/pickle2.dbasg"), "rb")
        pickle.loads (zlib.decompress (f.read()))
        f.close ()

    def test_can_read_pickle_3 (self):
        f = open (Utils.colocated_name ("pickles/pickle3.dbasg"), "rb")
        pickle.loads (zlib.decompress (f.read()))
        f.close ()

    def test_can_read_pickle_small (self):
        f = gzip.GzipFile(Utils.colocated_name ("pickles/small.asg"))
        pickle.load (f)
        f.close ()


class TestSqlAlchemyInserts (DbTestCase):
    def setUp (self):
        super (TestSqlAlchemyInserts, self).setUp()
        #self.batch_inserter = SqlAlchemyBatchInserter (session=self.session)
        self.batch_inserter = SqlAlchemyBatchInserter (uri=uri)
        with self.batch_inserter.session_provider.get_session() as session:
            Base.metadata.create_all(session.get_bind())

        self.log_inserter = SqlAlchemyRevLogsInserter (uri=uri)
        with self.log_inserter.session_provider.get_session() as session:
            Base.metadata.create_all(session.get_bind())

    def test_insert_pickle_medium_batch (self):
        version = self.create_empty_soft_version(commit=True)
        #start = time.time ()
        #import cProfile

        def insert_batch ():
            Batch.from_dict(values=batch_to_dict(medium_br,
                                             with_scenarios=True),
                        session=self.session,
                        commit=True,
                        version_id=version.id,
                        fast=True)
        #cProfile.runctx('insert_batch()', globals(), locals(), "C:\\insert.profile")
        insert_batch()
        
        #time_fast = time.time() - start
        #print "SQL Alchemy medium size import >>", time_fast


    def test_insert_pickle_large_batch (self):
        large_br = pickle.load (gzip.GzipFile(Utils.colocated_name ("pickles/large.asg")))
        version = self.create_empty_soft_version(commit=True)
        start = time.time ()
        #import cProfile

        def insert_batch ():
            Batch.from_dict(values=batch_to_dict(large_br,
                                             with_scenarios=True),
                        session=self.session,
                        commit=True,
                        version_id=version.id,
                        fast=True)
        #cProfile.runctx('insert_batch()', globals(), locals(), "C:\\insert.profile")
        insert_batch()
        
        time_fast = time.time() - start
        print "SQL Alchemy large size import >>", time_fast

    def test_insert_pickle_small_batch (self):
        start = time.time ()
        self.batch_inserter.generate (small_br)
        print "SQL Alchemy small size import from batch >>>", time.time() - start

    def test_insert_small_br_slow (self):
        b = Batch.from_batch(small_br, session=self.session)
        self.session.add (b)
        self.session.commit ()
        batch = self.session.query (Batch).one ()
        scenarios = self.session.query (Scenario)
        self.assertEquals (3, batch.scenarios.count())
        self.assertEquals (3, scenarios.count ())
        dict_from_db = batch.as_dict()
        dict_from_mem = batch_to_dict(small_br, with_scenarios=True)
        self.assertEquals(dict_from_db, dict_from_mem, "batch slow dict differ from memory dict")

    def test_insert_small_br_fast (self):
        b = Batch.from_batch(small_br, session=self.session, fast=True)
        self.session.add (b)
        self.session.commit ()
        batch = self.session.query (Batch).one ()
        scenarios = self.session.query (Scenario)
        self.assertEquals (3, batch.scenarios.count())
        self.assertEquals (3, scenarios.count ())
        dict_from_db = batch.as_dict()
        dict_from_mem = batch_to_dict(small_br, with_scenarios=True)
        self.assertEquals(dict_from_db, dict_from_mem, "batch fast dict differ from memory dict")

    def test_insert_small_br_fast_twice_and_check_equality (self):
        b1 = Batch.from_batch(small_br, session=self.session, fast=True)
        b1.uid = "a"
        self.session.add (b1)
        self.session.commit ()
        b2 = Batch.from_batch(small_br, session=self.session, fast=True)
        self.session.add (b2)
        self.session.commit ()
        batches = self.session.query (Batch).all ()
        dicts_from_db = [batch.as_dict() for batch in batches]
        for d in dicts_from_db:
            d ["uid"] = ""
        self.assertEquals (dicts_from_db[0], dicts_from_db [1], "batch dicts differ")
        
    def test_insert_fast_and_slow_simple_batch_with_lots_of_batch_props (self):
        version = self.create_empty_soft_version()
        d = dict (
            uid="",
            start_stamp=timestamp,
            name="whatever",
            context={"primebuildname": version.name},
            )
        nb = 1000
        for i in range (nb):
            d["context"]["key_%s" % i] = "value_%s" % i
        d["scenarios"] = [dict (name="bar",
                                duration=1,
                                status=0,
                                context={},
                                steps=[]
                            ),
                          dict (name="foo",
                                duration=2.0,
                                status=1,
                                context={"far":"boo"},
                                steps=[]
                            )
                          ]
        self.session.add (version)
        self.session.commit ()
        #start = time.time()
        Batch.from_dict(d, fast=True, session=self.session, version_id=version.id, commit=True)
        #print "Fast import of small batch with many props >> ", time.time() - start
        self.assertEquals (nb + 1, self.session.query (BatchProperty).count())
        #start = time.time()
        br = Batch.from_dict (d, fast=False, session=self.session)
        self.session.add (br)
        self.session.commit ()
        #print "From dict of small batch with many props  >> ", time.time() - start
        self.assertEquals (1, self.session.query (Version).count())
        self.assertEquals (2, self.session.query (Batch).count())
        self.assertEquals (nb * 2 + 2, self.session.query (BatchProperty).count())
        batches = self.session.query (Batch).all()
        self.assertEquals (batches[0].as_dict(), batches[1].as_dict())
        
    def test_insert_fast_and_slow_simple_scenario_with_lots_of_props (self):
        version = self.create_empty_soft_version()
        d = dict (
            uid="",
            start_stamp=timestamp,
            name="whatever",
            context={"primebuildname": version.name},
            )
        d["scenarios"] = [dict (name="bar",
                                duration=1,
                                status=0,
                                context={},
                                steps=[]
                            ),
                          dict (name="foo",
                                duration=2.0,
                                status=1,
                                context={},
                                steps=[]
                            )
                          ]
        nb = 1000
        for i in range (nb):
            d["scenarios"][0]["context"]["key_%s" % i] = "value_%s" % i
        self.session.add (version)
        self.session.commit ()
        start = time.time()
        Batch.from_dict(d, fast=True, session=self.session, version_id=version.id, commit=True)
        #print "Fast import of small scenario with many props >> ", time.time() - start
        self.assertEquals (nb, self.session.query (ScenarioProperty).count())
        start = time.time()
        br = Batch.from_dict (d, fast=False, session=self.session)
        self.session.add (br)
        self.session.commit ()
        #print "From dict of small scenario with many props  >> ", time.time() - start
        self.assertEquals (1, self.session.query (Version).count())
        self.assertEquals (2, self.session.query (Batch).count())
        self.assertEquals (nb * 2, self.session.query (ScenarioProperty).count())
        batches = self.session.query (Batch).all()
        self.assertEquals (batches[0].as_dict(), batches[1].as_dict())
            
    def test_insert_no_logs (self):
        class Ms ():
            messages = []
        self.log_inserter.generate_logs("4.3", Ms())
        self.assertEquals ("4.3", self.session.query (Version).one().name)
        
    def test_insert_one_log (self):
        class M ():
            action = "an action"
            spr_nb = 123456
            user_login = "foo"
            file_name = "a file"
            dir_name = "a dir"
            cc_ver_nb = 5
            branch = "a branch"
            comment = "a comment"
            gmt_datetime = datetime.datetime (2009, 12, 13)
        class Ms():
            messages = [M()]
        self.log_inserter.generate_logs("4.2", Ms())
        self.assertEquals ("4.2", self.session.query (Version).one().name)
        self.assertEquals ("a comment", self.session.query (RevLogs).one().comment)

    def test_insert_pickle_2_batch_run_and_delete (self):
        f = open (Utils.colocated_name ("pickles/pickle2.dbasg"), "rb")
        br = pickle.loads (zlib.decompress (f.read()))
        br.scenarios[0].steps[0].context ["the key"] = "the value"
        
        self.assertEquals (0, self.session.query (Batch).count ())

        self.batch_inserter.generate (br)

        db_br = self.session.query(Batch)[0]
        self.assertEquals (1, self.session.query (Batch).count ())
        self.assertEquals (20, self.session.query (BatchProperty).count ())
        self.assertEquals (1, self.session.query (Scenario).count ())
        self.assertEquals (2, self.session.query (ScenarioProperty).count ())
        self.assertEquals (6, self.session.query (Step).count ())
        self.assertEquals (3, self.session.query (StepInit).count ())
        self.assertEquals (1, self.session.query (StepProperty).count ())
        self.assertEquals (14, self.session.query (Row).count ())
        self.assertEquals (73, self.session.query (Col).count ())
        self.assertEquals (403, self.session.query (RealCell).count ())
        
        steps = self.session.query (Step).all ()
        self.assertEquals (['equity_trading.StartPrime',
                            'equity_trading.GetSnapshotData',
                            'equity_trading.RunQuoting',
                            'equity_trading.GetDataDuringQuoting',
                            'equity_trading.GetSnapshotData',
                            'equity_trading.TerminatePrimes'],
                            [step.fixture for step in steps]) 
        
        snapshot_step = steps [1]
        
        self.assertEquals (['MaximumWorkingSetSize',
                            'MinimumWorkingSetSize',
                            'WorkingSetSize',
                            'PeakVirtualSize',
                            'VirtualSize',
                            'PeakWorkingSetSize',
                            'KernelModeTime',
                            'UserModeTime',
                            'GcHeapSize',
                            'GcNumberOfCollections',
                            'GcNumberOfDisappearingLinks',
                            'GcNumberOfFinalizableObjects',
                            'GcNumberOfFreeBytes',
                            'VirtualMemorySize'], [col.name for col in snapshot_step.columns])
        self.assertEquals (1, snapshot_step.all_rows.count ())
        
        # Checking that all cells are in the right order, all the time, in all steps
        for step in steps:
            for row in step.all_rows: 
                self.assertEquals ([col.name for col in step.columns], [cell.column.name for cell in row.cells])
                
        self.assertEquals ("", steps [1].columns[1].cells[0].expected)
        self.assertEquals ("", steps [1].columns[1].cells[0].s_expected)
        self.assertEquals (None, steps [1].columns[1].cells[0].f_expected)
        self.assertEquals (204800.0, steps [1].columns[1].cells[0].actual)
        self.assertEquals (204800.0, steps [1].columns[1].cells[0].f_actual)
        self.assertEquals ("204800", steps [1].columns[1].cells[0].s_actual)
        self.assertEquals ("MinimumWorkingSetSize", steps [1].columns[1].name)
        
        # Recursive equals, in all cells
        self.assertTrue (batch_almost_eq(br, db_br))

        self.assertEquals (1, self.session.query (Version).count ())

        self.session.delete (db_br)
        self.session.commit()
        
        self.assertEquals (1, self.session.query (Version).count ())
        self.assertEquals (0, self.session.query (Batch).count ())
        self.assertEquals (0, self.session.query (BatchProperty).count ())
        self.assertEquals (0, self.session.query (Scenario).count ())
        self.assertEquals (0, self.session.query (ScenarioProperty).count ())
        self.assertEquals (0, self.session.query (Step).count ())
        self.assertEquals (0, self.session.query (StepInit).count ())
        self.assertEquals (0, self.session.query (StepProperty).count ())
        self.assertEquals (0, self.session.query (Row).count ())
        self.assertEquals (0, self.session.query (Col).count ())
        self.assertEquals (0, self.session.query (RealCell).count ())

        batch = Batch.from_batch(br, session=self.session)
        self.session.add (batch)
        self.session.commit ()
        batch = Batch.from_batch(br, session=self.session)
        self.session.add (batch)
        self.session.commit ()

        self.assertEquals (1, self.session.query (Version).count ())
        self.assertEquals (2, self.session.query (Batch).count ())

        batch.fast_delete()
        self.session.commit ()

uri = "mssql+pyodbc://ASG_ut:asgard@kantele.tqa.corp/ASG_UT"
#uri = "mssql+adodbapi://ASG_ut:asgard@kantele.tqa.corp/ASG_UT"
#uri = 'sqlite://'
#uri = 'sqlite:///C:/temp/afile.db'
session = None

def get_session ():
    global session
    #from sqlite3 import dbapi2 as sqlite
    #return create_engine('sqlite://:memory:')
    #return create_engine('sqlite:///C:/temp/afile.db')
    if session is None : 
        engine = create_engine(uri)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
    return session
    

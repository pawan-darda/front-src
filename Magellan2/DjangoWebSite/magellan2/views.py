from django.shortcuts import render_to_response 
from django.core.paginator import Paginator
from DjangoWebSite.utils import session_maker, filter_versions, filter_scenarios, filter_labels, filter_columns
from front_db.asgard_db import db_wrapper
from forms import VersionForm, ScenarioForm, GraphForm, OverviewForm
from forms import QHandler 
from sqlalchemy import desc
from django.template import RequestContext
from django.http import HttpResponseRedirect
from front_db.magellan_db.mag_db_wrapper import Wall, Portlet
from DjangoWebSite.settings import START_TAG

import datetime
#from django.conf import settings
#import DjangoWebSite

def exception404(request):
    return render_to_response('custom_error.xhtml',{'error_code':404})

def exception500(request):
    if not request.is_ajax():
        return render_to_response('custom_error.xhtml',{'error_code':500})

def index(request):
    return render_to_response('index.xhtml', {"version_tag":START_TAG})

def static (request, resource): # Could be better, but here it is for now
    return render_to_response('static/' + resource)


def graph (request):
    gr_limit = 100
    gr_count = 10
    to_graph_tuples = ()
    form = GraphForm (request.GET)

    with session_maker.asgard_read_uncommited_session_provider.get_session () as session:
        
        ver = request.GET.get("qv", "")
        baseline = request.GET.get("qbase", "")
        sc = request.GET.get("qs", "")
        col = request.GET.get("qc", "")
        lbl = request.GET.get("ql", "")
        qv = QHandler (ver) # Versions
        qs = QHandler (sc) # Scenarios
        qc = QHandler (col) # Columns
        ql = QHandler (lbl) # Labels
        qbase = QHandler (baseline) # baseline
        page = request.GET.get("page", 1)
        if form.is_valid():        
            # New algorithm: we take all tuples that correspond (scenario name, column name, label name) and we only keep the first 100.
            # Then we create the corresponding graphs.
            baseline_name = None
            baseline_name_str = ""
            if (ver or sc or col or lbl):
                if baseline :
                    baseline_query = session.query (db_wrapper.Version.name)
                    # TODO: What to do if we have no corresponding version
                    # TODO: decide if we should take the last corresponding version or the last corresponding version that contain the measure
                    # TODO: What to do if the version does not contain the corresponding measures (scenario with empty value)
                    # TODO: What to do if the version contains a negative number for a measure, or a zero
                    baseline_query = baseline_query.order_by (desc (db_wrapper.Version.main),
                                    desc(db_wrapper.Version.sub),
                                    desc(db_wrapper.Version.sub2),
                                    desc(db_wrapper.Version.hf),
                                    desc(db_wrapper.Version.p),
                                    desc(db_wrapper.Version.bn),
                                    desc(db_wrapper.Version.abn),
                                    desc(db_wrapper.Version.dat),
                                    )
                    baseline_query = filter_versions (baseline_query, qbase)
                    if baseline_query.count ():
                        baseline_name = baseline_query[0].name
                        baseline_name_str = "Baseline: " + baseline_query[0].name
                
                ver_query = session.query (db_wrapper.Version.name, db_wrapper.Version.main, db_wrapper.Version.sub)
                ver_query = filter_versions (ver_query, qv)                 
                ver_query = ver_query.order_by (desc(db_wrapper.Version.main),
                                    desc(db_wrapper.Version.sub),
                                    desc(db_wrapper.Version.sub2),
                                    desc(db_wrapper.Version.bn),
                                    desc(db_wrapper.Version.abn),
                                    desc(db_wrapper.Version.hf),
                                    desc(db_wrapper.Version.p),
                                    desc(db_wrapper.Version.dat),
                                    )
                
                last_version = ver_query.first()
    
                try:
                    main = last_version[1]
                    sub = last_version[2]
                except IndexError:
                    main = ''
                    sub = ''
    
                db_query = session.query (db_wrapper.ReportMetrics.sc_name, 
                                          db_wrapper.ReportMetrics.st_label,
                                          db_wrapper.ReportMetrics.col_name, 
                                          ).distinct()
                db_query = db_query.with_hint(db_wrapper.ReportMetrics, ' with(noexpand) ')
                                          
                                          # That is our main extraction place
                #db_query = db_query.join ((db_wrapper.ReportScenarioUniqueName, 
                #                           db_wrapper.ReportScenarioUniqueName.sc_name == db_wrapper.ReportMetrics.sc_name)) 
                #db_query = db_query.join ((db_wrapper.ReportLabelUniqueName, 
                #                           db_wrapper.ReportLabelUniqueName.st_label == db_wrapper.ReportMetrics.st_label)) 
                #db_query = db_query.join ((db_wrapper.ReportColumnUniqueName, 
                #                           db_wrapper.ReportColumnUniqueName.col_name == db_wrapper.ReportMetrics.col_name)) 
                db_query = db_query.join ((db_wrapper.Version, 
                                           db_wrapper.Version.id == db_wrapper.ReportMetrics.ver_id)) 
                db_query = db_query.order_by (db_wrapper.ReportMetrics.sc_name, 
                                                     db_wrapper.ReportMetrics.st_label,
                                                     db_wrapper.ReportMetrics.col_name)
                db_query = filter_versions (db_query, qv)
                
                # Needs some refactoring here because this filter_scenario needs NOT to use
                # some of the tables we do make joins against.
                # We should not allow status filter for instance, and maybe more than that. 
                db_query = db_query.join ((db_wrapper.ReportVersionScenario, db_wrapper.ReportVersionScenario.sc_id == db_wrapper.ReportMetrics.sc_id))
                db_query = filter_scenarios (db_query, qs, sc_name=db_wrapper.ReportMetrics.sc_name) # Only the scenarios that passed OK
                db_query = filter_labels (db_query, ql, st_label = db_wrapper.ReportMetrics.st_label) 
                db_query = filter_columns (db_query, qc, col_name = db_wrapper.ReportMetrics.col_name)
                
                to_graph_tuples = db_query[:gr_limit] # Pick the first N tuples and send them to the template
                paginator = Paginator(to_graph_tuples, gr_count) #Pagination of list.
                graph_page = paginator.page(page)
                response = render_to_response("graph.xhtml",
                                          {"form":form,
                                           "data":graph_page,
                                           "versions_filter" : "".join (request.GET.get("qv", "")),
                                           "main" : main,
                                           "sub" : sub,
                                           "baseline" : baseline_name or "",
                                           "baseline_str" : baseline_name_str,
                                           "version_tag":START_TAG
                                           #'comments' : comments
                                           },
                                           )
                return response
        
    return render_to_response("graph.xhtml",
                          {"form":form,
                           "data":(),
                           "versions_filter" : "",
                           "main" : "",
                           "sub" : "",
                           "baseline" : "",
                           "baseline_str" : "",
                           "comments" : "",
                           "version_tag":START_TAG
                           })
def version (request):
    form = VersionForm (request.GET)
    selected_version = request.GET.get('qv', '')
    qv = QHandler(selected_version)
    release = None
    component = None
        
    if qv.pos_keywords.has_key("rel") :
        release = qv.pos_keywords["rel"]
         
    if qv.pos_keywords.has_key("comp") :
        component = qv.pos_keywords["comp"]
    else :
        component = "PRIME"
        
    if form.is_valid():
        # Warning: don't close the session here, as the data we give to the template uses it.
        return render_to_response("version.xhtml",
                                  {'form':form,
                                   'qv':selected_version,
                                   'release':release or "",
                                   'component' : component or "",
                                   "version_tag":START_TAG
                                   },
                                   context_instance=RequestContext(request)
                                   )
        
    return render_to_response("version.xhtml", {'form':form,
                                                "version_tag":START_TAG })
    
def scenario(request):
    # TODO : replace the creation of the content of the first table (scenarios and versions) by a table that self-fill itself out of
    # ajax requests. Implement paging in bioth directions (versions / scenarios)
    # That would just make this page simpler and the page more responsive and functionally more complete.
    sc_limit = 40 # Number of scenarios to show (max number)
    v_limit = 30 # Number of versions to show (max number)
    page = request.GET.get("page", 1)

    q_string = request.META.get("QUERY_STRING").split("&")
    q_string = [q for q in q_string if not q.startswith("page")]
    base_url = "http://%s%s?%s"%(request.META.get("HTTP_HOST"), 
                                 request.path, 
                                 "&".join(q_string))
    
    
    
    form = ScenarioForm (request.GET)
        
    if form.is_valid():
        with session_maker.asgard_read_uncommited_session_provider.get_session() as session :
            class ScenarioAndVersions ():
                """A class that will help us encapsulate information about each scenario
                sc_name is the _name_ of the scenario
                The data is a list of _dictionaries_ related to the versions we
                want to display. The dictionaries are ordered as the versions are"""
                def __init__ (self, s):
                    self.sc_name = s
                    self.statuses = None
                def __str__ (self): 
                    return self.sc_name
                
            # Algorithm:
            # 1- Get all matching versions for version selector only. We want to know if the scenarios have been run in these versions or not, therefore
            # We need all of them, even if the scenarios have not been run.
            # 2- Find all corresponding tuples (scenario / version)
            # 3- Create a list of scenarios, each of them containing a list of version information about the version status
            
            # Part 1 : getting all version names.
            # Preparing data for the passing / failing / missing graph on the right of the scenario names
            # Here we pick all the versions to correspond to the version pattern
            # We ignore the scenario filter (picking _all_ versions that correspond to the version pattern,
            # not only the ones with the scenario pattern
            v_query = filter_versions (session.query (db_wrapper.Version), QHandler (request.GET.get("qv", "")))
            v_query = v_query.order_by (desc(db_wrapper.Version.main),
                                    desc(db_wrapper.Version.sub),
                                    desc(db_wrapper.Version.sub2),
                                    desc(db_wrapper.Version.bn),    
                                    desc(db_wrapper.Version.abn),
                                    desc(db_wrapper.Version.hf),
                                    desc(db_wrapper.Version.p),
                                    desc(db_wrapper.Version.dat),
                                    )
            last_version = v_query.first ()
            # FILTER NOT WORKING since .main and .sub are NONE
            v_query = v_query.filter_by (main=last_version.main).filter_by (sub=last_version.sub)            
            versions = v_query[:v_limit]
            version_names = list (v.name for v in versions)
            
            # Part 2 : we want to query the report-oriented-tables to get the results for the scenarios we target and the versions we target.
            # To get even faster we use 3 tables: the version table itself to select the versions, the unique-scenario-name for the scenario names
            # and the table with version-and-scenarios. This last table is the one that has been designed to go as fast as possible when extracting
            # scenario results.
            
            db_query = session.query (db_wrapper.ReportVersionScenario.sc_name).distinct()
            db_query = db_query.join ((db_wrapper.ReportScenarioUniqueName, db_wrapper.ReportScenarioUniqueName.sc_name == db_wrapper.ReportVersionScenario.sc_name))
            db_query = db_query.join ((db_wrapper.Version, db_wrapper.Version.id == db_wrapper.ReportVersionScenario.ver_id))
            db_query = db_query.filter (db_wrapper.Version.main==last_version.main).filter (db_wrapper.Version.sub==last_version.sub)
            db_query = db_query.order_by (db_wrapper.ReportVersionScenario.sc_name)
            db_query = filter_versions (db_query, QHandler (request.GET.get("qv", "")), session, True)
            db_query = filter_scenarios (db_query, QHandler (request.GET.get("qs", "")))
            
            data = db_query [:]
            paginator = Paginator(data , sc_limit) #Pagination of list.
            sc_data = paginator.page(page)

            scenario_names = list (ScenarioAndVersions (s.sc_name) for s in sc_data.object_list)
        
            # Here we have the number of scenario _names_ we found
            scenario_names_nb = db_query.count()
            
            # We want to display if and only if the id of the one we want to display is present
            # Later maybe also if we have only one scenario that was found
            sc_to_display_id = request.GET.get("qsid", 0)
            scenario_to_display = session.query(db_wrapper.Scenario).filter_by (id=sc_to_display_id).first()
    
            if scenario_to_display is not None and scenario_to_display.name not in (s.sc_name for s in scenario_names):
                scenario_to_display = None
            first_failing_step = None
            if scenario_to_display : 
                first_failing_step = scenario_to_display.steps.filter (db_wrapper.Step.status <> 1).first ()
            
            # Now we want to know the status of the the scenarios we look at
            # So first we create a query that returns all version / scenario status.
            v_s_query = (session.query (db_wrapper.ReportVersionScenario.ver_name, 
                                        db_wrapper.ReportVersionScenario.sc_name, 
                                        db_wrapper.ReportVersionScenario.sc_status, 
                                        db_wrapper.ReportVersionScenario.sc_id, 
                                        )
                         .filter (db_wrapper.ReportVersionScenario.ver_name.in_(version_names))
                         .filter (db_wrapper.ReportVersionScenario.sc_name.in_(list (s.sc_name for s in scenario_names)))
                         )
            res = v_s_query.all ()
            
            #statuses is a dictionary with (version name, scenario name) as key and {status, id} as value.
            statuses = dict (((tup[0], tup[1]), {'status':tup[2], 
                                                 'id':tup[3]
                                                 }) for tup in res)
            
            # Now we populate the scenario_names with information about the versions we display
            # We put None as a default value (UNKNOWN)
            for sc in scenario_names:
                sc.statuses = list (statuses.get ((v, sc.sc_name), None) for v in version_names)
            
            class VersionWrapper (object):
                """This class is meant to be used to display the version names at the top of the tab with all scenarios
                and versions. The main reason for it is that it will tell how many columns have the same value,
                enabling us to write "colspan" in cells
                """
                def __init__ (self, version):
                    self.version = version
                    self.nice_main_sub_nb = 1
                    self.bn_nb = 1
                    self.abn_nb = 1
                    self.dat_nb = 1
                    self.status = {}
              
            # Here we create a list of information that can be used to create a table with colspan      
            v_wrappers = list (VersionWrapper (v) for v in versions)
            for i in range (len(v_wrappers) - 1, 0, -1):# From last to nb 1 (ie not 1st but6 second).
                if (v_wrappers[i].version.nice == v_wrappers[i - 1].version.nice and 
                    v_wrappers[i].version.main == v_wrappers[i - 1].version.main and
                    v_wrappers[i].version.sub == v_wrappers[i - 1].version.sub) :
                    v_wrappers[i - 1].nice_main_sub_nb = v_wrappers[i].nice_main_sub_nb + 1
                    v_wrappers[i].nice_main_sub_nb = 0
                if v_wrappers[i].version.dat == v_wrappers[i - 1].version.dat:
                    v_wrappers[i - 1].dat_nb = v_wrappers[i].dat_nb + 1
                    v_wrappers[i].dat_nb = 0
                if v_wrappers[i].version.bn == v_wrappers[i - 1].version.bn:
                    v_wrappers[i - 1].bn_nb = v_wrappers[i].bn_nb + 1
                    v_wrappers[i].bn_nb = 0
                if v_wrappers[i].version.abn == v_wrappers[i - 1].version.abn:
                    v_wrappers[i - 1].abn_nb = v_wrappers[i].abn_nb + 1
                    v_wrappers[i].abn_nb = 0
                           
            # Warning: don't close the session here, as the data we give to the template uses it.
    
            # This one takes too long too.
            # We may need to improve our template.

            
            return render_to_response("scenario.xhtml",
                                      {'form':form,
                                       'scenario_names':scenario_names,
                                       'cut':db_query.count() > sc_limit,
                                       'scenario_names_nb':page,
                                       'scenario': scenario_to_display, # The scenario to display if any
                                       'now':datetime.datetime.now(),
                                       'first_failing_step': first_failing_step,
                                       'versions': v_wrappers, # The structure that encapsulates the list of versions
                                       'url': base_url,
                                       'data' : sc_data,
                                       "version_tag":START_TAG
                                       },
                                       )
    return render_to_response("scenario.xhtml", {'form':form,
                                              'scenarios_nb':0,
                                              "version_tag":START_TAG})
def shortcuts(request):
    """
    Here we generate the data for shortcuts form
    """
    with session_maker.asgard_read_uncommited_session_provider.get_session() as session :
    
        #Get the distinct scenarios names
        sc_query = session.query (db_wrapper.ReportMetrics.sc_name).distinct ()
        sc_query = sc_query.with_hint(db_wrapper.ReportMetrics, ' with(noexpand) ')
        sc_query = sc_query.order_by (db_wrapper.ReportMetrics.sc_name)
        sc_query = sc_query.filter (db_wrapper.ReportMetrics.main <> 555) # For some strange reason, the server needs that to be fast

                            
        return render_to_response('shortcut.xhtml',
                                       {'to_display':[sc.sc_name for sc in sc_query],
                                        "version_tag":START_TAG
                                        })
    

def overview(request):
    """
    Here we generate the performance overiew page with
    """
    with session_maker.asgard_read_uncommited_session_provider.get_session() as session :
        form = OverviewForm(request.GET)
        display_set = 20
        
        if form.is_valid():            
            ver = request.GET.get("qv", "")
            sc = request.GET.get("qs", "")
            baseline = request.GET.get("qbase", "")
    
            if (ver and sc ):
                qs = QHandler (sc) # Scenarios
                qv = QHandler (ver)
                qbase = QHandler (baseline) # baseline
                
                ver_query = session.query(db_wrapper.Version.nice,
                                          db_wrapper.Version.main,
                                          db_wrapper.Version.sub).distinct()
                
                ver_query = filter_versions(ver_query, qv)
                ver_list = ver_query.all()
    
                if ver_list:
                    try:
                        main = ver_list[0][1]
                        sub = ver_list[0][2]
                        nice = str(main) + "." + str(sub)
                    except IndexError:
                        main = ''
                        sub = ''
                        nice = ''
                        
                    baseline_name = None
                    baseline_name_str = ""
                
                    if baseline :
                        baseline_query = session.query (db_wrapper.Version.name)
                        # TODO: What to do if we have no corresponding version
                        # TODO: decide if we should take the last corresponding version or the last corresponding version that contain the measure
                        # TODO: What to do if the version does not contain the corresponding measures (scenario with empty value)
                        # TODO: What to do if the version contains a negative number for a measure, or a zero
                        baseline_query = baseline_query.order_by (desc (db_wrapper.Version.main),
                                        desc(db_wrapper.Version.sub),
                                        desc(db_wrapper.Version.sub2),
                                        desc(db_wrapper.Version.hf),
                                        desc(db_wrapper.Version.p),
                                        desc(db_wrapper.Version.bn),
                                        desc(db_wrapper.Version.abn),
                                        desc(db_wrapper.Version.dat),
                                        )
                        baseline_query = filter_versions (baseline_query, qbase)
                        
                        if baseline_query.count ():
                            baseline_name = baseline_query[0].name
                            baseline_name_str = "Baseline: " + baseline_query[0].name
                        
                    # Get the scenario searched
                    db_query = session.query (db_wrapper.ReportScenarioUniqueName.sc_name).distinct()      
                    db_query = db_query.order_by (db_wrapper.ReportScenarioUniqueName.sc_name)
                    db_query = filter_scenarios (db_query, qs)     
                    
                    sc_list = db_query.all()
                    sc_list = [sc[0] for sc in sc_list]
                    
                    db_query = session.query(db_wrapper.ReportMetrics.sc_name)
                    db_query = db_query.with_hint(db_wrapper.ReportMetrics, ' with(noexpand) ')
                    db_query = db_query.filter(db_wrapper.ReportMetrics.main == main)
                    db_query = db_query.filter(db_wrapper.ReportMetrics.sub == sub)
                    db_query = db_query.filter(db_wrapper.ReportMetrics.sc_name.in_(sc_list)).distinct()
                    
                    scenarios = db_query[:display_set]
                    
                    # vstr = "%s.%s" %( main,sub)
                    if  int(main) == 4 and int(sub) >= 7 :
                        column_label = [('Effect of loading sheet after GC', 'gc_used_kilobytes'),
                                        ('Effect of loading sheet after GC', 'vm_kilobytes_size'),
                                        ('Effect of loading sheet before GC', 'used_cpu_s'),
                                        ('Measure of loading sheet after GC', 'nb_nodes')]
                    else : 
                        column_label = [('Start up diff with GC', 'gc_used_kilobytes'),
                                        ('Start up diff with GC', 'vm_kilobytes_size'),
                                        ('Start up diff before GC', 'used_cpu_s'),
                                        ('Start up GC', 'nb_nodes')]                        
                    
                    return render_to_response("overview.xhtml",
                                              {'form':form,
                                               'to_display':scenarios,
                                               'baseline' : baseline_name or "",
                                               'baseline_str' : baseline_name_str,
                                               'version_nice' : nice,
                                               'versions_filter' : "".join (request.GET.get("qv", "")),
                                               'baseline_filter' : "".join (request.GET.get("qbase", "")),
                                               'column_label':column_label,
                                               "version_tag":START_TAG})
    #Make sure that we close the session under any circumstances.
    return render_to_response('overview.xhtml', {'form':form,
                                                 'to_display':(),
                                                 'versions_filter' : "",
                                                 'baseline_filter' : "",
                                                 'version_nice':"",
                                                 'baseline' : "",
                                                 'baseline_str' : "",
                                                 'column_label':(),
                                                 "version_tag":START_TAG})

def wall(request):
    """
    Here we generate the wall page
    """
    try :
        with session_maker.magellan_read_uncommited_session_provider.get_session() as session :
            wall_name= request.REQUEST.get("name","")
            wall_refresh= request.REQUEST.get("refresh","true")
            wall_description = ""
            max_col = 3
            grouped_portlets = []
            while max_col > 0:
                grouped_portlets.append([])
                max_col = max_col  - 1        
    
            if wall_name:
                query = session.query(Wall).filter(Wall.name == wall_name)
                wall_data = query.all()
                if len(wall_data) == 1:
                    wall_id =  wall_data[0].id
                    wall_description = wall_data[0].description 
                    portlet_query = session.query(Portlet).filter(Portlet.wall_id == wall_id)
                    portlet_query = portlet_query.order_by (Portlet.position)
                    portlets = portlet_query.all ()
    
                    if len(portlets) != 0:        
                        for portlet in portlets:
                            temp_col = int(portlet.position[0]) - 1                       
                            grouped_portlets[temp_col].append(portlet)
    
                    wall_name = wall_data[0].name
                else :
                    return HttpResponseRedirect("../magellan2/wall")
                
            return  render_to_response("wall.xhtml",{       
                                                   'wallname': wall_name,
                                                   'wallrefresh':wall_refresh,
                                                   'description' : wall_description,
                                                   'portlets' : grouped_portlets,
                                                   "version_tag":START_TAG}  
                                                   )
    except Exception:
        return HttpResponseRedirect("../magellan2/wall")    
        

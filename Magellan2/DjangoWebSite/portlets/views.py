from front_db.asgard_db import db_wrapper
import json
import ast
from django.http import HttpResponse, HttpResponseServerError
from DjangoWebSite import settings
from front_db.fast_db import direct_wrapper
from django.shortcuts import render_to_response
from front_db.magellan_db.mag_db_wrapper import Wall, Portlet
from DjangoWebSite.utils import session_maker
from django.template.loader import render_to_string
from sqlalchemy import func, desc, and_, or_
from front_db.asgard_db.db_wrapper import Version, ReportMetrics
from front_db.asgard_db.db_wrapper import ReportVersionScenario, UnitTestStatus
from front_db.asgard_db.db_wrapper import UnitTestRun, UnitTest, Status
from django.core.cache import cache
from DjangoWebSite.portlets.PortletUtils.build_status import BuildStatusDetails
from front_utils.versions import get_version
import os
import datetime
import itertools

__FAST_SERVER = settings.FAST_SERVER

def delete_wall (request):
    """
    Deletes an existing wall
    """
    try :
        with session_maker.magellan_write_session_provider.get_session() as session :
            wall_name = request.REQUEST.get("wall_name", "")
            wall_query = (session.query(Wall)).filter(Wall.name == wall_name)
            wall = wall_query.one ()
            wall.portlets.delete ()
            wall_query.delete()
            return HttpResponse("Done")
    except Exception:
        session.rollback()
        return HttpResponse("Failed")

def find_wall(request):
    """
    find a wall with given name , description
    """
    with session_maker.magellan_read_uncommited_session_provider.get_session() as session:
        query = session.query(Wall)
        #Getting Data table related values
        iDisplayStart = request.GET.get("iDisplayStart", "").strip() or 0
        iDisplayLength = request.GET.get("iDisplayLength", "").strip() or 0
        isEcho = request.GET.get ("sEcho", "").strip() or 0
        sSearch = request.GET.get("sSearch", "").strip() or None

        totalRecords = query.count()
        totalFilteredRecords = totalRecords
        
        # Adding search related queries 
        if sSearch != None:            
            sSearchLst = sSearch.split(" ")
            for isSearch in sSearchLst:
                iSearch = '%' + isSearch + '%'
                query = query.filter(or_(Wall.name.ilike(iSearch),
                                         Wall.description.ilike(iSearch)))
            totalFilteredRecords = query.count()
        query = query.order_by(Wall.name)
        walldata = query[int(iDisplayStart):int(iDisplayStart) + int(iDisplayLength)]
        
        output = {}
        output["sEcho"] = isEcho 
        output["iTotalRecords"] = totalRecords
        output["iTotalDisplayRecords"] = totalFilteredRecords  
        tmpLst = []
        
        for wall in walldata:
            tableCol = render_to_string('open_wall.xhtml', {"wall":wall})
            tableCol = tableCol.replace('\n', '')
            tmpLst.append([tableCol])
             
        output["aaData"] = tmpLst
        tempJson = json.dumps(output)
 
        tempJson = tempJson.replace("None", " ")
        tempJson = tempJson.replace('\n', '')
                
        response = HttpResponse()
        response.write(tempJson)
        return response
    
def update_postion(request):
    """
      Updates the portlet position.
    """     
    data = request.REQUEST.get("port_data")
    update_data = ast.literal_eval(data)
    try :
        with session_maker.magellan_write_session_provider.get_session() as session :
            for key, value in update_data.items():
                query = (session.query(Portlet)).filter(Portlet.id == key)
                query.update(values={Portlet.position:value})
            return HttpResponse("Successfully updated portlet")
    except Exception , err:
        return HttpResponseServerError(str(err))

def create_wall(request):
    """
      Here we create new wall
    """
    try :
        with session_maker.magellan_write_session_provider.get_session() as session :
            wall_name = request.REQUEST.get("name", "")
            wall_desc = request.REQUEST.get("description", "--")
            
            query = (session.query(Wall)).filter(Wall.name == wall_name)
            if query.count() == 1:
                return HttpResponseServerError("Wall name in use")   
            session.add(Wall(name=wall_name,
                             description=wall_desc))
            return HttpResponse("Done")
    except:
        return HttpResponseServerError("Failed")
        
def add_portlet(request):
    """
        Adds portlet data to the db
    """
    try :
        with session_maker.magellan_write_session_provider.get_session() as session :
            portlet_type = request.REQUEST.get("ptype")
            wall_name = request.REQUEST.get("wall_id", "")
            portlet_position = request.REQUEST.get("portlet_position")
            portlet_argument = request.REQUEST.get("data")
            portlet_title = request.REQUEST.get("title", "")
            portlet_wall = (session.query(Wall)\
                            .filter(Wall.name == wall_name)[0])
            portlet = Portlet(type=portlet_type,
                                argument=portlet_argument,
                                position=portlet_position,
                                title=portlet_title,
                                wall=portlet_wall)
            session.add(portlet)
            # commit session manually so portlet object can be updated with an id
            session.session.commit()
            return render_to_response("portlet.xhtml", {"portlet": portlet})
    except KeyError:
        return HttpResponseServerError("Insufficient parameters provided")
    except Exception, err:
        return HttpResponseServerError(str(err))

def build_sprs(request):
    """
    Function to get the sprs contained within a build
    """
    main = request.REQUEST.get ("main", "") 
    sub = request.REQUEST.get ("sub", "")
    build_val = request.REQUEST.get ("build", "")
    with session_maker.fast_read_uncommited_session_provider.get_session() as session :
        db_query = session.query (direct_wrapper.get_FAST_class("BuildNumber", session))
        db_query = db_query.filter_by (major=main)
        db_query = db_query.filter_by (minor=sub)
        db_query = db_query.filter_by (bnumber=build_val)
        #@todo: we need to also take the branches into account. For now it does not work.
        first = db_query.first ()
        if first is None : 
            l = []
        else:
            l = [s.strip () for s in first.clean_sprs_included.split (";") if s.strip()]
        spr_query = session.query (direct_wrapper.get_FAST_class("SPREntry", session))
        spr_query = spr_query.filter (direct_wrapper.get_FAST_class("SPREntry", session).spr_id.in_ (l))
        spr_query = spr_query.filter (direct_wrapper.get_FAST_class("1:SPREntry", session).spr_id <> 264097) # generic build spr
        spr_query = spr_query.filter (direct_wrapper.get_FAST_class("1:SPREntry", session).spr_id <> 260796) # generic build spr
        sprs = spr_query.count()
        return render_to_response('spr_count.xhtml',
                                       {'build':"%s.%s.%s" % (main, sub, build_val),
                                        'spr_count':sprs
                                        })

def delete_portlet(request):
    try :
        with session_maker.magellan_write_session_provider.get_session() as session :
            portlet_id = request.REQUEST.get("portlet_id", "")
            query = (session.query(Portlet)).filter(Portlet.id == portlet_id)
            query.delete()
            return HttpResponse("Successfully deleted portlet")
    except Exception , err:
        return HttpResponseServerError(str(err))

def edit_wall(request):
    """
        Updating the wall database for the new wall name and description
        Avoiding duplicate name.
    """
    try:
        with session_maker.magellan_write_session_provider.get_session() as session :
            old_name = request.REQUEST.get("old_name", "")
            new_name = request.REQUEST.get("new_name", "")
            wall_desc = request.REQUEST.get("description", "--")
    
            query = (session.query(Wall)).filter(Wall.name == new_name)
            if query.count() == 1 and new_name != old_name:
                return HttpResponseServerError("Wall name in use")
            else:
                query = (session.query(Wall)).filter(Wall.name == old_name)
                query.update(values={Wall.name:new_name, Wall.description:wall_desc})
                return HttpResponse("done")
    except Exception, err:
        return HttpResponseServerError(str(err))
            
def get_nice_name(request):
    """
        Gets the matching Nice name list for Autocomplete field on portlets
        where Nice name is a parameter required for adding the portlet
    """
    with session_maker.asgard_read_uncommited_session_provider.get_session() as session :
        # get the q value from requet.GET
        # get corresponding data and return 
        val = request.GET.get("term", "")
        ival = val + '%'
        v_query = session.query (Version.nice).distinct()
        v_query = v_query.filter(Version.abn == 0)
        v_query = v_query.filter(Version.nice.like(ival))
        v_query = v_query.order_by (Version.nice)
        v_query = v_query[:10]
        data = [v.nice for v in v_query if v.nice]
        return HttpResponse(json.dumps(data), mimetype='application/javascript')
    
def get_branch_name(request):
    """
        Gets the matching Branch name list for Autocomplete fields on portlets
        where Branch name is a parameter required for adding the portlet
    """
    with session_maker.asgard_read_uncommited_session_provider.get_session() as session :
        # get the q value from requet.GET
        # get corresponding data and return 
        val = request.GET.get("term", "")
        ival = '%' + val + '%'
        
        v_query = session.query (ReportVersionScenario.br_name).distinct()
        v_query = v_query.filter(ReportVersionScenario.br_name.like(ival))
        v_query = v_query.order_by (ReportVersionScenario.br_name)
        v_query= v_query[:10]
        data = [v.br_name for v in v_query if v.br_name]
        return HttpResponse(json.dumps(data), mimetype='application/javascript')

def get_pg_scenario(request):
    """
        Gets the matching Scenario name list for Autocomplete fields on portlets
        filtering the Scenarios on the version selected.
    """ 
    try:   
        with session_maker.asgard_read_uncommited_session_provider.get_session() as session :
            # get the q value from requet.GET
            # get corresponding data and return 
            val = request.GET.get("term", "")
            nice = request.GET.get("nice", "")
    
            ival = '%' + val + '%'
            inice = nice + '%'
    
            db_query = session.query (db_wrapper.ReportMetrics.sc_name).distinct()
            db_query = db_query.with_hint(db_wrapper.ReportMetrics, ' with(noexpand) ')
            db_query = db_query.order_by (db_wrapper.ReportMetrics.sc_name)
            
            if nice != '': 
                db_query = db_query.filter (db_wrapper.ReportMetrics.nice.ilike(inice))
            if val != '':
                db_query = db_query.filter (db_wrapper.ReportMetrics.sc_name.ilike(ival))
                
            column_filter = db_query[:5]
            col_data = [v.sc_name for v in column_filter]
            
            return HttpResponse(json.dumps(col_data), mimetype='application/javascript')
    except Exception, err:
        return HttpResponseServerError(str(err))

def get_pg_column(request):
    """
        Gets the matching Column name list for Autocomplete fields on portlets
        filtering the Column on the version, scenario and label selected.
    """ 
    try :
        with session_maker.asgard_read_uncommited_session_provider.get_session() as session :
            # get the q value from requet.GET
            # get corresponding data and return 
            val = request.GET.get("term", "")
            nice = request.GET.get("nice", "")
            scenario = request.GET.get("scenario", "")
            label = request.GET.get("label", "")
            
            ival = '%' + val + '%'
            inice = nice + '%'
            iscenario = '%' + scenario + '%'
            ilabel = '%' + label + '%'
    
            db_query = session.query (db_wrapper.ReportMetrics.col_name).distinct()
            db_query = db_query.with_hint(db_wrapper.ReportMetrics, ' with(noexpand) ')
            db_query = db_query.order_by (db_wrapper.ReportMetrics.col_name)
            if nice != '': 
                db_query = db_query.filter (db_wrapper.ReportMetrics.nice.ilike(inice))
            if scenario != '':
                db_query = db_query.filter (db_wrapper.ReportMetrics.sc_name.ilike(iscenario))
            if label != '':
                db_query = db_query.filter (db_wrapper.ReportMetrics.st_label.ilike(ilabel))
            if val != '':
                db_query = db_query.filter (db_wrapper.ReportMetrics.col_name.ilike(ival))
                
            column_filter = db_query[:5]
            col_data = [v.col_name for v in column_filter]
    
            return HttpResponse(json.dumps(col_data), mimetype='application/javascript')
    except Exception, err:
        return HttpResponseServerError(str(err))

def get_pg_label(request):
    """
        Gets the matching Label name list for Autocomplete fields on portlets
        filtering the Label on the version and scenario selected.
    """     
    try :
        with session_maker.asgard_read_uncommited_session_provider.get_session() as session :
            # get the q value from requet.GET
            # get corresponding data and return
            val = request.GET.get("term", "")
            nice = request.GET.get("nice", "")
            scenario = request.GET.get("scenario", "")
            
            ival = '%' + val + '%'
            inice = nice + '%'
            iscenario = '%' + scenario + '%'
     
            db_query = session.query (db_wrapper.ReportMetrics.st_label).distinct()
            db_query = db_query.with_hint(db_wrapper.ReportMetrics, ' with(noexpand) ')
            db_query = db_query.order_by (db_wrapper.ReportMetrics.st_label)
    
            if nice != '': 
                db_query = db_query.filter (db_wrapper.ReportMetrics.nice.ilike(inice))
            if scenario != '':
                db_query = db_query.filter (db_wrapper.ReportMetrics.sc_name.ilike(iscenario))
            if val != '':
                db_query = db_query.filter (db_wrapper.ReportMetrics.st_label.ilike(ival))
    
            scenario_filter = db_query[:5]
            scenario_data = [v.st_label for v in scenario_filter]
            
            return HttpResponse(json.dumps(scenario_data), mimetype='application/javascript')
    except Exception, err:
        return HttpResponseServerError(str(err))

def get_bs_nicename (request):
    """
        Gets the matching Nice name list for Autocomplete field on portlets specifically for build status portlet
        where Nice name is a parameter required for adding the portlet.
    """
    componentgroup = request.GET.get("componentgroup", "")
    search_nicename = request.GET.get("term", "")
    cache_status = cache.get ('build_dict', 'has_expired') 
    if cache_status == 'has_expired':
        build_dict, platform, component_group = initialize_build_dict()
    else:
        build_dict = cache.get('build_dict') 
    key_list = build_dict[componentgroup].keys()
    matched = [key for key in key_list if not key.find(search_nicename)]
    return HttpResponse(json.dumps(matched[:5]), mimetype='application/javascript')

def get_bs_componentgroup (request):
    """
        Gets the matching Nice name list for Autocomplete field on portlets specifically for build status portlet
        where Nice name is a parameter required for adding the portlet.
    """
    search_componentgroup = request.GET.get("term", "")
    cache_status = cache.get ('build_dict', 'has_expired') 
    if cache_status == 'has_expired':
        build_dict, platform, component_group = initialize_build_dict()
    else:
        build_dict = cache.get('build_dict') 
    key_list = build_dict.keys()
    matched = [key for key in key_list if not key.find(search_componentgroup)]
    return HttpResponse(json.dumps(matched[:5]), mimetype='application/javascript')
    


def asg_scenario(request):
    """
    Function to get the Asgard Scenario portlet content.
    """
    with session_maker.asgard_read_uncommited_session_provider.get_session() as session :
        sc_query = session.query (ReportVersionScenario.sc_name,
                                  ReportVersionScenario.br_name,
                                  ReportVersionScenario.nice,
                                  ReportVersionScenario.ver_name,
                                  ReportVersionScenario.main,
                                  ReportVersionScenario.sub,
                                  ReportVersionScenario.bn)

        val = request.REQUEST.get("nicename", "")
        ival = val + '%'
        sc_query = sc_query.filter (ReportVersionScenario.nice .ilike(ival))
        sc_query = sc_query.filter (ReportVersionScenario.abn == 0)
        sc_query = sc_query.filter(ReportVersionScenario.br_name == request.REQUEST.get("set", ""))

        # Added filter to remove 'pending 'scenario implementation from count
        sc_query = sc_query.filter (ReportVersionScenario.sc_impl == None)
        
        # sort to get the latest build
        sc_query = sc_query.order_by (desc(ReportVersionScenario.main),
                                      desc(ReportVersionScenario.sub),
                                       desc(ReportVersionScenario.bn))
        last = sc_query.first()
        sc_query = sc_query.filter(ReportVersionScenario.bn == last.bn)        
        failed = sc_query.filter(ReportVersionScenario.sc_status == 2)
        erred = sc_query.filter(ReportVersionScenario.sc_status == 3)
        
        failed_count = failed.count()
        passed_count = sc_query.filter(ReportVersionScenario.sc_status == 1).count()
        error_count = erred.count()

        last.prime = get_version('PRIME', last.ver_name)
        # Notify user if the build is more than one day old and build is not in top 3 builds for the track
        expired_build = ''
        if check_expired_build(last.prime):
            expired_build = 'asg_red'
                
        return render_to_response("asg_scenario.xhtml", {
                    "failed_count": failed_count,
                    "passed_count": passed_count,
                    "error_count": error_count,
                    "failed": failed[:5],
                    "erred": erred[:5],
                    "last": last,
                    "nice_display":val,
                    "expired_build":expired_build })
        
        
def check_expired_build (prime):
    """
        Check if build is more than one day old
        and 
        Not in top 3 builds for particular track.
    """
    with session_maker.asgard_read_uncommited_session_provider.get_session() as session :
        inice = prime.nice + '%'
        
        day_diff = datetime.date.today() - prime.date.date() 
        
        versions_query = session.query(Version).distinct()
        versions_query = versions_query.filter (Version.nice.ilike(inice))
        versions_query = versions_query.filter (Version.abn == 0)
        
        versions_query = versions_query.order_by (desc (Version.main),
                                                  desc (Version.sub),
                                                  desc (Version.bn))
        versions_data = versions_query[:3]
        if len(versions_data) == 3:
            version_list = [versions_data[0].bn,versions_data[1].bn,versions_data[2].bn]
            if abs(day_diff.days) > 1  and prime.bn not in version_list:
                return True
    return False
    

def get_build_status_details(detailed_dict):
    """
    Getting the build status and branch for the particular build number selected.
    """
    platforms = cache.get('build_platforms') 
    status_list = []
    for platform in platforms:
        try:
            status_list.append('status_' + detailed_dict[platform].buildStatus)
        except Exception:
            status_list.append ('build_not_available')

    return status_list, detailed_dict[detailed_dict.keys()[0]].branch


def initialize_build_dict():
    """
    Function to parse the status log file to get the build details and platforms
    Data parsed is also being cached. 
    """
    
    """
    If in debug mode locate status log file from clear case folder is parsed. 
    If on server file from service folder is parsed. 
    """
    if settings.QuickBuildLogPath == 'Debug':
        path = __file__.split(os.path.sep)
        path.pop()
        qbuild_log_dir = os.path.sep.join(path)
        qbuild_log_path = "%s%s%s" % (qbuild_log_dir, os.path.sep, 'qb_status.txt')
    else:
        qbuild_log_path = settings.QuickBuildLogPath
    
    f = open(qbuild_log_path)    
    data_file = f.readlines()
    f.close()
    all_builds = []
    build_dict = {}
    for line in data_file:
        all_builds.append(BuildStatusDetails (line))
    platforms = []
    component_group = []
    for bs_object in all_builds:
        build_nicebranch = bs_object.nicebranch
        buildType = bs_object.buildType
        if buildType == "release": #Filter to get the release builds.
            if not build_dict.has_key(bs_object.componentGroup):
                build_dict[bs_object.componentGroup] = {}
            if  not build_dict[bs_object.componentGroup].has_key (build_nicebranch):
                build_dict[bs_object.componentGroup][build_nicebranch] = {}
            build_dict[bs_object.componentGroup][build_nicebranch][bs_object.platform] = bs_object
            platforms.append (bs_object.platform)
            component_group.append (bs_object.componentGroup)
    platforms = list(set(platforms))
    component_group = list(set(component_group))
    platforms.sort()
    platforms.reverse()
    component_group.sort()
    cache.set('build_platforms', platforms , 360)   #Caching the parsed data for 6 min. (360 sec)
    cache.set('build_dict', build_dict , 180) #Caching the parsed data for 3 min. (180 sec)
    return build_dict, platforms, component_group

def build_status(request):
    """
    Function to get the Build Status data for portlet content.
    """
    #Widget under maintenance.
    '''
    cache_status = cache.get ('build_dict', 'has_expired') 
    if cache_status == 'has_expired':
        build_dict, platforms, component_group = initialize_build_dict()
    else:
        build_dict = cache.get('build_dict')
        platforms = cache.get('build_platforms') 
        
    nicename = request.REQUEST.get("bs_nicename", "").strip()
    component_group = request.REQUEST.get("bs_componentgroup", "").strip()
    status_list, branch = get_build_status_details (build_dict[component_group][nicename])
    return render_to_response("Build_Status.xhtml", {
                "build_status":status_list,
                "nicename": nicename,
                "component_group": component_group,
                "branch":branch,
                "platforms": platforms  
                 })
    '''
    return render_to_response("Build_Status.xhtml")

def perf_graph(request):
    """
    Function to get the Graph Portlet and Atrributes 
    """
    with session_maker.asgard_read_uncommited_session_provider.get_session() as session :
        nicename = request.REQUEST.get("pg_nicename", "").strip()
        scenario = request.REQUEST.get("pg_scenario", "").strip()
        lable = request.REQUEST.get("pg_label", "").strip()
        column = request.REQUEST.get("pg_column", "").strip()
        show_zero = request.REQUEST.get("pg_show_zero", "").strip()
                
        return render_to_response("perf_graph.xhtml", {
                    "nicename": nicename,
                    "scenario": scenario,
                    "lable":lable,
                    "column":column,
                    "show_zero":show_zero
                    })
    
def graph_data(request):
    """
    Function to get the Graph Data 
    """
    with session_maker.asgard_read_uncommited_session_provider.get_session() as session :
        nicename = request.REQUEST.get("nice", "").strip()
        scenario = request.REQUEST.get("sc", "").strip()
        lable = request.REQUEST.get("la", "").strip()
        column = request.REQUEST.get("co", "").strip()
                
        versions_query = session.query (Version)
        versions_query = versions_query.filter (Version.nice == nicename)
        versions_query = versions_query.filter (Version.abn == 0)
        versions_query = versions_query.order_by (desc (Version.main),
                                                  desc (Version.sub))
        last_v = versions_query.first ()
        db_query = session.query (ReportMetrics.bn, ReportMetrics.f_actual)
        db_query = db_query.with_hint(ReportMetrics, ' with(noexpand) ')
        db_query = db_query.filter (ReportMetrics.main == last_v.main)
        db_query = db_query.filter (ReportMetrics.sub == last_v.sub)
        db_query = db_query.filter (ReportMetrics.abn == 0)

        db_query = db_query.filter (ReportMetrics.st_label == lable)
        db_query = db_query.filter (ReportMetrics.sc_name == scenario)
        db_query = db_query.filter (ReportMetrics.col_name == column)
        
        db_query = db_query.order_by (ReportMetrics.main,
                                      ReportMetrics.sub,
                                      ReportMetrics.bn)
        all_points = db_query.all()

        data = []
        if not len(all_points) == 0:    
            last_build = 0
            for d in all_points:
                if d.bn - last_build > 1:
                    for offset in range(1, d.bn - last_build):
                        #Add the dummy build values
                        data.append((last_build + offset, None))
                        
                data.append(d)
                last_build = d.bn
            data.sort()

        output = {}
        output["label"] = "%s" % (column)
        output["data"] = data

        return HttpResponse(json.dumps(output), mimetype='application/javascript')

def edit_portlet(request):
    """
        Function to edit a portlet title or portlet arguments.
    """
    try :
        with session_maker.magellan_write_session_provider.get_session () as session:
            pid = request.REQUEST.get("portletid")
            argument = request.REQUEST.get("data")
            title = request.REQUEST.get("title", "")
            
            portlet = (session.query(Portlet)).filter(Portlet.id == pid).first()
            portlet.argument = argument
            portlet.title = title
            return render_to_response("portlet.xhtml", {"portlet": portlet})
    except KeyError:
        return HttpResponseServerError("Insufficient parameters provided")
    except Exception, err:
        return HttpResponseServerError(str(err))
        
        
def get_unittest_versions(request):
    """
        Gets the matching Nice name list for Autocomplete field for the
        Unit Test results widget
    """
    with session_maker.asgard_read_uncommited_session_provider.get_session() as session :
        # get the q value from requet.GET
        # get corresponding data and return 
        val = request.GET.get("term", "")
        ival = val + '%'
        
        v_query = session.query (Version.nice).distinct()
        v_query = v_query.filter(Version.abn == 0)
        v_query = v_query.filter(Version.nice.like(ival))
        v_query = v_query.join(UnitTestRun).filter(UnitTestRun._version == Version.id)
        v_query = v_query.order_by(Version.nice)
        
        v_query = v_query[:10]
        data = [v.nice for v in v_query if v.nice]
        return HttpResponse(json.dumps(data), mimetype='application/javascript')
        
def scenario_unittest(request):
    """
    Function to get the Unit Test portlet content. 
    """
    with session_maker.asgard_read_uncommited_session_provider.get_session() as session :
        nicename = request.REQUEST.get("nicename", "").strip()
        inicename = nicename + '%'
        
        unittest_results = [{"name": "Win32"}, #{"name": ""}, 
                                {"name": "Sol32"},{"name": "Win64"},
                                {"name": "Lin64"},{"name": "Sol64"}]
        
        # query to get the most recent version
        ver_query = session.query(UnitTestRun)
        ver_query = ver_query.join(Version).filter(Version.nice.ilike(inicename))
        ver_query =  ver_query.filter(Version.abn == 0)
        # filter by component and Component type("PRIME" for now)
        ver_query  = ver_query.filter(Version.component == "PRIME")
        ver_query  = ver_query.filter(Version.comp_type == "PRIME")
        ver_query = ver_query.order_by(desc(Version.main),
                                   desc(Version.sub),
                                   desc(Version.bn))
        
        last = ver_query.first()
              
        if last is None:
            return HttpResponseServerError("Version not Found")
        
        u_query = session.query(UnitTestRun.platform,
                                UnitTestRun.start,
                                UnitTestRun.status.label("row_status"), 
                                UnitTest.status.label("test_status"),
                                func.count(UnitTest.status).label("count"))
        # group by platform and status to get count of each status
        u_query = u_query.group_by(UnitTestRun.platform, UnitTestRun.start, UnitTestRun.status ,UnitTest.status)
        u_query = u_query.outerjoin(UnitTest)
        u_query =  u_query.filter(UnitTestRun.version == last.version)
        u_query = u_query.order_by(desc(UnitTestRun.platform),
                                   desc(UnitTestRun.start))


        last.prime = get_version('PRIME', last.version.name)
        # Notify user if the build is more than one day old and build is not in top 3 builds for the track
        expired_build = ''
        if check_expired_build(last.prime):
            expired_build = 'asg_red'
        has_errors = False
        
        # group results by platform then pick the time of latest run
        # for that platform so we use only the latest run data
        results = itertools.groupby(u_query.all(), lambda elt: (elt.platform))
        
        for group, result in results:            
            latest_run = None
            platform = None
            for pl in unittest_results:
                if pl["name"].lower() == group.lower():
                    platform = pl
                    break
                     
            if not platform:
                continue
            
            for res in result:
                if not latest_run:
                    latest_run = res.start
                if res.start != latest_run:
                    continue           
                if res.row_status == UnitTestStatus.crash:
                    platform["crashed"] = True
                else:
                    platform[UnitTestStatus.statuses[
                            res.test_status]] = res.count
                if res.row_status != UnitTestStatus.passed:
                    has_errors = True
     
        #insert empty platform for arranging of data in html
        unittest_results.insert(1, {"name": ""})
        return render_to_response("unittest_results.xhtml", {
                    "last": last,
                    "nicename": nicename,
                    "has_errors": has_errors,
                    "results": [ unittest_results[:3], unittest_results[3:] ],
                    "expired_build":expired_build 
                    }) 
    
def unittest_grid_widget(request): 
    """
    Function to get UnitTestGrid widget content. 
    """
    with session_maker.asgard_read_uncommited_session_provider.get_session() as session :
        versions_to_show = 5
        nicename = request.REQUEST.get("nicename", "").strip()
        inicename = nicename + '%'
                
        #1 List of version to be displayed from version table (latest 5)
        #2 Get the latest unit test runs data for the most recent versions
        #3 Generating build number and status map
        
        # part 1 get the latest 5 versions from the version table
        ver_query = session.query(Version.id, Version.name, Version.bn).distinct()
        ver_query  = ver_query.filter(Version.component == "PRIME")
        ver_query  = ver_query.filter(Version.comp_type == "PRIME")
        ver_query = ver_query.filter(Version.nice.ilike(inicename))
        ver_query =  ver_query.filter(Version.abn == 0)
        ver_query = ver_query.order_by(desc(Version.main),
                                   desc(Version.sub),
                                   desc(Version.bn))
        
        recent_versions =  ver_query[:versions_to_show]
        recent_versions.reverse()
        
        # Creating a mapping of build number: index 
        bn_list = [(ver.id, ver.bn) for ver in recent_versions]
        build_dict  = {}
        for idx, item in enumerate(bn_list):
            build_dict[item[0]] = (item[1], idx)

        if not recent_versions:
            return HttpResponseServerError("Version not Found")
        
        last = recent_versions[-1]
        
        last.prime = get_version('PRIME', last.name)
        
        # part 2 get the latest unit test runs for the most recent versions
        # grouped as to get individual counts of passing, failing unit tests acccording to platform, version , time of run
        # ordered by platform and time of run to be able to pick the latest run only.
        
        u_query = session.query(UnitTestRun.platform,
                                UnitTestRun._version.label("version_id"),
                                UnitTestRun.status.label("row_status"),
                                UnitTestRun.start,
                                UnitTest.status.label("test_status"), 
                                func.count(UnitTest.status).label("count"))
        u_query = u_query.group_by(UnitTestRun.platform, 
                                   UnitTestRun._version, 
                                   UnitTestRun.start, 
                                   UnitTestRun.status,
                                   UnitTest.status)
        u_query = u_query.outerjoin(UnitTest)
        u_query =  u_query.filter(UnitTestRun._version.in_([v.id for v in recent_versions]))
        u_query = u_query.order_by(desc(UnitTestRun.platform),
                                   desc(UnitTestRun.start))
        u_query = u_query.all()
        # get all unique platforms tests have been run on.
        unittests = set([run.platform for run in u_query])
        
        # create a mapping dict for the unittest data
        unittest_result_map = []
        unittest_dict = {}
        for idx, run in enumerate(unittests):
            unittest_dict[run] = idx
            unittest_result_map.append([run, [{} for i in range(versions_to_show)]])
        
        # part three, first group results by platform name and version
        unittest_results = itertools.groupby(u_query, lambda elt: (elt.platform, elt.version_id))
        
        has_errors = False
        for group, results in unittest_results:
            unit_idx = unittest_dict[group[0].strip()]
            latest_run = None
            for result in results:
                if result.row_status == UnitTestStatus.crash or result.row_status == UnitTestStatus.failed:
                    has_errors = True
                # we only need the data for the latest run, if multiple runs for the same version,
                # we only want to pick the latest one of those runs
                if not latest_run:
                    latest_run = result.start
                if not result.start == latest_run:
                    continue
                # locate the position of this version and platform in mapping dict
                bn_idx = build_dict[result.version_id][1]
                record = unittest_result_map[unit_idx][1][bn_idx]
                # add status of run to mapping dict
                record["row_status"] = result.row_status
                # add count of failures, errors etc to non failing runs
                if not result.test_status is None:
                    record[result.test_status] = result.count
                    
        return render_to_response("unittest_grid_portlet.xhtml", {
                    "last": last,
                    "bn_list": bn_list,
                    "nicename": nicename,
                    "has_errors": has_errors,
                    "results": unittest_result_map,
                    "statuses": UnitTestStatus
                    }) 
        
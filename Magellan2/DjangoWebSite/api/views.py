# -*- coding: latin-1 -*-

import csv
import json
from django.http import HttpResponse 
from DjangoWebSite.utils import QHandler, session_maker, filter_versions, filter_scenarios, filter_labels, filter_columns
from DjangoWebSite import settings
from front_db.asgard_db import db_wrapper
from front_db.fast_db import direct_wrapper
from front_db.cvc_db import cvc_wrapper
from front_db.asgard_db.db_wrapper import ReportVersionScenario, Status, Version
from front_db.asgard_db.db_wrapper import UnitTestRun, UnitTest, UnitTestStatus, Tag
from django.shortcuts import render_to_response
from front_utils.versions import get_version
from sqlalchemy import desc, and_, or_, except_, distinct
from django.template.loader import render_to_string
from DjangoWebSite.magellan2.templatetags.asgard_tags import spaceify
from django.core.paginator import Paginator
import itertools
from django.core.cache import cache
from DjangoWebSite.settings import DEBUG
from notify import eq_trading_alert, scenario_alert, regression_alert, active_mq_monitor

__FAST_SERVER = settings.FAST_SERVER

def batch_uploaded (request):
    batch_uid = str(request.GET.get("batch_uid", ""))
    
    try:
        with session_maker.asgard_read_uncommited_session_provider.get_session() as session:
            batch = session.query (db_wrapper.Batch).filter_by (uid=batch_uid).one()
                        
            sc_msg = scenario_alert(batch)
            reg_msg = regression_alert(batch)
#            amq_msg = active_mq_monitor()
            if batch.name == "eqt":
                eqt_msg = eq_trading_alert(batch)            
            else:
                eqt_msg = []                

            all_msg = sc_msg + reg_msg + eqt_msg
            for m in all_msg:
                m.send()
            
            response = HttpResponse (status=200)
    except Exception, err:
        response = HttpResponse (status=500)
    finally:
        return response


def graph_list (request):
    
    scenario_name = str(request.GET.get("scenario", ""))
    # Here we need all the corresponding data for this scenario
    
    with session_maker.asgard_read_uncommited_session_provider.get_session() as session:
        db_query = session.query (db_wrapper.ReportMetrics.main,
                                  db_wrapper.ReportMetrics.sub,
                                  db_wrapper.ReportMetrics.st_label,
                                  db_wrapper.ReportMetrics.col_name).distinct()
        db_query = db_query.with_hint(db_wrapper.ReportMetrics, ' with(noexpand) ')
        
        db_query = db_query.filter_by (sc_name=scenario_name)
        db_query = db_query.order_by (desc (db_wrapper.ReportMetrics.main),
                                      desc (db_wrapper.ReportMetrics.sub),
                                      db_wrapper.ReportMetrics.st_label,
                                      db_wrapper.ReportMetrics.col_name,
                                    )
        
        all_values = []
        for by_main_sub in itertools.groupby (db_query, lambda elt:(elt.main, elt.sub)) :
            main_sub = by_main_sub[0]
            # her we need a list of columns and a list of labels
            labels = [] 
            column_set = set ()
            graph_exists = {}
            for by_label in itertools.groupby (by_main_sub [1], lambda elt:elt.st_label):
                label = by_label[0]
                labels.append (label)
                graph_exists [label] = {}
                for column in (elt.col_name for elt in by_label[1]):
                    column_set.add (column)
                    graph_exists [label] [column] = True
            columns = list (column_set)
            columns.sort()
            for label in labels:
                for column in columns:
                    graph_exists [label] [column] = graph_exists [label].get (column, False) 
            all_values.append ({"scenario" : scenario_name,
                                "main_sub" : main_sub,
                                "labels" : labels,
                                "columns" : columns,
                                "graph_exists" : graph_exists
                                })
    
        # Now we create a N big sets where we put the information this way : (label, column).
        # The sets are put in a list of (main, sub)
        # We'll use the set inside the building of the 
        
        # Now we prepare the data for the template engine, because it is quite slow.
        
        return render_to_response('graph_list.xhtml',
                                       {'scenario':scenario_name,
                                        'values': all_values
                                       })

def spr_shortcut (request):
    """
    This function generates a FAST shortcut for an SPR
    """
    d = request.GET.get ("spr_id")
    response = HttpResponse(mimetype='text/text')
    response['Content-Disposition'] = 'attachment; filename=SPR_#%s.ARTask'%d
    
    response.write ("""[Shortcut]
Name = 1:SPREntry
Type = 0
Server = %s
Join = 0
Ticket = %s
"""%(__FAST_SERVER, d))

    return response

def build_comment_shortcut(request):
    """
    This function generates a FAST shortcut for build comment page.
    """
    id = request.GET.get("build_comment_id")
    response = HttpResponse(mimetype='text/text')
    response['Content-Disposition'] = 'attachment; filename=BuildComment#%s.ARTask'%id
    shortcut_text = """[Shortcut]
Name = 5:1:7:BuildComment
Type = 0
Server = %s
Join = 0
Ticket = %s""" %(__FAST_SERVER, id)
    response.write(shortcut_text)
    
    return response

def hist_data(request):    
    #format_h = QHandler (request.GET.get("format", ""))
    label_h = QHandler (request.GET.get("label", "")) or None
    col_h = QHandler (request.GET.get("col", "")) or None
    version_h = QHandler (request.GET.get("vfilter", "")) or None
    scenario_h = QHandler (request.GET.get("scenario", "")) or None
    baseline = request.GET.get("baseline", "") or None
    # Don't care about format for now. CSV for all !
    
    label = " ".join (label_h.pos_freewords)
    column = " ".join (col_h.pos_freewords)
    scenario_name = " ".join (scenario_h.pos_freewords)
    
    with session_maker.asgard_read_uncommited_session_provider.get_session () as session:
        
        if baseline :
            # The query that gives us the values against which we want to baseline
            # redoing the whole set of query to allow cross version benchmarking in performance graphs 
            
            baseline_prime = get_version('PRIME', baseline)
            baseline_query = session.query (db_wrapper.ReportMetrics.f_actual, db_wrapper.ReportMetrics.bn)
            baseline_query = baseline_query.with_hint(db_wrapper.ReportMetrics, ' with(noexpand) ')
    
            baseline_query = baseline_query.filter (db_wrapper.ReportMetrics.main == baseline_prime.main)
            baseline_query = baseline_query.filter (db_wrapper.ReportMetrics.sub == baseline_prime.sub)
            baseline_query = baseline_query.filter (db_wrapper.ReportMetrics.abn == 0)
    
            baseline_query = baseline_query.filter (db_wrapper.ReportMetrics.ver_name == baseline)
            
            baseline_query = baseline_query.filter (db_wrapper.ReportMetrics.st_label == label)
            baseline_query = baseline_query.filter (db_wrapper.ReportMetrics.sc_name == scenario_name)
            baseline_query = baseline_query.filter (db_wrapper.ReportMetrics.col_name == column)            
            
            base_data_all = baseline_query.all()
            baseline_divisor = 0.01 * sum (data[0] for data in base_data_all) / len (base_data_all) # If many runs, pick the last one. Then pick the value in it.
            # it will fail (on purpose) if we do not find any data
        else :
            baseline_divisor = 1.0        
        
        versions_query = session.query (db_wrapper.Version)
        versions_query = filter_versions (versions_query, version_h)
        versions_query = versions_query.filter (db_wrapper.Version.abn == 0)
        versions_query = versions_query.order_by (desc (db_wrapper.Version.main),
                                                  desc (db_wrapper.Version.sub),)
        last_v = versions_query.first ()
        
        db_query = session.query (db_wrapper.ReportMetrics.f_actual, db_wrapper.ReportMetrics.bn)
        db_query = db_query.with_hint(db_wrapper.ReportMetrics, ' with(noexpand) ')

        db_query = db_query.filter (db_wrapper.ReportMetrics.main == last_v.main)
        db_query = db_query.filter (db_wrapper.ReportMetrics.sub == last_v.sub)
        db_query = db_query.filter (db_wrapper.ReportMetrics.abn == 0)

        db_query = db_query.filter (db_wrapper.ReportMetrics.st_label == label)
        db_query = db_query.filter (db_wrapper.ReportMetrics.sc_name == scenario_name)
        db_query = db_query.filter (db_wrapper.ReportMetrics.col_name == column)
        
        db_query = db_query.order_by (db_wrapper.ReportMetrics.main,
                                      db_wrapper.ReportMetrics.sub,
                                      db_wrapper.ReportMetrics.bn,
                                      db_wrapper.ReportMetrics.abn
                                      )
        all_points = db_query.all()
        
        data = [("Data Unavailable",0)]

        # Maybe there is a faster way to do this
        if not len(all_points) == 0:
            data = []
            if not baseline :
                last_build = 0
                for d in all_points:
                    if d.bn - last_build > 1:
                        for offset in range(1, d.bn - last_build):
                            #Add the dummy build values
                            data.append((last_build + offset, None, 0))
                    data.append((d.bn, d.f_actual and d.f_actual/baseline_divisor, 0))
                    last_build = d.bn
                data.sort();
                data.insert(0, ("Build", column, "x-axis"))
            else :
                last_build = 0
                for d in all_points:
                    if d.bn - last_build > 1:
                        for offset in range(1, d.bn - last_build):
                            #Add the dummy build values
                            data.append((last_build + offset, None, 100, 0))
                    data.append((d.bn, d.f_actual and d.f_actual/baseline_divisor, 100, 0))
                    last_build = d.bn
                data.sort()
                data.insert(0, ("Build", column, "base", "x-axis"))
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=data_values.csv'
        
        writer = csv.writer(response)    
        for rowvalu in data:
            writer.writerow(rowvalu)
        return response


def get_annotations(request):
    """
    Get the list of build numbers from fast for a particular track.
    """
    
    main = request.GET.get("main")
    sub = request.GET.get("sub")

    with session_maker.fast_read_uncommited_session_provider.get_session () as session:
        squery = session.query(direct_wrapper.get_FAST_class("BuildComment", session))
        squery = squery.join (direct_wrapper.get_FAST_class("BuildNumber", session))
        squery  = squery.filter (direct_wrapper.get_FAST_class("BuildComment", session).component.in_ (("PRIME", "ADS", "AMBA", "ADM")))
        squery = squery.filter (direct_wrapper.get_FAST_class("BuildNumber", session).major == main)
        squery = squery.filter (direct_wrapper.get_FAST_class("BuildNumber", session).minor == sub)
    
        comments =  squery.all()
        
        build_data = list (set([str(comment.build_number_item.bn) for comment in comments]))
            
        buildTxt = ",".join(build_data)
    
        return HttpResponse(content=buildTxt)

def build_comments(request):
    """
    function  to get the build comments from fast
    """
    main = request.GET.get ("main") 
    sub = request.GET.get ("sub")
    build_val = request.GET.get ("build")
    with session_maker.fast_read_uncommited_session_provider.get_session () as session:
        squery = session.query(direct_wrapper.get_FAST_class("BuildComment", session))
        squery = squery.join (direct_wrapper.get_FAST_class("BuildNumber", session))
        squery  = squery .filter (direct_wrapper.get_FAST_class("BuildComment", session).component.in_ (("PRIME", "ADS", "AMBA", "ADM")))
        squery = squery.filter (direct_wrapper.get_FAST_class("BuildNumber", session).major == main)
        squery = squery.filter (direct_wrapper.get_FAST_class("BuildNumber", session).minor == sub)
        squery = squery.filter (direct_wrapper.get_FAST_class("BuildNumber", session).bnumber == build_val)
        comments =  squery.all()
    
        return render_to_response('build_comment.xhtml',
                                       {'build':build_val,
                                        'comments': comments})

def build_sprs(request):
    """
    Function to get the sprs contained within a build
    """
    main = request.GET.get ("main") 
    sub = request.GET.get ("sub")
    build_val = request.GET.get ("build")
    with session_maker.fast_read_uncommited_session_provider.get_session () as session:
        db_query = session.query (direct_wrapper.get_FAST_class("BuildNumber", session))
        db_query = db_query.filter_by (major = main)
        db_query = db_query.filter_by (minor = sub)
        db_query = db_query.filter_by (bnumber = build_val)
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

        sprs = spr_query.all()
        
        response = render_to_response('build_sprs.xhtml',
                                       {'build':build_val,
                                        'sprs':sprs
                                        })
        return response

def spr_detailed_list(request):
    """
    Populate list of SPRs for version page.
    """
    spr_list = set()
    build_1 = request.GET.get ("b1").strip() or None # 2011.1-4.7.541.0....
    build_2 = request.GET.get ("b2").strip() or None
    sprs = request.GET.get ("rel_spr").strip() or None
    component = request.GET.get("component", "PRIME").strip().upper()
    
    if build_1 == None and build_2 == None:
        return HttpResponse()
    
    versions = [build_1 and get_version(component, build_1), build_2 and get_version(component, build_2)]
    versions.sort ()
    
    build_nbs = [versions[0] and versions[0].bn, versions[1].bn]
#    bldnumber2= build_nbs [1]
    bldnumber1= build_nbs [0]

    # Getting Data table related values
    iDisplayStart = request.GET.get("iDisplayStart").strip() or 0
    iDisplayLength = request.GET.get("iDisplayLength").strip() or 0
    isEcho = request.GET.get ("sEcho").strip() or 0
    sSearch = request.GET.get("sSearch").strip() or None
    
#    released_sprs = {}
#    if sprs != None: 
#        released_sprs = dict( [ite,1] for ite in sprs.split(","))
    
#    releaseFound = False    
#    if len(released_sprs) != 0:
#        releaseFound = True

    with session_maker.fast_read_uncommited_session_provider.get_session () as session:
        build_number_class = direct_wrapper.get_FAST_class("BuildNumber", session)
        db_query = session.query (build_number_class)
        db_query = db_query.filter_by (major = versions[1].main)
        db_query = db_query.filter_by (minor = versions[1].sub)
        db_query = db_query.filter_by (alt_bnumber = 0)
        #Single build selected.
        if bldnumber1 is None :
            db_query = db_query.filter(build_number_class.bnumber == build_nbs[1])
        else:
        #Multiple selection
            db_query = db_query.filter(and_(build_number_class.bnumber <= build_nbs[1], 
                                        build_number_class.bnumber > build_nbs[0]))
    
        #@todo: we need to also take the branches into account. For now it does not work.
        spr_bld_mapping = {}
        for bn in db_query:   
            if bn.clean_sprs_included != None:         
                bn_spr_list = set([s.strip () for s in bn.clean_sprs_included.split (";") if s.strip()])
                build_set = set([])
                for spr in bn_spr_list:
                    build_set = set([bn.build_number])
                    if spr_bld_mapping.has_key(spr):
                        spr_bld_mapping[spr].union (build_set)
                    else:
                        spr_bld_mapping[spr]=set (build_set)
                    
                spr_list = spr_list.union(bn_spr_list)
        dw_SPR = direct_wrapper.get_FAST_class("1:SPREntry", session)
          
        spr_query = session.query (dw_SPR)
        spr_query = spr_query.filter (dw_SPR.spr_id.in_ (spr_list))
        spr_query = spr_query.filter (dw_SPR.spr_id <> 264097) # generic build spr
        spr_query = spr_query.filter (dw_SPR.spr_id <> 260796) # generic build spr
        
        totalRecords = spr_query.count()
        totalFilteredRecords = totalRecords
        
        # Adding search related queries 
        if sSearch != None:            
            sSearchLst = sSearch.split(" ")
            for isSearch in sSearchLst:
                iSearch = '%' + isSearch + '%'
                spr_query = spr_query.filter(or_(dw_SPR.spr_id.like(iSearch), 
                                                 dw_SPR.component.ilike(iSearch),
                                                 dw_SPR.severity.ilike(iSearch), 
                                                 dw_SPR.spr_submitter.ilike(iSearch), 
                                                 dw_SPR.assigned_to.ilike(iSearch), 
                                                 dw_SPR.spr_status.ilike(iSearch), 
                                                 #dw_SPR.tester.like(sSearch),
                                                 dw_SPR.short_description_spr.ilike(iSearch), 
                                                 dw_SPR.external_spr_description.like(iSearch) )) #Cannot do an ilike request here
                
            totalFilteredRecords = spr_query.count()
        
        spr_query = spr_query.order_by(dw_SPR.spr_id)
        sprs = spr_query[int(iDisplayStart):int(iDisplayStart)+int(iDisplayLength)]
        
        output = {}
        output["sEcho"] = isEcho 
        output["iTotalRecords"] = totalRecords
        output["iTotalDisplayRecords"] = totalFilteredRecords 
        tmpLst = []
        
        for spr in sprs:
            spr_txt = ",".join(spr_bld_mapping[spr.spr_id])
            tableCol = render_to_string('spr_detailed_list.xhtml',{"spr":spr,'bld_mapping':spr_txt})
            tableCol = tableCol.replace('\n','')
            tmpLst.append([tableCol])
             
        output["aaData"] = tmpLst
        tempJson = json.dumps(output)
 
        tempJson = tempJson.replace("None"," ")
        tempJson = tempJson.replace('\n','')
                
        response = HttpResponse()
        response.write(tempJson);
        return response
    
def get_spr_build_maping(request):
    """
    Function to get the build numbers for any given spr
    """
    sprno = request.GET.get ("sprno").strip()
    main = request.GET.get ("main") 
    sub = request.GET.get ("sub")
    
    with session_maker.fast_read_uncommited_session_provider.get_session () as session:
        db_query = session.query (direct_wrapper.get_FAST_class("BuildNumber", session))
        db_query = db_query.filter_by (major = main)
        db_query = db_query.filter_by (minor = sub)
        #db_query = db_query.filter_by (spr_inc = "312757")
        
        db_query  = db_query.filter (direct_wrapper.get_FAST_class("BuildNumber", session).sprs_included.like ('%'+sprno+'%'))
        #@todo: we need to also take the branches into account. For now it does not work.
        
        builds = db_query.all ()
        build_data = list (set([str(build.bn) for build in builds]))
        buildTxt = ",".join(build_data)
    
        return HttpResponse(content=buildTxt)

def get_versions(request):

    session = None
    selected_version = request.GET.get('vfilter', '')
    
    cache_key = str ((selected_version))
    cache_status = cache.get (cache_key, 'has_expired')

    if cache_status == "has_expired": 
        qv = QHandler(selected_version)
        with session_maker.asgard_read_uncommited_session_provider.get_session () as session:
            db_query = session.query (db_wrapper.Version.name,db_wrapper.Version.main,db_wrapper.Version.sub)
            # Should order things almost right
            db_query = db_query.order_by (desc (db_wrapper.Version.main),
                                desc(db_wrapper.Version.sub),
                                desc(db_wrapper.Version.sub2),
                                desc(db_wrapper.Version.hf),
                                desc(db_wrapper.Version.p),
                                desc(db_wrapper.Version.bn),
                                desc(db_wrapper.Version.abn),
                                desc(db_wrapper.Version.dat))
    
            # forcing the querry to default to a component
            db_query = filter_versions(db_query, qv)
                
            last= db_query.first ()
            db_query = db_query.filter (db_wrapper.Version.main == last.main)
            db_query = db_query.filter (db_wrapper.Version.sub == last.sub)
            db_query = db_query.filter (or_(db_wrapper.Version.abn == 0,db_wrapper.Version.abn == None))
              
            versiondata = db_query.all() 
            version_data = list(str(versiondata.name) for versiondata in versiondata)    
            version_txt = ",".join(version_data)

            cache.set (cache_key, version_txt, 3600)

            # Order things really well
            #versions.sort (key=lambda s:get_version('PRIME', s.name), reverse=True)
    else :
        version_txt = cache.get(cache_key)

    return HttpResponse(content=version_txt)

def checkin_detailed_list(request):
    """
    Populate list of SPRs for version page.
    """
    build_1 = request.GET.get ("b1").strip() or None # 2011.1-4.7.541.0....
    build_2 = request.GET.get ("b2").strip() or None
    sprs = request.GET.get ("rel_spr").strip() or None
    filter_data = request.GET.get ("filter_data").strip() or None
    component = request.GET.get("component", "PRIME").strip().upper()
    
    if build_1 == None and build_2 == None:
        return HttpResponse()
    
    released_sprs = {}
    if sprs != None: 
        released_sprs = dict( [ite,1] for ite in sprs.split(","))
  
    iDisplayStart = request.GET.get("iDisplayStart").strip() or 0
    iDisplayLength = request.GET.get("iDisplayLength").strip() or 0
    isEcho = request.GET.get ("sEcho").strip() or 0
    sSearch = request.GET.get("sSearch").strip() or None
    
    versions = [build_1 and get_version(component, build_1), build_2 and get_version(component, build_2)]
    versions.sort ()
    
    build_nbs = [versions[0] and versions[0].bn, versions[1].bn]
    bldnumber1= build_nbs [0]
    
    with session_maker.asgard_read_uncommited_session_provider.get_session () as session:
        db_query = session.query(db_wrapper.RevLogs, db_wrapper.Version.name)
        db_query = db_query.join (db_wrapper.Version)
        db_query = db_query.filter (db_wrapper.Version.main == versions[1].main)
        db_query = db_query.filter (db_wrapper.Version.sub ==  versions[1].sub)
        db_query = db_query.filter (db_wrapper.Version.abn == 0)
        db_query = db_query.filter (db_wrapper.RevLogs.action <> 'create branch') # generic build spr
        db_query = db_query.filter (db_wrapper.RevLogs.spr <> 264097) # generic build spr
        db_query = db_query.filter (db_wrapper.RevLogs.spr <> 260796) # generic build spr
        
        if bldnumber1 is None :
            db_query = db_query.filter(db_wrapper.Version.bn == build_nbs[1])
        else:
        #Multiple selection 
            db_query = db_query.filter(and_(db_wrapper.Version.bn <= build_nbs[1], 
                                        db_wrapper.Version.bn > build_nbs[0]))

        totalRecords = db_query.count()
        totalFilteredRecords = totalRecords

        if sSearch != None:
            sSearchLst = sSearch.split(" ")
            for isSearch in sSearchLst:
                iSearch = '%' + isSearch + '%'
                db_query = db_query.filter(or_(db_wrapper.RevLogs.spr.like(iSearch),
                                               db_wrapper.RevLogs.branch.ilike(iSearch),
                                               db_wrapper.RevLogs.dir_name.ilike(iSearch),
                                               db_wrapper.RevLogs.file_name.ilike(iSearch),
                                               db_wrapper.RevLogs.cc_ver_nb.like(iSearch), 
                                               db_wrapper.RevLogs.user_login.ilike(iSearch),
                                               db_wrapper.RevLogs.dat.like(iSearch),
                                               db_wrapper.RevLogs.comment.like(iSearch)))

            totalFilteredRecords = db_query.count()

        db_query = db_query.order_by(db_wrapper.RevLogs.spr)

        output = {}
        output["sEcho"] = isEcho 
        output["iTotalRecords"] = totalRecords
        tmpLst = []

        releaseFound = False
        filterData = False
        
        if len(released_sprs) != 0:
            releaseFound = True
        
        if filter_data =='1':
            filterData = True
            checkins = db_query.all()
        else:
            checkins = db_query[int(iDisplayStart):int(iDisplayStart)+int(iDisplayLength)]
            
        for checkin in checkins:
            checkin_ver_name = str(checkin.name).strip().split("-")[1]
            checkin_date= str(checkin.RevLogs.dat).strip().split(" ")[0]
            spr_id = str (checkin.RevLogs.spr)
            highlight = False
            includeSpr = True 
            
            if releaseFound:
                if not released_sprs.has_key(spr_id): 
                    highlight = True
                elif filterData: 
                    includeSpr = False

            if includeSpr:
                tableCol = render_to_string('checkin_detailed_list.xhtml',
                                            {"checkin":checkin,"checkin_name":checkin_ver_name, 
                                             "checkin_date":checkin_date, 
                                             "highlight":highlight,
                                             "spr_id":spr_id})
                tableCol = tableCol.replace('\n','')
                tmpLst.append([tableCol])
        
        if filterData: 
            totalFilteredRecords = len(tmpLst)
            tmpLst = tmpLst[int(iDisplayStart):int(iDisplayStart)+int(iDisplayLength)]
            
        output["iTotalDisplayRecords"] = totalFilteredRecords
        output["aaData"] = tmpLst
        tempJson = json.dumps(output)
 
        tempJson = tempJson.replace("None"," ")
        tempJson = tempJson.replace('\n','')
                
        response = HttpResponse()
        response.write(tempJson);

        return response
    
        
def get_spr_release_information(request):
    """
    Get the list of SPRs for version page | checkins tab to compare it with Rev logs information.
    """
    component_value = request.GET.get ("comp").strip() or None
    release_value = request.GET.get ("rel").strip() or None
    
    if component_value == None or release_value == None:
        return HttpResponse()
    
    with session_maker.fast_read_uncommited_session_provider.get_session () as session:
        release_class = direct_wrapper.get_FAST_class("ReleasesFixedIn", session)
        db_query = session.query (release_class)
        db_query = db_query.filter_by (component = component_value)
        db_query = db_query.filter_by (fixed_in = release_value)

        sprs = db_query.all()
        
        spr_data = list (set([str(spr.spr_id) for spr in sprs]))
        sprTxt = ",".join(spr_data)

        return HttpResponse(content=sprTxt)

def alerts_list(request):
    """
    This function populates the alerts table from the database.
    """
    #Columns start at one because 0th column (Raw scenario)
    #is hidden chrome has issues with datatables hiding last
    #column so we need to reindex all the columns keep this
    #in mind while working with sorting.
    column_map = {"1":db_wrapper.AverageHistory.batch_name, 
                  "2":db_wrapper.AverageHistory.scenario,
                  "3":db_wrapper.AverageHistory.measure,
                  "4":db_wrapper.AverageHistory.label,
                  "5":db_wrapper.AverageHistory.avg_value,
                  "6":db_wrapper.AverageHistory.f_actual,
                  "7":None}
    iDisplayStart = int(request.GET.get("iDisplayStart", "").strip() or 0)
    iDisplayLength = int(request.GET.get("iDisplayLength", "").strip() or 0)
    sEcho = request.GET.get("sEcho", "").strip() or 0
    sSearch = request.GET.get("sSearch", "").strip() or None
    sort_on = request.GET.get("iSortCol_0", None)
    sort_direction = request.GET.get("sSortDir_0", None)
    sort_col = column_map.get(sort_on, None)
    with session_maker.asgard_read_uncommited_session_provider.get_session () as session:
        alerts = []
        sc_list = []
        col_list = []
        lbl_list = []
        average_data = []
        ver = request.GET.get("b1", "")
        tolerance = request.GET.get("txt_tolerance", "5")
        tolerance = float(tolerance) if tolerance else 5.0

        col_list = ['gc_used_kilobytes', 'used_cpu_s', 'nb_nodes']

        lbl_list = ('Effect of loading sheet after GC', 
                    'Effect of loading sheet after GC',
                    'Effect of loading sheet before GC',
                    'Measure of loading sheet after GC')
            
        #Get the appropriate version
        qv = QHandler (ver) # Versions
        ver = filter_versions(session.query(db_wrapper.Version),
                                    qv, session, True).first()

        #Now fetch the data for averaged values for alerts.
        db_query = session.query(db_wrapper.AverageHistory.batch_name,
                                 db_wrapper.AverageHistory.scenario,
                                 db_wrapper.AverageHistory.label,
                                 db_wrapper.AverageHistory.measure,
                                 db_wrapper.AverageHistory.avg_value,
                                 db_wrapper.AverageHistory.f_actual,
                                 db_wrapper.AverageHistory.avg_id)
        db_query = db_query.join(db_wrapper.Average)
        db_query = db_query.filter(db_wrapper.AverageHistory.main == ver.main)
        db_query = db_query.filter(db_wrapper.AverageHistory.sub == ver.sub)
        db_query = db_query.filter(db_wrapper.AverageHistory.sub2 == ver.sub2)
        db_query = db_query.filter(db_wrapper.AverageHistory.abn == ver.abn)
        db_query = db_query.filter(db_wrapper.AverageHistory.bn == ver.bn)
        db_query = db_query.filter(db_wrapper.AverageHistory.batch_name.in_(('perf', 'perf_bdp')))

#        db_query = db_query.filter(db_wrapper.AverageHistory.scenario.in_(sc_list))
        db_query = db_query.filter(db_wrapper.AverageHistory.label.in_(lbl_list))
        db_query = db_query.filter(db_wrapper.AverageHistory.measure.in_(col_list))
        
        if sSearch:
            key_words = sSearch.split(" ")
            for word in key_words:
                search_string = '%%%s%%'%word
                db_query = db_query.filter(or_(db_wrapper.AverageHistory.scenario.ilike(search_string),
                                               db_wrapper.AverageHistory.label.ilike(search_string),
                                               db_wrapper.AverageHistory.measure.ilike(search_string)))

            
        if sort_col:
            if sort_direction == 'asc':
                db_query = db_query.order_by(sort_col.asc())
            else:
                db_query = db_query.order_by(sort_col.desc())

        average_data = [avg_data for avg_data in db_query]
            
        ver_hist = []
        for batch, sc, lbl, col, avg_value, new_value, avg_id in average_data:
            if not ver_hist:
                avg_ver = session.query(db_wrapper.AverageVersion.main,
                                        db_wrapper.AverageVersion.sub,
                                        db_wrapper.AverageVersion.bn)
                avg_ver = avg_ver.filter(db_wrapper.AverageVersion.avg_id == avg_id)
                ver_hist = ['%d.%d.%d'%(v.main, v.sub, v.bn) for v in avg_ver]
            if avg_value == None: continue
            if new_value == None: continue
            if avg_value != 0:
                diff = ((new_value - avg_value)/avg_value) * 100
                if (tolerance < abs(diff)):
                    alert = (batch, sc, lbl, col, avg_value, 
                         new_value, diff)
                    if alert not in alerts: alerts.append(alert)
            else:
                diff = new_value - avg_value 
                if ( (diff > tolerance ) or (diff < (-tolerance) )):
                    alert = (batch, sc, lbl, col, avg_value, 
                         new_value, diff)
                    if alert not in alerts: alerts.append(alert)
    
        #Sort of the diff column
        def alert_sort(a, b): return cmp(a[6], b[6])    
        if sort_on == "7":
            alerts.sort(alert_sort)
            if sort_direction != 'asc':
                alerts.reverse()
      
        template = []
        for batch, scenario, label, measure, avg, f_actual, diff in alerts[iDisplayStart:iDisplayStart + iDisplayLength]:
            alert = (scenario, batch, spaceify(scenario), measure, label, 
                     '%.2f'%avg, '%.2f'%f_actual, '%.2f'%diff)
            template.append(alert)
        total_records = len(alerts)
        
        output = {}
        output["sEcho"] = sEcho
        output["sSearch"] = sSearch
        output["aaData"] = template
        output["iDisplayStart"] = iDisplayStart
        output["iDisplayLength"] = iDisplayLength
        output["iTotalRecords"] = total_records
        output["iTotalDisplayRecords"] = total_records
        json_data = json.dumps(output)
        json_data = json_data.replace("None"," ")
    
        response = HttpResponse()
        response.write(json_data);
        return response
    
def get_cvc_setup(request):
    """
    This function populates the CVC setup information.
    """
    build1 = request.GET.get("b1", "").strip() or None
    build2 = request.GET.get("b2", "").strip() or None

    if build1 in (None,"" ) or build2 in (None,"" ):
        return HttpResponse()
    
    build1_prime = get_version('PRIME', build1)
    build2_prime = get_version('PRIME', build2)

    with session_maker.cvc_read_uncommitted_db_session_provider.get_session () as session:
    
        my_build = session.query(cvc_wrapper.Build)
        my_build = my_build.filter(cvc_wrapper.Build.platform == "Windows")
        my_build = my_build.filter(cvc_wrapper.Build.platform_bits == "32")
        
        my_first_build = my_build.filter(cvc_wrapper.Build.exe_full_version == build1)
        build1_all = my_first_build.all()
        
        my_second_build = my_build.filter(cvc_wrapper.Build.exe_full_version == build2)
        build2_all = my_second_build.all()        
        
        if len(build1_all) == 0 or len(build2_all) == 0:
            return HttpResponse()

        build1_id = build1_all[0].id
        build2_id = build2_all[0].id
        
        tsk_defs = session.query(cvc_wrapper.Setup.taskdef)
        tsk_defs = tsk_defs.join (cvc_wrapper.Report)
        
        all_first_reports = tsk_defs.filter(cvc_wrapper.Report.build_id == build1_id)
        all_second_reports = tsk_defs.filter(cvc_wrapper.Report.build_id == build2_id)
        
        task_add = all_first_reports.except_ (all_second_reports).all()
        task_rem = all_second_reports.except_ (all_first_reports).all()
        
        tasks = map( None , *[task_add,task_rem])
        
        response = render_to_response('cvc_setup.xhtml',
                                       {'build1':build1_prime,
                                        'build2':build2_prime,
                                        'tasks':tasks,
                                        'task_add_len':len(task_add),
                                        'task_rem_len':len(task_rem)
                                        })
        return response
    
def get_cell_exception_details (request):
    cell_id = request.GET.get("cell_id", "").strip() or None
    with session_maker.asgard_read_uncommited_session_provider.get_session () as session:
        cell = session.query (db_wrapper.RealCell).filter_by (id = cell_id).one ()
        response = render_to_response('cell_exception_data.xhtml',
                                       {'cell':cell,
                                        })
        return response
    
def get_step_row_exception_details (request):
    row_id = request.GET.get("row_id", "").strip() or None
    step_id = request.GET.get("step_id", "").strip() or None
    with session_maker.asgard_read_uncommited_session_provider.get_session () as session:
        if row_id is not None:
            obj = session.query (db_wrapper.Row).filter_by (id = row_id).one ()
        elif step_id is not None:
            obj = session.query (db_wrapper.Step).filter_by (id = step_id).one ()
        response = render_to_response('row_exception_data.xhtml',
                                       {'obj':obj,
                                        })
        return response
    
def get_scenario_grid(request):
    """
    This function populates the Grid view in Scenario tab.
    """
    main_release = request.GET.get("b1", "").strip() or None
    component = request.GET.get("component", "PRIME").strip().upper()
    qset = request.GET.get("set", "").strip()
    page_num = int(request.GET.get("page", 1))
    sSearch = request.GET.get("sSearch", "").strip()

    # these are calculated on JS side since we have the list ready with client
    versions_list = request.GET.get("versions_list", []).split(",")
    
    if not main_release:
        return HttpResponse("No build selected. If issue persist please contact us.")
    
    build1 = get_version(component, main_release)
    
    with session_maker.asgard_read_uncommited_session_provider.get_session () as session:

        #1 List of version to be displayed from version table 12< selected >12  
        #2 Geting scenario names for the selected release with sorting on status
        #3 Getting data for all the builds 
        #4 Generating build number and status map

        # Part one the list of names should be sent from the client side 
        # and then processed here so that we have the list of build numbers 
        build_list = [get_version(component, ver) for ver in versions_list]
        bn_list = [b.bn for b in build_list]
        build_dates = itertools.groupby(sorted(build_list, key=lambda item: item.date), lambda elt:(elt.date.strftime("%b %d")))
        build_dates =  [(d[0], list(d[1])) for d in build_dates] 
        
        # Creating build dict data to be used to find the index in the list 
        build_dict  = {}
        for idx,item in enumerate(bn_list):
            build_dict[item] = idx

        #part two sort on status and name to get the latest falling scenarios for the main release selected

        sc_name_query = session.query(distinct(ReportVersionScenario.sc_name))
        sc_name_query = sc_name_query.filter (ReportVersionScenario.comp_type == component)        
        sc_name_query = sc_name_query.filter (ReportVersionScenario.main == build1.main)
        sc_name_query = sc_name_query.filter (ReportVersionScenario.sub == build1.sub)
        sc_name_query = sc_name_query.filter (or_(ReportVersionScenario.abn == 0,ReportVersionScenario.abn == None))
        
        if not qset == "none" : sc_name_query = sc_name_query.filter (ReportVersionScenario.br_name == qset)
        # Added filter to remove 'pending 'scenario implementation from count
        sc_name_query = sc_name_query.filter (ReportVersionScenario.sc_impl == None)

        #sc_display_query = sc_name_query.filter (ReportVersionScenario.sc_status.in_(['3','2']))
        if sSearch:
            # filtering on the search            
            sSearchLst = sSearch.split(" ")
            for isSearch in sSearchLst:
                iSearch = '%' + isSearch + '%'
                sc_name_query = sc_name_query.filter(or_(
                                        ReportVersionScenario.sc_name.ilike(iSearch),
                                        ReportVersionScenario.sc_authors.ilike(iSearch),
                                        ReportVersionScenario.sc_owner.ilike(iSearch),
                                        ReportVersionScenario.sc_spr.ilike(iSearch),
                                        ReportVersionScenario.sc_descr.ilike(iSearch)))

        sc_all_bn_name_query = sc_name_query.filter (ReportVersionScenario.bn.in_ (bn_list))
        sc_exact_bn_name_query = sc_name_query.filter (ReportVersionScenario.bn == build1.bn)

        # First we create a list of scenarios that are of the current build, in reverse order of their statuses
        
        scenario_name_to_display =  [o[0] for o in sc_exact_bn_name_query.filter (ReportVersionScenario.sc_status == Status.crash).all()]
        scenario_name_to_display.extend ([o[0] for o in sc_exact_bn_name_query.filter (ReportVersionScenario.sc_status == Status.error).all() if o[0] not in scenario_name_to_display])
        scenario_name_to_display.extend ([o[0] for o in sc_exact_bn_name_query.filter (ReportVersionScenario.sc_status == Status.failed).all() if o[0] not in scenario_name_to_display])
        # Since we are caching the complete list for the given set this is not needed
        #scenario_name_to_display.extend ([o[0] for o in sc_exact_bn_name_query.filter (ReportVersionScenario.sc_status == Status.passed).all() if o[0] not in scenario_name_to_display])
        
        # Now we add the scenarios from the other build numbers, but only if we do not have any scenario to display
        scenario_name_to_display.extend ([o[0] for o in sc_all_bn_name_query.filter (ReportVersionScenario.sc_status == Status.crash).all() if o[0] not in scenario_name_to_display])
        scenario_name_to_display.extend ([o[0] for o in sc_all_bn_name_query.filter (ReportVersionScenario.sc_status == Status.error).all() if o[0] not in scenario_name_to_display])
        scenario_name_to_display.extend ([o[0] for o in sc_all_bn_name_query.filter (ReportVersionScenario.sc_status == Status.failed).all() if o[0] not in scenario_name_to_display])
        # Since we are caching the complete list for the given set this is not needed
        #scenario_name_to_display.extend ([o[0] for o in sc_all_bn_name_query.filter (ReportVersionScenario.sc_status == Status.passed).all() if o[0] not in scenario_name_to_display])
        
        # Now, if needed (if the previous list is empty), we add all the names for the current branch, not looking at the build numbers at all.
        cache_key = str ((component, build1.main, build1.sub, qset, sSearch))
        cache_status = cache.get (cache_key, 'has_expired')
        if not cache_status == "has_expired": 
            all_names = cache.get(cache_key) 
        else :
            all_names = [o[0] for o in sc_name_query.all()]
            if all_names :
                cache.set (cache_key, all_names, 3600)
            

        scenario_name_to_display.extend ([o for o in all_names if o not in scenario_name_to_display]) 
        
        #sc_display_query = sc_display_query.order_by (desc(ReportVersionScenario.sc_status),
        #                                              ReportVersionScenario.sc_name)
        failing_scenarios_to_display =  scenario_name_to_display[:]
        paginator = Paginator(failing_scenarios_to_display , 30) #Pagination of list.
        page = paginator.page(page_num)
        scenarios_to_display = list( str(s).strip() for s in page.object_list)

        # creating the map structure in form of list[sc_name,list[status]]]
        
        scenario_result_map = []
        scenario_dict = {}

        build_values_len = len(build_dict.items())
        
        for idx,sce in enumerate(scenarios_to_display):
            scenario_dict[sce] = idx
            scenario_result_map.append([sce,[[-1]]*build_values_len])               

        #part three for range of builds to be displayed in grid 
        sc_grid_query = session.query (ReportVersionScenario.sc_id,
                                       ReportVersionScenario.sc_name,
                                       ReportVersionScenario.sc_status,
                                       ReportVersionScenario.bn)
        
        # sc_query = sc_query.filter (ReportVersionScenario.component == component)        
        sc_grid_query = sc_grid_query.filter (ReportVersionScenario.main == build1.main)
        sc_grid_query = sc_grid_query.filter (ReportVersionScenario.sub == build1.sub)
        sc_grid_query = sc_grid_query.filter (or_(ReportVersionScenario.abn == 0,ReportVersionScenario.abn == None))
        if not qset == "none" : sc_grid_query = sc_grid_query.filter (ReportVersionScenario.br_name == qset)
        # Added filter to remove 'pending 'scenario implementation from count
        sc_grid_query = sc_grid_query.filter (ReportVersionScenario.sc_impl == None)
                      
        sc_grid_query = sc_grid_query.filter (ReportVersionScenario.bn.in_(bn_list))        
        sc_grid_query = sc_grid_query.filter (ReportVersionScenario.sc_name.in_(scenarios_to_display))
        if sSearch != None:
        # filtering on the search            
            sSearchLst = sSearch.split(" ")
            for isSearch in sSearchLst:
                iSearch = '%' + isSearch + '%'
                sc_grid_query = sc_grid_query.filter(or_(
                                        ReportVersionScenario.sc_name.ilike(iSearch),
                                        ReportVersionScenario.sc_authors.ilike(iSearch),
                                        ReportVersionScenario.sc_owner.ilike(iSearch),
                                        ReportVersionScenario.sc_spr.ilike(iSearch),
                                        ReportVersionScenario.sc_descr.ilike(iSearch)))
        
        sc_grid_query = sc_grid_query.order_by (ReportVersionScenario.sc_name,
                                                ReportVersionScenario.bn)
        
        #part four for adding information to map created earlier
        
        for scenario_result in sc_grid_query:
            sc_idx = scenario_dict[str(scenario_result.sc_name).strip()]
            bn_idx = build_dict[scenario_result.bn]
            scenario_result_map[sc_idx][1][bn_idx] = [scenario_result.sc_status,scenario_result.sc_id]
        
        return render_to_response('scenario_grid.xhtml',
                                       {'build1':build1,
                                        'builds':bn_list,
                                        'scenarios':scenario_result_map,
                                        'data': page,
                                        'build_dates': build_dates
                                        })            

def get_scenario_steps(request):
    """
    This function populates the step information for a scenario
    """
    sc_id = request.REQUEST.get("sc_id")
    try:
        sc_id = int(sc_id)
    except:
        return HttpResponse("Unknown Scenario selected.")
    
    with session_maker.asgard_read_uncommited_session_provider.get_session () as session:
        scenario_to_display = session.query(db_wrapper.Scenario).filter_by (id=sc_id).first()
    
        first_failing_step = None
        if scenario_to_display : 
            first_failing_step = scenario_to_display.steps.filter (db_wrapper.Step.status <> 1).first ()
        
        return render_to_response('scenario_step.xhtml',
                                    {'scenario': scenario_to_display,
                                    'first_failing_step': first_failing_step
                                })

def get_sets(request):
    """
        Returns all the scenario sets
    """
    with session_maker.asgard_read_uncommited_session_provider.get_session() as session :
        # get the q value from requet.GET
        # get corresponding data and return 
        sc_comp = request.REQUEST.get("sc_comp").strip().upper()
        v_query = session.query (ReportVersionScenario.br_name).distinct()
        v_query = v_query.filter (ReportVersionScenario.comp_type == sc_comp)        
        v_query = v_query.order_by (ReportVersionScenario.br_name)
        
        data = [v.br_name for v in v_query if v.br_name]
        return HttpResponse(json.dumps(data), mimetype='application/javascript')
    
def get_unittest_grid(request):
    """
    This function populates the Grid view in UnitTest tab.
    """
    main_release = request.GET.get("b1", "").strip() or None
    component = request.GET.get("component", "PRIME").strip().upper()
    tag = request.GET.get("tag", "").strip()
    page_value = int(request.GET.get("page", 1))
    sSearch = request.GET.get("sSearch", "").strip()
    
    # these are calculated on JS side since we have the list ready with client
    versions_list = request.GET.get("versions_list", []).split(",")

    if not main_release:
        return HttpResponse("No build selected. If issue persist please contact us.")
    
    if component != "PRIME" :
        return HttpResponse("Unit Tests are currently automated only in PRIME. If you want your component here please contact CI: Continous Integration")

    with session_maker.asgard_read_uncommited_session_provider.get_session () as session:

        #1 List of version to be displayed from version table 10< selected >10  
        #2 Geting version id of all the build numbers to be searched 
        #3 Getting data for all the builds 
        #4 Generating build number and status map

        # Part one the list of names should be sent from the client side 
        # and then processed here so that we have the list of build numbers 

        sel_build = get_version('PRIME',main_release)
        build_list = [get_version('PRIME', ver) for ver in versions_list]
        bn_list = [b.bn for b in build_list]
        build_dates = itertools.groupby(sorted(build_list, key=lambda item: item.date), lambda elt:(elt.date.strftime("%b %d")))
        build_dates = [(d[0], list(d[1])) for d in build_dates] 
        
        # Creating build dict data to be used to find the index in the list 
        build_dict = {}
        for idx,item in enumerate(bn_list):
            build_dict[item] = idx
        
        ver_query = session.query(Version.id, Version.bn)
        ver_query = ver_query.filter(Version.main == sel_build.main)
        ver_query = ver_query.filter(Version.sub == sel_build.sub)
        ver_query = ver_query.filter(Version.bn.in_(bn_list))
        ver_query = ver_query.filter(Version.component == "PRIME")
        ver_query = ver_query.filter(Version.comp_type == "PRIME")
        ver_query = ver_query.filter(Version.abn == 0)
        
        all_ver = ver_query.all()
        sel_version = None
        # creating version dict to have a map of version id and bnumbers
        version_dict = {}
        for p in all_ver:
            version_dict[p.id] = p.bn
            if p.bn == sel_build.bn:
                sel_version = p.id
        
        sel_run_query = session.query(UnitTestRun._id,UnitTestRun.platform,UnitTestRun.status)
        sel_run_query = sel_run_query.filter(UnitTestRun._version == sel_version)
        sel_run_query = sel_run_query.filter(UnitTestRun.status != UnitTestStatus.crash)
        sel_run_query = sel_run_query.order_by(desc(UnitTestRun.platform), desc(UnitTestRun.start))
        sel_run_data = sel_run_query.all()

        sel_run_ids = {}
        for run in sel_run_data:
            sel_run_ids[run._id] = [run.platform,run.status]

        run_query = session.query(UnitTestRun._id,UnitTestRun.platform,UnitTestRun._version)
        run_query = run_query.filter(UnitTestRun._version.in_(version_dict.keys()))
        run_query = run_query.order_by(desc(UnitTestRun.platform), desc(UnitTestRun.start))
        run_query = run_query.filter(UnitTestRun.status != UnitTestStatus.crash)
        run_data = run_query.all()
        
        run_ids = {}
        run_id_lst = []
        run_platform = {}
        for run in run_data:
            run_id_lst.append(run._id)
            run_ids[run._id] = run._version
            run_platform[run._id] = run.platform

        sel_test_query = session.query(UnitTest.method, UnitTest._run)
        sel_test_query = sel_test_query.order_by(desc(UnitTest.status))

        if sSearch:
            # filtering on the search            
            sSearchLst = sSearch.split(" ")
            for isSearch in sSearchLst:
                iSearch = '%' + isSearch + '%'
                sel_test_query = sel_test_query.filter(or_(
                                        UnitTest.method.ilike(iSearch),
                                        UnitTest.classname.ilike(iSearch),
                                        UnitTest.filepath.ilike(iSearch)))
        if tag:
            sTagLst = tag.lower().split()   
            sel_test_query = sel_test_query.join(UnitTest.tags)
            sel_test_query = sel_test_query.filter(Tag.name.in_(sTagLst))

        exaxt_sel_test_query = sel_test_query.filter(UnitTest._run.in_(sel_run_ids.keys()))
        exaxt_sel_test_query_crash = exaxt_sel_test_query.filter(UnitTest.status == UnitTestStatus.crash)
        exaxt_sel_test_query_error = exaxt_sel_test_query.filter(UnitTest.status == UnitTestStatus.error)
        exaxt_sel_test_query_fail = exaxt_sel_test_query.filter(UnitTest.status == UnitTestStatus.failed)
        
        all_sel_test_query = sel_test_query.filter(UnitTest._run.in_(run_id_lst))
        all_sel_test_query_crash = all_sel_test_query.filter(UnitTest.status == UnitTestStatus.crash)
        all_sel_test_query_error = all_sel_test_query.filter(UnitTest.status == UnitTestStatus.error)
        all_sel_test_query_fail = all_sel_test_query.filter(UnitTest.status == UnitTestStatus.failed)        
                
        tests_to_display_data = []
        #tests_to_display_data = [(m[0],m[1]) for m in exaxt_sel_test_query.all()]

        tests_to_display_data.extend((m[0], run_platform[m[1]]) for m in exaxt_sel_test_query_crash.all() if (m[0], run_platform[m[1]]) not in tests_to_display_data)
        tests_to_display_data.extend((m[0], run_platform[m[1]]) for m in exaxt_sel_test_query_error.all() if (m[0], run_platform[m[1]]) not in tests_to_display_data)
        tests_to_display_data.extend((m[0], run_platform[m[1]]) for m in exaxt_sel_test_query_fail.all() if (m[0], run_platform[m[1]]) not in tests_to_display_data)

        tests_to_display_data.extend((m[0], run_platform[m[1]]) for m in all_sel_test_query_crash.all() if (m[0], run_platform[m[1]]) not in tests_to_display_data)
        tests_to_display_data.extend((m[0], run_platform[m[1]]) for m in all_sel_test_query_error.all() if (m[0], run_platform[m[1]]) not in tests_to_display_data)
        tests_to_display_data.extend((m[0], run_platform[m[1]]) for m in all_sel_test_query_fail.all() if (m[0], run_platform[m[1]]) not in tests_to_display_data)

        cache_key = str ((component, sel_build.main, sel_build.sub, "unit_test_grid", sSearch, tag))
        cache_status = cache.get (cache_key, 'has_expired')
        if not cache_status == "has_expired": 
            all_names = cache.get(cache_key) 
        else :
            all_names = []
            all_sel_test_query = all_sel_test_query.order_by(UnitTest.method)
            all_names.extend((m[0], run_platform[m[1]]) for m in all_sel_test_query.all() if (m[0], run_platform[m[1]]) not in all_names)
            if all_names :
                cache.set (cache_key, all_names, 3600)

        tests_to_display_data.extend(m for m in all_names if m not in tests_to_display_data)

        paginator = Paginator(tests_to_display_data , 30)
        page = paginator.page(page_value)
        paged_tests_to_display_data = list(s for s in page.object_list)

        tests_to_display = []
        test_dict = {}
        test_result_map = []
        build_values_len = len(bn_list)
        for idx, tst in enumerate(paged_tests_to_display_data):
            tests_to_display.append(tst[0])
            test_dict[(tst[0], tst[1])] = idx
            test_result_map.append([tst[0], "", [[-1]] * build_values_len])        
        
        final_test_query = session.query(UnitTest)
        final_test_query = final_test_query.filter(UnitTest._run.in_(run_id_lst))
        final_test_query = final_test_query.filter(UnitTest.method.in_(tests_to_display))
        #test_query = test_query.order_by(desc(UnitTest.status))

        for test_result in final_test_query:
            tpl = (test_result.method, run_platform[test_result._run])
            if test_dict.has_key(tpl): 
                tst_idx = test_dict[tpl]
                bn_idx = build_dict[version_dict[run_ids[test_result._run]]]
                test_result_map[tst_idx][1] = run_platform[test_result._run]
                test_result_map[tst_idx][2][bn_idx] = [test_result.status, test_result._id]
  
        return render_to_response('unittest_grid.xhtml',
                                       {'build1':sel_build,
                                        'builds':bn_list,
                                        'tests':test_result_map,
                                        'data': page,
                                        'build_dates': build_dates
                                        })
    

def get_unittest_tags(request):
    """
    This function populates the autocomplete for unit test tags.
    """
    pass            

def get_unittest_exception(request):
    """
    This Function returns the exception string for a unittest
    """
    
    unit_id = request.REQUEST.get("unit_id")
    exc = None
    with session_maker.asgard_read_uncommited_session_provider.get_session () as session:
        try:
            unit_id = int(unit_id)
            unit_query = session.query(db_wrapper.UnitTest)
            unit_query = unit_query.filter(db_wrapper.UnitTest._id == unit_id)
            unittest = unit_query.one()
        finally:
            return render_to_response("unittest_details.xhtml", {"unittest": unittest})
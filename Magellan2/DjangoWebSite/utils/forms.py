'''
Created on 17 sep 2010

@author: Laurent.Ploix
'''
from front_db.asgard_db import db_wrapper
from front_db.fast_db import direct_wrapper
from sqlalchemy import desc
from sqlalchemy.sql.expression import and_, or_, not_
import re
import session_maker
from DjangoWebSite import settings

class QHandler (object):
    prog = re.compile ('(?P<minus>-?)((?P<name>\w+):)?(\"((?P<quoted>\w[\w\ \.-]*)\")|((?P<word>\w[\w\.-]*)\ ))')
    def __init__ (self, q):
        self.neg_keywords = {}
        self.pos_keywords = {}
        self.neg_freewords = []
        self.pos_freewords = []
        
        result = self.prog.finditer(q + " ")
        for i in result:
            name = i.group("name")
            if i.group("minus") == "":
                # positive case
                if name :
                    self.pos_keywords [name] = (i.group("quoted") or i.group("word"))
                else :
                    self.pos_freewords.append (i.group("quoted") or i.group("word"))
            else :
                # negative case
                if name :
                    self.neg_keywords [name] = (i.group("quoted") or i.group("word"))
                else :
                    self.neg_freewords.append (i.group("quoted") or i.group("word"))
        
        
def filter_scenarios (db_query, qh, 
                      sc_name = db_wrapper.ReportScenarioUniqueName.sc_name,
                      sc_id = db_wrapper.ReportVersionScenario.sc_id,
                      sc_status = db_wrapper.ReportVersionScenario.sc_status,
                      br_name = db_wrapper.ReportVersionScenario.br_name,
                      report_class_for_meta = db_wrapper.ReportVersionScenario):
    """
    We specify what class and attributes we use to filter on. The reason is that, by default, the filtering of scenarios
    can be done in different ways, depending on the query that is coming and the joins it contains.
    If the query does not contain a join on ReportScenarioUniqueName, for instance, one has to ovcerride the default behavior
    for the filtering of the scenario name. 
    """
    for word in qh.pos_keywords :
        if word == "name" :
            db_query = db_query.filter (sc_name == qh.pos_keywords[word])
        elif word == "id" :
            db_query = db_query.filter (sc_id == qh.pos_keywords[word])
        elif word == "b":
            db_query = db_query.filter (sc_name.ilike(qh.pos_keywords[word] + "%"))
        elif word == "status":
            i_status = 1
            if qh.pos_keywords[word].lower () in ("passed", "success"): i_status = 1
            elif qh.pos_keywords[word].lower () in ("failed", "fail"): i_status = 2
            elif qh.pos_keywords[word].lower () in ("error", ): i_status = 3
            db_query = db_query.filter (sc_status == i_status)
        elif word == "set" :
            db_query = db_query.filter (br_name == qh.pos_keywords[word])
        elif word == "impl":
            col = getattr(report_class_for_meta, 'sc_' + word)
            db_query = db_query.filter(col == qh.pos_keywords[word])
        elif word in ("authors", "owner", "spr", "descr"):
            col = getattr(report_class_for_meta, 'sc_' + word)
            db_query = db_query.filter(col.ilike('%' + qh.pos_keywords[word] + '%'))
    for word in qh.neg_keywords:
        if word == "name" :
            db_query = db_query.filter(sc_name != qh.pos_keywords[word])
        elif word == "id" :
            db_query = db_query.filter(sc_id != qh.pos_keywords[word])
        elif word == "b":
            db_query = db_query.filter(sc_name.ilike(qh.neg_keywords[word] + "%"))
        elif word == "status":
            i_status = 1
            if qh.neg_keywords[word].lower () in ("passed", "success"): i_status = 1
            elif qh.neg_keywords[word].lower () in ("failed", ): i_status = 2
            elif qh.neg_keywords[word].lower () in ("error", ): i_status = 3
            db_query = db_query.filter(sc_status != i_status)
        elif word == "set" :
            db_query = db_query.filter(br_name != qh.neg_keywords[word])
        elif word in ("authors", "owner", "spr", "descr"):
            col = getattr(report_class_for_meta, 'sc_' + word)
            db_query = db_query.filter(or_(not_(col.ilike('%'+qh.neg_keywords[word]+'%')),
                                           col == None))
        elif word == "impl":
            col = getattr(report_class_for_meta, 'sc_' + word)
            db_query = db_query.filter(or_(col != qh.neg_keywords[word],
                                           col == None))

       
    for word in qh.pos_freewords :
        db_query = db_query.filter (sc_name.ilike ("%" + word + "%"))

    for word in qh.neg_freewords :
        db_query = db_query.filter (not_(sc_name.ilike("%" + (word.replace ("\\", "")
                                                                  .replace ("%", "")
                                                                  .replace ("'", "")) + "%")))
        
    return db_query

def filter_columns (db_query, qh, col_name = db_wrapper.ReportColumnUniqueName.col_name):
    """
    Takes a database query as input and returns it as an output.
    It will filter the query (add a WHERE clause) 
    """
    for word in qh.pos_freewords :
        db_query = db_query.filter (col_name.ilike("%" + word + "%"))
    for word in qh.neg_freewords :
        db_query = db_query.filter (col_name.ilike("%" + (word.replace ("\\", "")
                                                                  .replace ("%", "")
                                                                  .replace ("'", "")) + "%"))
    for word in qh.pos_keywords :
        if word == "name" :
            db_query = db_query.filter (col_name == qh.pos_keywords[word])
    for word in qh.neg_keywords :
        if word == "name" :
            db_query = db_query.filter (col_name != qh.pos_keywords[word])
    return db_query

def filter_labels (db_query, qh, st_label=db_wrapper.ReportLabelUniqueName.st_label):
    for word in qh.pos_freewords :
        db_query = db_query.filter (st_label.ilike("%" + word + "%"))
    for word in qh.neg_freewords :
        db_query = db_query.filter (not_(st_label.ilike("%" + (word.replace ("\\", "")
                                                                  .replace ("%", "")
                                                                  .replace ("'", "")) + "%")))
    for word in qh.pos_keywords :
        if word == "name" :
            db_query = db_query.filter (st_label == qh.pos_keywords[word])
    for word in qh.neg_keywords :
        if word == "name" :
            db_query = db_query.filter (st_label != qh.pos_keywords[word])
    return db_query

def filter_versions (db_query, qh, session=None, filter_last=False):
    """
    Special case: if we have a limit in the number of versions (keyword : last), then we want to list of available versions
    then only modify the query with an "in" keyword for the version names corresponding to the last N version.
    """
    componentFound = False
    for word in qh.pos_keywords :
        if word in ("rel", ): 
            
            releasev = qh.pos_keywords["rel"]
            
            if qh.pos_keywords.has_key("comp"):
                componentv = qh.pos_keywords["comp"]
            else :
                componentv = "PRIME"
            
            with session_maker.fast_read_uncommited_session_provider.get_session () as session_fast:
            
                build_number_class = direct_wrapper.get_FAST_class("BuildNumber", session_fast)
                fast_query = session_fast.query (build_number_class)
                fast_query = fast_query.filter_by (component = componentv)
                fast_query = fast_query.filter_by (release_number = releasev)
                fast_query = fast_query.filter_by (alt_bnumber = 0)
    
            # fast_query = fast_query.filter(not_(build_number_class.sprs_included.like('264097;')))
    
            builds = fast_query.all()
                        
            if len(builds) != 0 :
                
                build_data = list (set([str(bld.bn) for bld in builds]))
                build_data.sort()
                
                db_query = db_query.filter (db_wrapper.Version.main == builds[0].main)
                db_query = db_query.filter (db_wrapper.Version.sub == builds[0].sub)
                db_query = db_query.filter (db_wrapper.Version.bn.in_(build_data))  
                #db_query = db_query.filter (and_(db_wrapper.Version.bn <= int(bn_f[-1][2]), db_wrapper.Version.bn >= int(bn_f[0][2])))
                db_query = db_query.filter (db_wrapper.Version.abn == 0)
                
        elif word == "comp":
            db_query = db_query.filter (db_wrapper.Version.comp_type == qh.pos_keywords["comp"].upper())
            componentFound = True
        elif word != "last" :
            db_query = db_query.filter (getattr (db_wrapper.Version, word) == qh.pos_keywords[word])
        elif word == "last" and filter_last is True:
            local_query = session.query (db_wrapper.Version.name)
            local_query = filter_versions(local_query, qh, None, filter_last=False) # Do not use "last" keyword !
            local_query = local_query.order_by (desc (db_wrapper.Version.main),
                                desc(db_wrapper.Version.sub),
                                desc(db_wrapper.Version.sub2),
                                desc(db_wrapper.Version.hf),
                                desc(db_wrapper.Version.p),
                                desc(db_wrapper.Version.bn),
                                desc(db_wrapper.Version.abn),
                                desc(db_wrapper.Version.dat),
                                )
            names = [n[0] for n in local_query [:int (qh.pos_keywords["last"])]]
            db_query = db_query.filter (db_wrapper.Version.name.in_(names))

    if not componentFound:
        db_query = db_query.filter (db_wrapper.Version.comp_type == "PRIME")

    for word in qh.neg_keywords :
        if word in ("rel","comp"): pass
        db_query = db_query.filter (getattr (db_wrapper.Version, word) != qh.neg_keywords[word])
    db_query = db_query.filter (db_wrapper.Version.name != '')

    for word in qh.pos_freewords :
        db_query = db_query.filter (db_wrapper.Version.name.ilike("%" + word + "%"))

    for word in qh.neg_freewords :
        db_query = db_query.filter (not_(db_wrapper.Version.name.ilike("%" + (word.replace ("\\", "")
                                                                  .replace ("%", "")
                                                                  .replace ("'", ""))+ "%")))

    return db_query


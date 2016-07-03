'''
Created on 5 nov 2010

@author: Laurent.Ploix
'''
import sqlalchemy
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from front_db.fast_db import meta_wrapper, direct_wrapper

uri = "mssql://Magellan:Magellan@emeastofast02/ARSystem"
normal_engine = create_engine(uri, 
                              poolclass=sqlalchemy.pool.QueuePool, 
                              echo=False, 
                              pool_size=20,
                              connect_args={'unicode_results': True})
from unittest import TestCase

class TestConnection (TestCase):
    def test_can_have_session (self):
        Session = sessionmaker(bind=normal_engine)
        session = Session()
        session.close()
        
class ConnectedTestCase (TestCase):
    def setUp (self):
        Session = sessionmaker(bind=normal_engine)
        self.session = Session()
    def tearDown (self):
        self.session.close()
        
class TestSchema (ConnectedTestCase):  
    def test_read_first_item_in_ArSchema_and_access_fields (self):
        db_query = self.session.query (meta_wrapper.ArSchema)
        item = db_query.first ()
        item.name 
        item.schema_id 
        item.schema_type 
        item.timestamp 
        item.owner 
        item.last_changed 
        item.core_version 
        item.num_fields 
        item.num_vuis 
        item.default_vui 
        item.next_id 
        item.max_stat_enums 
        item.next_field_id
        self.assertNotEqual (None, item.fields) # must be a backref to fields
    
    def test_read_first_item_in_Field_and_access_fields (self):
        db_query = self.session.query (meta_wrapper.Field)
        item = db_query.first ()
        item.record_id
        item.schema_id
        item.schema
        item.field_id
        item.field_name
        item.field_type 
        item.timestamp 
        item.owner
        item.last_changed 
        item.datatype
        item.f_option 
        item.create_mode
        item.fb_option 
        item.default_value 
        item.change_diary 
        item.help_text
        self.assertNotEqual (None, item.schema)
        self.assertTrue (item in item.schema.fields.all())
    
class TestSPREntry (ConnectedTestCase):
    def test_read_first_item_in_SPREntry_and_access_fields (self):
        db_query = self.session.query (direct_wrapper.get_FAST_class("1:SPREntry", self.session)).filter_by (spr_id = 297255)
        item = db_query.first ()
        item.spr_id
        item.spr_submitter
        item.created
        item.assigned_to
        item.short_description_spr
        item.external_spr_description
        item.clean_spr_description
        item.component
        item.module
        item.klass
        item.severity
        item.spr_status
        item.spr_diary
        item.clean_spr_diary
    
    def test_list_all_sprs (self):
        db_query = self.session.query (direct_wrapper.get_FAST_class("1:SPREntry", self.session).spr_id, 
                                       direct_wrapper.get_FAST_class("1:SPREntry", self.session).short_description_spr)
        for item in db_query.all():
            item.short_description_spr
            
class testReleasesFixedIn (ConnectedTestCase):
    def test_read_releases_fixed_in (self):
        db_query = self.session.query (direct_wrapper.get_FAST_class("1:5:ReleasesFixedIn", self.session))
        db_query = db_query.order_by (desc (direct_wrapper.get_FAST_class("1:5:ReleasesFixedIn", self.session).build_number))
        db_query = db_query.filter_by (component = "PRIME")
        db_query = db_query.filter (direct_wrapper.get_FAST_class("1:5:ReleasesFixedIn", self.session).build_number == "4.7.195.0")

        for item in db_query:
            item.build_number
            item.spr_id
            item.spr_item # getting the actual spr
            item.spr_item.clean_spr_description
        
class TestComponent (ConnectedTestCase):
    def test_read_first_item_in_Component_and_access_fields (self):
        db_query = self.session.query (direct_wrapper.get_FAST_class("5:2:Components", self.session))
        item = db_query.first ()
        item.component_id
        item.component
        item.component_comment
        
    def test_can_read_releases_per_component_items (self): 
        db_query = self.session.query (direct_wrapper.get_FAST_class("5:2:Components", self.session)) \
            .order_by (direct_wrapper.get_FAST_class("5:2:Components", self.session).component)
        for component in db_query[2:]:
            releases_per_component = component.releases_per_component_items
            for item in releases_per_component : 
                item.component
                item.build_number
                self.assertTrue (item.component_item is component)
        
    def test_can_read_build_number_items (self): 
        db_query = self.session.query (direct_wrapper.get_FAST_class("5:2:Components", self.session)).filter_by (component = "PRIME")
        for component in db_query:
            build_numbers = component.build_number_items
            for item in build_numbers : 
                item.component, item.build_number
                self.assertTrue (item.component_item is component)
        
class TestBuildNumber (ConnectedTestCase):
    def test_read_first_item_in_BuildNumber_and_access_fields (self):
        db_query = self.session.query (direct_wrapper.get_FAST_class("5:1:6:BuildNumber", self.session))
        item = db_query.first ()
        item.request_id
        item.component_id
        item.component
        item.major
        item.main
        item.minor
        item.sub
        item.bnumber
        item.bn
        item.alt_bnumber
        item.abn
        
    def test_read_BuildNumber_component_item (self):
        db_query = self.session.query (direct_wrapper.get_FAST_class("5:1:6:BuildNumber", self.session))
        item = db_query.first ()
        item.component_item.component_id

    def test_read_BuildNumber_build_comments_items (self):
        db_query = self.session.query (direct_wrapper.get_FAST_class("5:1:6:BuildNumber", self.session)).order_by (
                                                            direct_wrapper.get_FAST_class("5:1:6:BuildNumber", self.session).major,
                                                            direct_wrapper.get_FAST_class("5:1:6:BuildNumber", self.session).minor,
                                                            direct_wrapper.get_FAST_class("5:1:6:BuildNumber", self.session).bnumber,
                                                            direct_wrapper.get_FAST_class("5:1:6:BuildNumber", self.session).alt_bnumber
                                                                            )
        for item in db_query [-100:]:
            for build_comment in item.build_comment_items :
                self.assertTrue (build_comment.build_number_item is item)
                
    def test_read_build_comments_for_one_version_and_one_component (self):
        db_query = self.session.query (direct_wrapper.get_FAST_class("5:1:7:BuildComment", self.session))
        db_query = db_query.join (direct_wrapper.get_FAST_class("5:1:6:BuildNumber", self.session))
        db_query = db_query.filter (direct_wrapper.get_FAST_class("5:1:7:BuildComment", self.session).component == "PRIME")
        db_query = db_query.filter (direct_wrapper.get_FAST_class("5:1:6:BuildNumber", self.session).major == 4)
        db_query = db_query.filter (direct_wrapper.get_FAST_class("5:1:6:BuildNumber", self.session).minor == 7)
        for comment in db_query:
            comment.clean_comment # getting the text
            comment.component
            comment.component_item # the actual item from the database
            comment.build_number_item.main, comment.build_number_item.sub, comment.build_number_item.bn 
        
class TestReleasesPerComponent (ConnectedTestCase):
    def test_read_first_item_in_ReleasesPerComponent_and_access_fields (self):
        db_query = self.session.query (direct_wrapper.get_FAST_class("5:1:ReleasesPerComponent", self.session))
        item = db_query.first ()
        item.component_release_id
        item.component_id
        item.component

    def test_read_ReleasesPerComponent_component_item (self):
        db_query = self.session.query (direct_wrapper.get_FAST_class("5:1:ReleasesPerComponent", self.session)).filter_by (release_number = "2010.2.1")
        item = db_query.first ()
        item.component_item
        item.build_number
        item.build_number_item
        self.assertEquals (item.build_number_item.release_item, item)

class TestBuildComment (ConnectedTestCase):
    def test_read_first_item_in_BuildComment_and_access_fields (self):
        db_query = self.session.query (direct_wrapper.get_FAST_class("5:1:7:BuildComment", self.session))
        item = db_query.first ()
        item.request_id
        item.diary_field
        item.comment
        item.build_number
        item.regression_accepted
        item.regression_accepted_by
        item.build_number_request_id
        
    def test_read_BuildComment_build_number_item (self):
        db_query = self.session.query (direct_wrapper.get_FAST_class("5:1:7:BuildComment", self.session))
        item = db_query.first ()
        item.build_number_item
        
class TestUser (ConnectedTestCase):
    def test_read_one_User_and_acces_fields (self):
        db_query = self.session.query (direct_wrapper.get_FAST_class("User", self.session)) \
            .filter (direct_wrapper.get_FAST_class("User", self.session).full_name.like ("%plo%"))
        for item in db_query:
            item.user_status
            item.full_name
            item.login_name
            item.email_address
            item.location
            item.department
            item.work_phone
            item.manager

    def test_read_sprs_from_users (self):
        db_query = self.session.query (direct_wrapper.get_FAST_class("User", self.session))\
            .filter (direct_wrapper.get_FAST_class("User", self.session).full_name.like ("%plo%"))
        for item in db_query:
            for spr in item.assigned_to_items :
                self.assertTrue (spr.assigned_to_item.one() is item)
            for spr in item.spr_submitter_items :
                self.assertTrue (spr.spr_submitter_item.one() is item)

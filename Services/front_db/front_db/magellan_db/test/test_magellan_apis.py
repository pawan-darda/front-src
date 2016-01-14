# -*- coding: latin-1 -*-
import unittest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from front_db.magellan_db.mag_db_wrapper import Wall, Portlet, Base
import sqlalchemy

class DbTestCase(unittest.TestCase):
    
    def setUp (self):
        engine = create_engine('sqlite:///:memory:', echo=False)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        metadata = Base.metadata
        metadata.create_all(engine)
        
class TestWallCreation(DbTestCase):
    
        def test_no_walls_at_beginning(self):
            self.assertEquals(0,self.session.query(Wall).count())
            
        def test_wall_creation(self):    #Testing mapping of the table
            wall_1 = Wall(name = 'test_wall_1',
                           description = 'test wall 1 description')
            
            wall_2 = Wall(name = 'test_wall_2',
                          description = 'test wall 2 description')
            self.session.add_all([wall_1, wall_2])
            self.session.commit()
            self.assertEquals(2,self.session.query(Wall).count())
              
            self.session.delete(wall_1)
            self.session.commit()
            self.assertEquals(1, self.session.query(Wall).count())
            self.session.delete(wall_2)
            self.session.commit()
            self.assertEquals(0, self.session.query(Wall).count())
            #Testing the not null constraint
            wall = Wall(name = None, description = "description")
            self.session.add(wall)
            self.assertRaises(sqlalchemy.exc.IntegrityError, self.session.commit) 
            self.session.rollback()
            wall = Wall(name = 'wall_name', description = None)
            self.session.add(wall)
            self.session.commit()
            self.assertEquals('wall_name', self.session.query(Wall)
                              .filter(Wall.name == 'wall_name')[0].name)
            
            self.session.delete(wall)
            #Testing the unique name constraint
            wall_1 = Wall(name = 'same_name', description = 'xyz')
            self.session.add(wall_1)
            self.session.commit()
            
            wall_2 = Wall(name = 'same_name', description = 'sss')
            self.session.add(wall_2)
            self.assertRaises(sqlalchemy.exc.IntegrityError, self.session.commit) 
            self.session.rollback()
            self.session.close()
                  
        def test_portlet_is_added_to_database(self):
            #Testing the mapping
            wall_1 = Wall(name = 'test_wall_1',
                          description = 'test wall 1 description')
            self.session.add(wall_1)
            self.session.commit()
            portlet_1 = Portlet(type = 'scenario_count',
                                argument = 'version:4.7,buildnumber: 2010.4.7-xx.xx.xx',
                                position = 'A:1',
                                wall =wall_1)
            self.session.add(portlet_1)
            self.session.commit()
           
            self.assertEquals(1,self.session.query(Portlet).count())
            
        def test_portlet (self):
            
            wall_1 = Wall(name = 'test_wall_1',
                          description = 'test wall 1 description')
            self.session.add(wall_1)
            self.session.commit()
            portlet_1 = Portlet(type = 'scenario_count',
                                argument = 'version:4.7,buildnumber: 2010.4.7-xx.xx.xx',
                                position = 'A:1',
                                wall =wall_1)
            self.session.add(portlet_1)
            self.session.commit()

            portlet_list= self.session.query(Portlet).join(Wall).filter(Wall.name == 'test_wall_1').all()
            wall_list = self.session.query(Wall).filter(Wall.name == 'test_wall_1').all()
            self.assertEquals(portlet_list[0].wall_id, wall_list[0].id)

            self.session.delete(wall_1)
            self.session.commit()
            #self.session.delete(portlet_1)
            #self.session.commit()
            #Testing the not null constraint
            wall_1 = Wall(name = 'test_wall_portlet',
                          description = 'test wall portlet description')
            portlet_1 = Portlet(type = None,
                                argument = 'version:4.7,buildnumber: 2010.4.7-xx.xx.xx',
                                position = 'A:1',
                                wall =wall_1)
            self.session.add(portlet_1)
            self.assertRaises(sqlalchemy.exc.IntegrityError, self.session.commit) 
            self.session.rollback()
            
            portlet_1 = Portlet(type = "Some Type",
                                argument = None,
                                position = 'A:1',
                                wall =wall_1)
            self.session.add(portlet_1)
            self.assertRaises(sqlalchemy.exc.IntegrityError, self.session.commit) 
            self.session.rollback()
            
            portlet_1 = Portlet(type = "Some Type",
                                argument = 'version:4.7,buildnumber: 2010.4.7-xx.xx.xx',
                                position = None,
                                wall =wall_1)
            self.session.add(portlet_1)
            self.assertRaises(sqlalchemy.exc.IntegrityError, self.session.commit) 
            self.session.rollback()
            self.session.close()
            
if __name__ == '__main__':
    unittest.main()


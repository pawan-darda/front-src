# -*- coding: latin-1 -*-
#
# $Id: db_report.py 1298 2010-05-05 11:43:29Z laurent.ploix $

#
# This is the Database output generator
#

#import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import backref, relation

Base = declarative_base()

    
class ArSchema(Base):
    __tablename__ = 'arschema'
    name = Column(String(254))
    schema_id = Column("schemaId", 
                       Integer, 
                       primary_key=True)
    schema_type = Column("schemaType", Integer)
    timestamp = Column(Integer)
    owner = Column(String(254))
    last_changed = Column("lastChanged", String(254))
    core_version = Column("coreVersion", Integer)
    num_fields = Column("numFields", Integer)
    num_vuis = Column("numVuis", Integer)
    default_vui = Column("defaultVui", String(254))
    next_id = Column("nextId", Integer)    # What does this one point to ?
    max_stat_enums = Column("maxStatEnums", Integer)
    fields = None # backref that comes with definition of schema in Field
    next_field_id = Column("nextFieldId", Integer)
    
    @property
    def nextField (self):
        return self.fields.filter_by (schemaId = self.schema_id)

class Field (Base):
    __tablename__ = "field"
    record_id = Column("recordId", 
                       Integer, 
                       primary_key=True)
    schema_id = Column("schemaId", 
                       Integer, 
                       ForeignKey(ArSchema.schema_id))
    field_id= Column("fieldId", Integer)
    field_name = Column("fieldName", String(254))
    field_type = Column("fieldType", Integer)
    timestamp = Column(Integer)
    owner = Column(String(254))
    last_changed = Column("lastChanged", String(254))
    datatype = Column(Integer)
    f_option = Column("fOption", Integer)
    create_mode = Column("createMode", Integer)
    fb_option = Column("fbOption", Integer)
    default_value = Column("defaultValue", String)
    change_diary = Column("changeDiary", String)
    help_text = Column("helpText", String)
    schema = relation (ArSchema, 
                       primaryjoin=schema_id == ArSchema.schema_id, 
                       backref=backref('fields', lazy='dynamic')
                       )
    

from unittest import TestCase
#import codecs
from front_utils.mappings.people import PeopleMapper
#--------------------------------------
from StringIO import StringIO
class TestPeopleMapper (TestCase):

    def testOpenRealFile (self):
        PeopleMapper (StringIO ("""Login Name","Full Name","Email Address"
            "anup.devhade","Anup Devhade","Anup.Devhade@sos.sungard.com"
            "saurabh.purandare","Saurabh Purandare","Saurabh.Purandare@sos.sungard.com"
            """))
        
    def testCreateValues (self):
        s = """"Login Name","Full Name","Email Address"
            "anup.devhade","Anup Devhade","Anup.Devhade@sos.sungard.com"
            "saurabh.purandare","Saurabh Purandare","Saurabh.Purandare@sos.sungard.com"
            """
        man = PeopleMapper (StringIO (s))
        assert man.values [0][0] == "anup.devhade"        
        assert man.values [0][1] == "anup devhade"        
        assert man.values [0][2] == "anup.devhade@sos.sungard.com", "%s <> %s"%(man.values [0][2], "Anup.Devhade@sos.sungard.com")
        assert len (man.values) == 2
        
    def testDict (self):
        s = """"Login Name","Full Name","Email Address"
            "anup.devhade","Anup Devhade","Anup.Devhade@sos.sungard.com"
            "saurabh.purandare","Saurabh Purandare","Saurabh.Purandare@sos.sungard.com"
            """
        man = PeopleMapper (StringIO (s))
        assert man.fromlogin ["anup.devhade"]["fullname"] == "anup devhade"   
        assert man.fromlogin ["anup.devhade"]["email"] == "anup.devhade@sos.sungard.com"   
        assert man.fromfullname ["anup devhade"]["login"] == "anup.devhade"   
        assert man.fromfullname ["anup devhade"]["email"] == "anup.devhade@sos.sungard.com"   
        
    
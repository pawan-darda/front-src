from front_utils.versions import get_version, PrimeVersion, AmasVersion, SbVersion
import unittest


class TestVersionFactory (unittest.TestCase):
    """
      Test class for softbroker version parsing logic
    """
    
    def test_incorrect_version(self):
        self.assertRaises(ValueError, get_version, '', "6.9.5-20111125_100")
        self.assertRaises(ValueError, get_version, None, "6.9.5-20111125_100")
        self.assertRaises(ValueError, get_version, 'foo', "6.9.5-20111125_100")
        
    def test_for_prime_comp(self):
        self.assertTrue(isinstance(get_version('PRIME',"2009.2.3-4.4.446.0"), PrimeVersion))
 
    def test_for_amas_comp(self):
        self.assertTrue(isinstance(get_version('AMAS',"6.5.40-20110908_2"), AmasVersion))
        
    def test_for_softbroker_comp(self):
        self.assertTrue(isinstance(get_version('SOFTBROKER',"6.9.5-20111125_1"), SbVersion))
      

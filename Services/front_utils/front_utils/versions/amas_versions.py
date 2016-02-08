'''
Created on 22 sep 2011

@author: laurent.ploix
'''
from front_utils.versions import VersionParser
import re


class AmasVersionParsingError (Exception):
    """
     Exception class for Amas component.
    """
    pass


class AmasVersion (VersionParser):
    """
      Parser class for AMAS component
    """

    VERSION_RE = re.compile("(?P<main>\d+)\.(?P<sub>\d+)\.(?P<sub2>\d+)-(?P<year>\d\d\d\d)(?P<month>\d\d)(?P<day>\d\d)_(?P<ordinal>\d\d?)$")

    def __init__(self, name, component=None):
        super(AmasVersion, self).__init__(name,
                                          component,
                                          exc_cls=AmasVersionParsingError)

    @property
    def bn(self):
        """
         Build number property
        """
        return self.ordinal \
               + self.day * 100\
               + self.month * 100 * 100 \
               + self.year * 100 * 100 * 100

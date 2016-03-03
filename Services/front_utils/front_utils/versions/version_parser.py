'''
Created on 29 November 2011

@author: Laurent.Ploix
'''
import datetime


class VersionParsingError(Exception):
    """
      Exception class for version parser
    """
    pass


class VersionParser(object):
    """
      This class acts as a base class for parsing versions.
    """
    VERSION_RE = None

    def __init__(self, name, component, exc_cls=VersionParsingError):
        self.name = name
        self.main = None
        self.sub = None
        self.sub2 = None
        self.year = None
        self.month = None
        self.day = None
        self.ordinal = None
        self.date = None
        self.component = component
        self.nice = ""

        m = self.VERSION_RE.match(name)
        if m:
            d = m.groupdict()
            self.main = int(d["main"])
            self.sub = int(d["sub"])
            self.sub2 = int(d["sub2"])
            self.year = int(d["year"])
            self.month = int(d["month"])
            self.day = int(d["day"])
            self.ordinal = int(d["ordinal"])
            try:
                self.date = datetime.datetime(self.year, self.month, self.day)
            except ValueError, e:
                raise exc_cls(e)
        else:
            raise exc_cls("Could not parse %r", name)

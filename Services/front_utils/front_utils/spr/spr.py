
class SPR (object):
    def __init__ (self, id, provider = None):
        self.__id = id
        self.__provider = provider
        self.__short_desc = None
        
    @property
    def id (self): return self.__id

    def __eq__ (self, other): return self.id == other.id    
    def __ne__ (self, other): return not self == other
    
    @property
    def short_desc (self):
        if self.__short_desc is None and self.__provider :
            self.__short_desc = self.__provider.spr_short_description (self.id)
        return self.__short_desc
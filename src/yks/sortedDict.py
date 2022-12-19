class SortedDict(dict):
    """
    Custom Dictionary used for the yakuake-sessions software
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.keyOrder = dict.keys(self)
    def keys(self):
        return self.keyOrder
    def iterkeys(self):
        for key in self.keyOrder:
            yield key
    __iter__ = iterkeys
    def items(self):
        return [(key, self[key]) for key in self.keyOrder]
    def iteritems(self):
        for key in self.keyOrder:
            yield (key, self[key])
    def values(self):
        return [self[key] for key in self.keyOrder]
    def itervalues(self):
        for key in self.keyOrder:
            yield self[key]
    def __setitem__(self, key, val):
        # self[key] = val
        self.update({key: val})
       # self.keyOrder.append(key)
       #  dict.__setitem__(self, key, val)
    def __delitem__(self, key):
        self.keyOrder.remove(key)
        dict.__delitem__(self, key)
from __future__ import absolute_import


class User(dict):
    """Data model for User, DynamicDocument allows to add fields dynamically"""
    def __init__(self, *args, **kw):
        super(User, self).__init__(*args, **kw)
        self.itemlist = super(User, self).keys()

    def __setitem__(self, key, value):
        # TODO: what should happen to the order if
        #       the key is already in the dict
        # self.itemlist.append(key)
        super(User, self).__setitem__(key, value)

    def __iter__(self):
        return iter(self.itemlist)

    def keys(self):
        return self.itemlist

    def values(self):
        return [self[key] for key in self]

    def itervalues(self):
        return (self[key] for key in self)

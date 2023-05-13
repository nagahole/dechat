# Idea by https://discuss.python.org/t/syntax-for-aliases-to-keys-of-python-dictionaries/14992
class AliasDictionary(dict):
    """
    To solve the problem of the user needing to be able to 
    access a channel by its name and the protocol needing to be 
    able to access a channel by its id

    Only supports one alias :(
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.aliases = {}

    def __getitem__(self, key):

        # Will get the key an alias points to if exists, otherwise
        # will try to access the base dictionary with just the given key
        key = self.aliases.get(key, key) 

        return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        if type(key) == tuple:
            alias = key[1]
            self.aliases[alias] = key[0]

            return dict.__setitem__(self, key[0], value)
        else:
            # Will get the key an alias points to if exists, otherwise
            # will try to access the base dictionary with just the given key
            key = self.aliases.get(key, key)

            return dict.__setitem__(self, key, value)

    def __iter__(self):
        """
        Need to modify this dunder method so that when you run
        "alias in AliasDictionary" it will return true, because
        without this code when you call in on an AliasDictionary
        it will only iterate through the keys, not the aliases
        """

        # Not the cleanest solution because iterating through builtin
        # python dictionaries uses a dict_keyiterator under the hood,
        # but it works
        alias_keys = self.aliases.keys()
        all_keys = list(dict.keys(self))
        all_keys.extend(alias_keys)

        return iter(all_keys)

    def __contains__(self, key):
        return key in self.aliases or dict.__contains__(self, key)

    def add_alias(self, key, alias):
        self.aliases[alias] = key

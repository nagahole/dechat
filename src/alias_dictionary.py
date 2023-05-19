# Idea by https://discuss.python.org/t/syntax-for-aliases-to-keys-of-python-dictionaries/14992
class AliasDictionary:
    """
    To solve the problem of the user needing to be able to 
    access a channel by its name and the protocol needing to be 
    able to access a channel by its id
    """
    def __init__(self, *args, **kwargs):
        self.dict = dict(*args, **kwargs)
        self.aliases = {}

    def __getitem__(self, key):

        # Will get the key an alias points to if exists, otherwise
        # will try to access the base dictionary with just the given key
        key = self.aliases.get(key, key) 

        if key in self.dict:
            return self.dict[key]

        raise KeyError(f"{key} not found")

    def __setitem__(self, key, value):
        # Will get the key an alias points to if exists, otherwise
        # will try to access the base dictionary with just the given key
        key = self.aliases.get(key, key)

        self.dict[key] = value

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
        all_keys = list(self.dict.keys())
        all_keys.extend(alias_keys)

        return iter(all_keys)

    def __contains__(self, key):
        return key in self.aliases or key in self.dict

    def __len__(self):
        return len(self.dict)

    def values(self):
        return self.dict.values()

    def add_alias(self, key, alias):
        self.aliases[alias] = key

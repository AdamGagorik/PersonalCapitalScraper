"""
A script to play with the personal capital api.
"""
import pandas as pd
import dataclasses
import functools
import inspect
import typing
import yaml
import os


from scraper.handler import PCHandler


# noinspection PyArgumentList
@dataclasses.dataclass()
class ObjectMapping:
    """
    A base class to aid in creating objects from JSON.
    """
    @classmethod
    def safe_init(cls, **kwargs) -> 'ObjectMapping':
        """
        Create an object from the keyword arguments.
        Silently ignore any keyword arguments that are not known.
        """
        skwargs = {}
        for name in inspect.signature(cls).parameters:
            try:
                skwargs[name] = kwargs[name]
            except KeyError:
                pass

        return cls(**skwargs)

    def fillna(self, rules: typing.List[typing.MutableMapping]) -> 'ObjectMapping':
        """
        Fill in missing values based on the list of rules.

        The rules is a list of of `where` and `value` mappings.
        An update occurs when all instance variables match the `where` items.
        The items from the `values` mapping are used when the update step occurs.

        Parameters:
            rules: A list of rule mappings.

        Returns:
            The updated instance with missing values filled in based on the rules.
        """
        for i, rule in enumerate(rules):
            if self._matches(**rule['where']):
                self._update(**rule['value'])
                rules.pop(i)
                break

        return self

    def _matches(self, **kwargs) -> bool:
        """
        Check to see if key-value pair matches.

        Returns:
            True if all items match.
        """
        if not kwargs:
            return False

        for k, v in kwargs.items():
            if getattr(self, k) != v:
                return False

        return True

    def _update(self, **kwargs):
        """
        Update attributes using key-value pairs.
        """
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise AttributeError(k)


class Scraper:
    """
    A base class that can preform API calls or reload data using a PC handler.
    """
    __reload_yaml__: str = '{dt:%Y-%m-%d}-scraper.yaml'
    __fillna_yaml__: str = 'fillna-scraper.yaml'
    __store_class__: ObjectMapping = ObjectMapping

    def __init__(self, handler: PCHandler, store: str = 'scraper.yaml'):
        """
        Parameters:
            handler: The personal capital api handler instance.
            store: The basename stub for the storage file.
        """
        #: The personal capital api handler
        self.handler: PCHandler = handler
        #: The name of the file to store the API results in
        self.store: str = os.path.join(handler.config.workdir, self.__reload_yaml__)
        self.store: str = self.store.format(dt=handler.config.dt, self=self)
        #: The data that was fetched as json from the API call
        self.data: dict = {}

    def fetch(self, **kwargs) -> list:
        """
        The logic of the API call.
        """
        raise NotImplementedError

    def reload(self, force: bool = False, **kwargs) -> 'Scraper':
        """
        Download the data from the PC API or reload it from disk.

        Parameters:
            force: Use the API even if the store exists?
        """
        if force or not os.path.exists(self.store):
            self.data = self.fetch(**kwargs)
            with open(self.store, 'w') as stream:
                yaml.dump(self.data, stream)
        else:
            with open(self.store, 'r') as stream:
                self.data = yaml.load(stream, yaml.SafeLoader)

        return self

    @property
    @functools.lru_cache(maxsize=1)
    def rules(self):
        """
        Get the list of fillna rules from the yaml file.
        """
        path: str = os.path.join(self.handler.config.workdir, self.__fillna_yaml__)
        if os.path.exists(path):
            return yaml.load(open(path, 'r'), yaml.SafeLoader).get('rules', [])
        else:
            return []

    @property
    @functools.lru_cache(maxsize=1)
    def objects(self) -> list:
        """
        Get the store object instances.

        Returns:
            A list of transaction objects.
        """
        return [self.__store_class__.safe_init(**transaction).fillna(self.rules) for transaction in self.data]

    def __iter__(self) -> typing.Generator[ObjectMapping, None, None]:
        """
        Iterate over the JSON objects.

        Yields:
            The JSON objects.
        """
        for instance in self.objects:
            yield instance

    @property
    @functools.lru_cache(maxsize=1)
    def frame(self) -> pd.DataFrame:
        """
        Get the transaction objects as a dataframe.

        Returns:
            The transactions dataframe.
        """
        return pd.DataFrame(dataclasses.asdict(obj) for obj in self.objects)

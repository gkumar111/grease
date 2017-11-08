from tgt_grease.core import GreaseContainer
import pkg_resources
import os
import fnmatch
import json


class PrototypeConfig(object):
    """Responsible for Scanning/Detection/Scheduling configuration

    Attributes:
        ioc (GreaseContainer): IOC access
        Configuration (dict): the raw configuration loaded

    """

    def __init__(self, ioc=None):
        if ioc and isinstance(ioc, GreaseContainer):
            self.ioc = ioc
        else:
            self.ioc = GreaseContainer()
        self.Configuration = self.load()

    def load(self):
        """[Re]loads configuration data about the current execution node

        Configuration data loads from 3 places in GREASE. The first is internal to the package, if one were to manually
        add their own files into the package in the current directory following the file pattern. The next is following
        the same pattern but loaded from `<GREASE_DIR>/etc/`. The final place GREASE looks for configuration data is
        from the `configuration` collection in MongoDB

        Returns:
            dict: Configuration information

        """
        # fill out raw results
        conf = dict()
        conf['configuration'] = dict()
        conf['configuration']['pkg'] = self.load_from_fs(
            pkg_resources.resource_filename('tgt_grease.enterprise.Model', 'config/')
        )
        conf['configuration']['fs'] = self.load_from_fs(
            self.ioc.getConfig().get('Configuration', 'dir')
        )
        conf['configuration']['mongo'] = self.load_from_mongo()
        # split by source & detector
        return conf

    def load_from_fs(self, directory):
        """Returns all configurations from tgt_grease.enterprise.Model/config/*.config.json

        Args:
            directory (str): Directory to load from

        Returns:
            list of dict: configurations

        """
        self.ioc.getLogger().trace("Loading Configurations from directory [{0}]".format(directory), trace=True)
        intermediate = list()
        matches = []
        for root, dirnames, filenames in os.walk(directory):
            for filename in fnmatch.filter(filenames, '*.config.json'):
                matches.append(os.path.join(root, filename))
        result = matches
        for doc in result:
            with open(doc) as current_file:
                content = current_file.read().replace('\r\n', '')
            try:
                intermediate.append(json.loads(content))
            except ValueError:
                continue
        self.ioc.getLogger().trace("total documents returned from fs [{0}]".format(len(intermediate)), trace=True)
        return intermediate

    def load_from_mongo(self):
        """Returns all active configurations from the mongo collection Configuration

        Returns:
            list of dict: Configurations

        """
        self.ioc.getLogger().trace("Loading Configurations from mongo", trace=True)
        mConf = []
        for conf in self.ioc.getCollection('Configuration').find({
            'active': True,
            'type': 'prototype_config'
        }):
            mConf.append(dict(conf))
        self.ioc.getLogger().trace("total documents returned from mongo [{0}]".format(len(mConf)), trace=True)
        return mConf

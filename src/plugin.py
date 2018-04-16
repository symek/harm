
class PluginType(object):
    """ Enumeration for plugin types.
        Nothing fancy atm (placeholder).
    """
    class LeftTab(type):
        pass
    class RightTab(type):
        pass


class PluginRegister(type):
    """
    A plugin mount point derived from:
        http://martyalchin.com/2008/jan/10/simple-plugin-framework/
    Acts as a metaclass which creates anything inheriting from Plugin
    # see http://stackoverflow.com/questions/14510286/plugin-architecture-\
    # plugin-manager-vs-inspecting-from-plugins-import
    """

    def __init__(self, name, bases, attrs):
        """Called when a Plugin derived class is imported"""

        if not hasattr(self, '_plugins_store'):
            # Called when the metaclass is first instantiated
            self._plugins_store = []
        else:
            # Called when a plugin class is imported
            self.register_plugin(self)

    def register_plugin(self, plugin):
        """Add the plugin to the plugin list and perform any registration logic"""
        instance = plugin()
        if instance.register_signals():
            self._plugins_store += [instance]


class PluginManager(object):
    """A plugin which must provide a register_signals() method"""
    __metaclass__ = PluginRegister
    name = "PluginManager"
    type = None
    def __init__(self, *args, **kwargs):
        super(PluginManager, self).__init__()
        self.args   = args
        self.kwargs = kwargs

    @property
    def plugins(self):
        return self._plugins_store

    @property
    def error(self):
        return self.last_error

    # @CachedMethod
    def get_plugin_by_type(self, type):
        """ Getter for plugins of type.

            Params: type -> class(type) present in job.plugin.PluginType.
            Return: List of matchnig plugins 
                    (classes derived from job.plugin.PluginManager) 
        """
        plg = []
        for plugin in self.plugins:
            if plugin.type == type:
                plg += [plugin]
        return plg

    # @CachedMethod
    def get_plugin_by_name(self, name):
        """ Getter for plugin by name. Currently first matching name
         is returned, which might not be the best policy ever...

        Params: string prepresenting plugin class.
        Return: First matching plugin. 
        """
        for plugin in self.plugins:
            if plugin.name == name:
                return plugin
        raise OSError

    # @CachedMethod
    def get_first_maching_plugin(self, prefered_plugin_names):
        """ Select first matching plugin from provided list of names.

        Params: List with prefered plugins names.
        Return: First matching plugin. 
        """
        from collections import Iterable
        assert isinstance(prefered_plugin_names, Iterable)
        installed_plg_names = [plugin.name for plugin in self.plugins]
        for plugin_name in prefered_plugin_names:
            if plugin_name in installed_plg_names:
                plugin_instance = self.get_plugin_by_name(plugin_name)
                # FIXME: this is workaround...
                plugin_instance.logger  = LoggerFactory().get_logger(plugin_name,\
                    level=self.log_level)
                return plugin_instance
        return None


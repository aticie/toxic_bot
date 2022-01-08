import configparser


class ConfigSingleton(object):
    """
    Singleton class for Config
    """
    _instance = None

    def __new__(cls):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        return cls._instance


class Config(ConfigSingleton, configparser.ConfigParser):
    """
    Config class
    """
    def __init__(self):
        super().__init__()
        self.config_file = 'config.ini'
        self.read(self.config_file)
    pass

import importlib.metadata

try:
    __version__ = importlib.metadata.version("pycrc")
except:
    __version__ = 'unknown'
__author__ = "Thomas Pircher"

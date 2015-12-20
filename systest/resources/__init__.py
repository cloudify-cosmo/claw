import os
import pkgutil


def get(resource):
    return pkgutil.get_data(__package__, resource)


DIR = os.path.dirname(__file__)

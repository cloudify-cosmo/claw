import pkgutil

def get(resource):
    return pkgutil.get_data(__package__, resource)

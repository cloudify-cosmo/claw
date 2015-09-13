from proxy_tools import proxy
from cloudify.state import CurrentContext


current_conf = CurrentContext()


@proxy
def conf():
    return current_conf.get_ctx()

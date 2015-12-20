import unittest

from systest import conf
from systest import state


class TestState(unittest.TestCase):

    def test(self):
        obj = object()
        state.current_conf.set(obj)
        try:
            self.assertIs(obj, conf._get_current_object())
        finally:
            state.current_conf.clear()

from daboserver.tests import *

class TestWebupdateController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='webupdate', action='index'))
        # Test response...

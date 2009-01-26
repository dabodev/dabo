from daboserver.tests import *

class TestBizobjController(TestController):

    def test_index(self):
        response = self.app.get(url_for(controller='bizobj'))
        # Test response...

from xmlrunner.extra.djangotestrunner import XMLTestRunner
from django.test.runner import DiscoverRunner

class SmartEnergyTestRunner(XMLTestRunner):
    """ A test runner to test without database creation """

    def setup_databases(self, **kwargs):
        return {}

    def teardown_databases(self, old_config, **kwargs):
        return {}

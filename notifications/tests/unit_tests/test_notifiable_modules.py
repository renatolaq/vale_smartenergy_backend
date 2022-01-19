from unittest import mock

from notifications.utils.db import get_db_field_internal_type

mock.patch("django.db.transaction.atomic", lambda func: func).start()

from django.test import SimpleTestCase
from django.db.models.query_utils import Q
from notifications.business.notifiable_modules import Modules
from notifications.business.notifications_business import NotifiableModulesFactory


class TestNotifiableModule(SimpleTestCase):
    def test_notifiable_module_factory_should_return_a_implementation_of_all_modules(
        self,
    ):
        for module in Modules:
            module_implementation = NotifiableModulesFactory.create_notifiable_module(
                module
            )

            self.assertNotEqual(module_implementation, None)

    def test_every_notifiable_module_field_should_be_a_valid_field(self):
        for module in Modules:
            notifiable_module = NotifiableModulesFactory.create_notifiable_module(
                module
            )
            notifiable_module.add_field_options = mock.Mock()
            non_related_fields, related_fields = notifiable_module.get_fields()
            for field in non_related_fields + related_fields:
                get_db_field_internal_type(field["name"], notifiable_module)

    def test_every_notifiable_module_field_should_generate_a_valid_django_orm_expression(
        self,
    ):
        """
        I don't care about values, types or anything .. I'm free human. My code my rules.
        Besides the joke, this test is just about verify the fields returned from
        notifiable modules generates valid django orm expressions.
        """

        for module in Modules:
            notifiable_module = NotifiableModulesFactory.create_notifiable_module(
                module
            )
            notifiable_module.add_field_options = mock.Mock()
            non_related_fields, related_fields = notifiable_module.get_fields()
            for field in non_related_fields + related_fields:
                value = None
                notifiable_module.main_model.objects.filter(Q(**{field["name"]: value}))

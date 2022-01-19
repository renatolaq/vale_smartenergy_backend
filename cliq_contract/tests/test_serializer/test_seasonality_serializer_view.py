from django.test import SimpleTestCase
from ...serializers import SeasonalitySerializerView
from energy_contract.models import EnergyContract
from datetime import date
from unittest import mock


@mock.patch("cliq_contract.serializers.generic_insert_user_and_observation_in_self", mock.Mock(return_value=None))
class TestSeasonalitySerializerView(SimpleTestCase):
    energy_contract = EnergyContract()

    def setUp(self):
        self.energy_contract.start_supply = date(2020, 7, 1)
        self.energy_contract.end_supply = date(2021, 12, 31)

        self.request = mock.MagicMock()
        self.request.META = {}
        self.request.META["HTTP_ACCEPT_LANGUAGE"] = "pt-BR"

    def test_validate_seasonality_different_12pu_parcial_year_supply(self):

        seasonality_serializer_view = SeasonalitySerializerView(data={
            "year": 2020,
            "january": 0,
            "february": 0,
            "march": 1,
            "april": 2,
            "may": 3,
            "june": 0,
            "july": 0,
            "august": 0,
            "september": 0,
            "october": 0,
            "november": 0,
            "december": 0
        },  context={
            "energy_contract": self.energy_contract,
            'request': self.request,
            'observation_log': ""
        })

        self.assertEqual(seasonality_serializer_view.is_valid(), True)

    def test_validate_seasonality_equal_12pu(self):
        seasonality_serializer_view = SeasonalitySerializerView(data={
            "year": 2019,
            "january": 1,
            "february": 0.5,
            "march": 0.5,
            "april": 2,
            "may": 1,
            "june": 1,
            "july": 0,
            "august": 0,
            "september": 3,
            "october": 1,
            "november": 1,
            "december": 1
        },  context={
            "energy_contract": self.energy_contract,
            'request': self.request,
            'observation_log': ""
        })

        self.assertEqual(seasonality_serializer_view.is_valid(), True)

    def test_validate_seasonality_equal_12pu_year_out_of_range(self):
        seasonality_serializer_view = SeasonalitySerializerView(data={
            "year": 2019,
            "january": 1,
            "february": 0.5,
            "march": 0.5,
            "april": 2,
            "may": 1,
            "june": 1,
            "july": 0,
            "august": 0,
            "september": 3,
            "october": 1,
            "november": 1,
            "december": 1
        },  context={
            "energy_contract": self.energy_contract,
            'request': self.request,
            'observation_log': ""
        })

        self.assertEqual(seasonality_serializer_view.is_valid(), True)


    def test_validate_seasonality_great_than_12pu_parcial_year_supply(self):

        seasonality_serializer_view = SeasonalitySerializerView(data={
            "year": 2020,
            "january": 0,
            "february": 0,
            "march": 1,
            "april": 2,
            "may": 3,
            "june": 0,
            "july": 0,
            "august": 0,
            "september": 0,
            "october": 0,
            "november": 0,
            "december": 12
        },  context={
            "energy_contract": self.energy_contract,
            'request': self.request,
            'observation_log': ""
        })

        self.assertEqual(seasonality_serializer_view.is_valid(), False)

    def test_validate_seasonality_less_than_12pu(self):
        seasonality_serializer_view = SeasonalitySerializerView(data={
            "year": 2019,
            "january": 0,
            "february": 0.5,
            "march": 0.5,
            "april": 2,
            "may": 1,
            "june": 1,
            "july": 0,
            "august": 0,
            "september": 3,
            "october": 1,
            "november": 1,
            "december": 1
        },  context={
            "energy_contract": self.energy_contract,
            'request': self.request,
            'observation_log': ""
        })

        self.assertEqual(seasonality_serializer_view.is_valid(), False)

    def test_validate_seasonality_less_than_12pu_year_out_of_range(self):
        seasonality_serializer_view = SeasonalitySerializerView(data={
            "year": 2019,
            "january": 0,
            "february": 0.5,
            "march": 0.5,
            "april": 2,
            "may": 1,
            "june": 1,
            "july": 0,
            "august": 0,
            "september": 3,
            "october": 1,
            "november": 1,
            "december": 1
        },  context={
            "energy_contract": self.energy_contract,
            'request': self.request,
            'observation_log': ""
        })

        self.assertEqual(seasonality_serializer_view.is_valid(), False)

from django.http import HttpRequest
from django.contrib.auth.models import User

from datetime import date

from gauge_point.models import GaugePoint, GaugeEnergyDealership
from usage_contract.models import UsageContract
from company.models import Company
from usage_contract.models import (
    UploadFileUsageContract,
    RatePostException,
    TaxModality,
    ContractCycles,
    Cct,
    EnergyDistributor,
    RatedVoltage,
)
from core.models import Log
from django.db.models import QuerySet

from collections import OrderedDict

# Custom mock classes
class HttpRequestMock(HttpRequest):
    def __init__(self, query_params):
        self.query_params = query_params
        self.META = {"HTTP_ACCEPT_LANGUAGE": "pt-br"}
        self.user = MockRequestUser()
        self.auth = {"cn": "cn", "UserFullName": "User Example"}
        self.kwargs = {}


class MockRequestUser(User):
    is_authenticated = True
    username = "Admin"


class MockSerializer:
    def __init__(self, data):
        self.data = data


class MockFile:
    path = "some/path/here"
    name = "file"

    def __init__(self):
        self.dict = {}

    def copy(self):
        return self.dict


class DateMock:
    def __init__(self, value):
        self.value = value

    def today(self, *args, **kwargs):
        return self.value


class QuerysetMock(QuerySet):
    def __init__(self, value, values_list=None):
        self.value = value
        self.query = self
        self.values_list_value = values_list

    def order_by(self, *args, **kwargs):
        return self.value

    def values_list(self, *args, **kwargs):
        if self.values_list_value:
            return self.values_list_value
        return self.value

    def update(self, *args, **kwargs):
        return self.value

    def can_filter(self, *args, **kwargs):
        return self

    def delete(self, *args, **kwargs):
        return self

    def __iter__(self):
        return iter(["a", "b", "c"])

    def __getitem__(self, key):
        return self.value[key]

    def __setitem__(self, key):
        return getattr(self, key)

    def __delitem__(self, key):
        return getattr(self, key)

    def __str__(self):
        return str(self.value)


class MockData:
    def __init__(self):
        pass

    def getlist(self, *args, **kwargs):
        return ["file", "path"]

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key):
        return getattr(self, key)

    def __delitem__(self, key):
        return getattr(self, key)

    def update(self, *args, **kwargs):
        return None


def check_module_mock(module, permissions):
    def decorator(drf_custom_method):
        def _decorator(self, *args, **kwargs):
            return drf_custom_method(self, *args, **kwargs)

        return _decorator

    return decorator


# Mocked data
usage_contract_mock = UsageContract(1)
usage_contract_mock.status = "N"
usage_contract_mock.company = Company(1)
usage_contract_mock.energy_dealer = Company(1)
usage_contract_mock.rated_voltage = RatedVoltage(1)

usage_contract_queryset_mock = QuerysetMock([usage_contract_mock])

usage_contract_enabled_mock = UsageContract(1)
usage_contract_enabled_mock.status = "S"
usage_contract_enabled_mock.end_date = date(2020, 2, 2)
usage_contract_enabled_mock.energy_dealer = Company(1)

gauge_points = [GaugePoint(1)]
gauge_points[0].status = "S"

gauge_dealers = [GaugeEnergyDealership(1), GaugeEnergyDealership(2)]

gauge_dealers[0].id_dealership = Company(1)

serializer_data_mock = MockSerializer(
    [
        {"usage_contract_type": {"description": "DISTRIBU"}},
        {"usage_contract_type": {"description": "other"}},
    ]
)

upload_file_usage_contract = [UploadFileUsageContract(1)]
upload_file_usage_contract[0].file_path = MockFile()

upload_file_usage_contract_incomplete = [UploadFileUsageContract(1)]

order_by_possibilities = [
    "company_name",
    "company_cnpj",
    "company_state",
    "company_city",
    "energy_dealer",
    "agent_cnpj",
    "group",
    "subgroup",
]

logs_mock = [Log()]
logs_mock[0].new_value = "'status': 'S'"


logs_filter_mock = QuerysetMock(logs_mock)

source_pme_mock = QuerysetMock([])

rpe_list_mock = [RatePostException(1)]
rate_post_exception_list_mock = [
    RatePostException(1),
    RatePostException(2),
    RatePostException(3),
]
rate_post_exception_list_dict_mock = [
    RatePostException(1).__dict__,
    RatePostException(2).__dict__,
    RatePostException(3).__dict__,
]
rate_post_exception_list_dict_2_mock = [
    RatePostException(1).__dict__,
    RatePostException(2).__dict__,
    RatePostException(3).__dict__,
    RatePostException(4).__dict__,
    RatePostException(5).__dict__,
]

tax_list_mock = [TaxModality(1)]
tax_list_2_mock = [TaxModality(1), TaxModality(2), TaxModality(3)]

tax_list_dict_mock = [tax_list_mock[0].__dict__]
tax_list_dict_2_mock = [
    TaxModality(1).__dict__,
    TaxModality(2).__dict__,
    TaxModality(3).__dict__,
]

cc_list_mock = [ContractCycles(1)]
cc_list_2_mock = [ContractCycles(1), ContractCycles(2), ContractCycles(3)]
cc_list_dict_2_mock = [
    ContractCycles(1).__dict__,
    ContractCycles(2).__dict__,
    ContractCycles(3).__dict__,
]

cct_list_mock = [Cct(1)]
cct_list_2_mock = [Cct(1), Cct(2), Cct(3)]
cct_list_dict_mock = [Cct(1).__dict__]
cct_list_dict_2_mock = [Cct(1).__dict__, Cct(2).__dict__, Cct(3).__dict__]

energy_distributor_mock = EnergyDistributor(1)

usage_contract_export_dict = [
    OrderedDict(
        [
            ("id_usage_contract", 3),
            (
                "usage_contract_type",
                OrderedDict(
                    [("id_usage_contract_type", 2), ("description", "Transmissão")]
                ),
            ),
            (
                "companys",
                OrderedDict(
                    [
                        ("id_company", 10147),
                        ("company_name", "Itabira 2"),
                        ("state_number", "33.592.510/0164-09"),
                        (
                            "id_address",
                            OrderedDict(
                                [
                                    (
                                        "url",
                                        "http://localhost:8080/core-api/address/10147/",
                                    ),
                                    ("id_address", 10147),
                                    (
                                        "id_city",
                                        OrderedDict(
                                            [
                                                (
                                                    "id_state",
                                                    OrderedDict(
                                                        [
                                                            ("name", "Minas Gerais"),
                                                            ("initials", "MG"),
                                                        ]
                                                    ),
                                                ),
                                                ("city_name", "Itabira"),
                                            ]
                                        ),
                                    ),
                                    ("street", "Serra do Esmeril"),
                                    ("number", None),
                                    ("zip_code", "35901-190"),
                                    ("complement", ""),
                                    ("neighborhood", ""),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
            (
                "energy_dealers",
                OrderedDict(
                    [
                        ("id_company", 10098),
                        ("company_name", "Cemig Geração e Transmissão S.A"),
                        ("state_number", "06.981.176/0001-58"),
                        (
                            "id_address",
                            OrderedDict(
                                [
                                    (
                                        "url",
                                        "http://localhost:8080/core-api/address/10098/",
                                    ),
                                    ("id_address", 10098),
                                    (
                                        "id_city",
                                        OrderedDict(
                                            [
                                                (
                                                    "id_state",
                                                    OrderedDict(
                                                        [
                                                            ("name", "Minas Gerais"),
                                                            ("initials", "MG"),
                                                        ]
                                                    ),
                                                ),
                                                ("city_name", "Belo Horizonte"),
                                            ]
                                        ),
                                    ),
                                    ("street", "Av. Barbacena"),
                                    ("number", "1200"),
                                    ("zip_code", "30190-131"),
                                    ("complement", "12º Andar"),
                                    ("neighborhood", ""),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
            ("contract_number", "0592002"),
            (
                "rated_voltage",
                OrderedDict(
                    [
                        ("id_rated_voltage", 5),
                        ("voltages", "230.00"),
                        ("group", "A"),
                        ("subgroup", "A1"),
                    ]
                ),
            ),
            ("bought_voltage", "230.00"),
            ("tolerance_range", "5.00"),
            ("power_factor", "95.00"),
            ("peak_begin_time", "17:00:00"),
            ("peak_end_time", "20:00:00"),
            ("contract_value", "10962000.00"),
            ("rate_post_exception", []),
            ("energy_distributor", None),
            (
                "energy_transmitter",
                OrderedDict(
                    [
                        ("ons_code", "MGITAB230"),
                        ("aneel_resolution", ""),
                        ("aneel_publication", None),
                        (
                            "cct",
                            [
                                OrderedDict(
                                    [
                                        ("id_cct", 1),
                                        ("cct_number", "12003"),
                                        ("length", None),
                                        ("destination", "SE Itabira 2"),
                                        ("begin_date", "2019-07-04"),
                                        ("end_date", "2023-12-31"),
                                        ("contract_value", "523767.84"),
                                    ]
                                )
                            ],
                        ),
                        (
                            "contract_cycles",
                            [
                                OrderedDict(
                                    [
                                        ("id_contract_cycles", 1),
                                        ("begin_date", "2020-01-01"),
                                        ("end_date", "2020-06-30"),
                                        ("peak_must", "114.00"),
                                        ("peak_tax", "1.00"),
                                        ("off_peak_must", "117.00"),
                                        ("off_peak_tax", "1.00"),
                                    ]
                                ),
                                OrderedDict(
                                    [
                                        ("id_contract_cycles", 2),
                                        ("begin_date", "2020-07-01"),
                                        ("end_date", "2020-12-31"),
                                        ("peak_must", "114.00"),
                                        ("peak_tax", "1.00"),
                                        ("off_peak_must", "114.00"),
                                        ("off_peak_tax", "1.00"),
                                    ]
                                ),
                                OrderedDict(
                                    [
                                        ("id_contract_cycles", 3),
                                        ("begin_date", "2021-01-01"),
                                        ("end_date", "2023-12-31"),
                                        ("peak_must", "114.00"),
                                        ("peak_tax", "1.00"),
                                        ("off_peak_must", "114.00"),
                                        ("off_peak_tax", "1.00"),
                                    ]
                                ),
                            ],
                        ),
                        ("renovation_period", None),
                        ("audit_renovation", None),
                    ]
                ),
            ),
            ("start_date", "2020-01-01"),
            ("end_date", "2023-12-31"),
            ("observation", ""),
            ("create_date", "2020-06-07T22:39:03.223000Z"),
            ("status", "S"),
            ("upload_file", []),
            ("connection_point", "SE ITABIRA II"),
        ]
    ),
    OrderedDict(
        [
            ("id_usage_contract", 4),
            (
                "usage_contract_type",
                OrderedDict(
                    [("id_usage_contract_type", 2), ("description", "Transmissão")]
                ),
            ),
            (
                "companys",
                OrderedDict(
                    [
                        ("id_company", 10192),
                        ("company_name", "Itabira 4"),
                        ("state_number", "33.592.510/0164-09"),
                        (
                            "id_address",
                            OrderedDict(
                                [
                                    (
                                        "url",
                                        "http://localhost:8080/core-api/address/10192/",
                                    ),
                                    ("id_address", 10192),
                                    (
                                        "id_city",
                                        OrderedDict(
                                            [
                                                (
                                                    "id_state",
                                                    OrderedDict(
                                                        [
                                                            ("name", "Minas Gerais"),
                                                            ("initials", "MG"),
                                                        ]
                                                    ),
                                                ),
                                                ("city_name", "Itabira"),
                                            ]
                                        ),
                                    ),
                                    ("street", "Serra do Esmeril"),
                                    ("number", None),
                                    ("zip_code", "35900-900"),
                                    ("complement", ""),
                                    ("neighborhood", "Zona Rural"),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
            (
                "energy_dealers",
                OrderedDict(
                    [
                        ("id_company", 10098),
                        ("company_name", "Cemig Geração e Transmissão S.A"),
                        ("state_number", "06.981.176/0001-58"),
                        (
                            "id_address",
                            OrderedDict(
                                [
                                    (
                                        "url",
                                        "http://localhost:8080/core-api/address/10098/",
                                    ),
                                    ("id_address", 10098),
                                    (
                                        "id_city",
                                        OrderedDict(
                                            [
                                                (
                                                    "id_state",
                                                    OrderedDict(
                                                        [
                                                            ("name", "Minas Gerais"),
                                                            ("initials", "MG"),
                                                        ]
                                                    ),
                                                ),
                                                ("city_name", "Belo Horizonte"),
                                            ]
                                        ),
                                    ),
                                    ("street", "Av. Barbacena"),
                                    ("number", "1200"),
                                    ("zip_code", "30190-131"),
                                    ("complement", "12º Andar"),
                                    ("neighborhood", ""),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
            ("contract_number", "1112012"),
            (
                "rated_voltage",
                OrderedDict(
                    [
                        ("id_rated_voltage", 5),
                        ("voltages", "230.00"),
                        ("group", "A"),
                        ("subgroup", "A1"),
                    ]
                ),
            ),
            ("bought_voltage", "230.00"),
            ("tolerance_range", "5.00"),
            ("power_factor", "95.00"),
            ("peak_begin_time", "17:00:00"),
            ("peak_end_time", "20:00:00"),
            ("contract_value", "8954400.00"),
            ("rate_post_exception", []),
            ("energy_distributor", None),
            (
                "energy_transmitter",
                OrderedDict(
                    [
                        ("ons_code", "MGITAB4-230-A"),
                        ("aneel_resolution", ""),
                        ("aneel_publication", None),
                        (
                            "cct",
                            [
                                OrderedDict(
                                    [
                                        ("id_cct", 2),
                                        ("cct_number", "1662012"),
                                        ("length", None),
                                        ("destination", "SE Itabira 4"),
                                        ("begin_date", "2012-12-18"),
                                        ("end_date", "2023-12-31"),
                                        ("contract_value", "306720.00"),
                                    ]
                                )
                            ],
                        ),
                        (
                            "contract_cycles",
                            [
                                OrderedDict(
                                    [
                                        ("id_contract_cycles", 4),
                                        ("begin_date", "2020-01-01"),
                                        ("end_date", "2021-12-31"),
                                        ("peak_must", "94.00"),
                                        ("peak_tax", "1.00"),
                                        ("off_peak_must", "94.00"),
                                        ("off_peak_tax", "1.00"),
                                    ]
                                ),
                                OrderedDict(
                                    [
                                        ("id_contract_cycles", 5),
                                        ("begin_date", "2022-01-01"),
                                        ("end_date", "2022-12-31"),
                                        ("peak_must", "91.20"),
                                        ("peak_tax", "1.00"),
                                        ("off_peak_must", "94.00"),
                                        ("off_peak_tax", "1.00"),
                                    ]
                                ),
                                OrderedDict(
                                    [
                                        ("id_contract_cycles", 6),
                                        ("begin_date", "2023-01-01"),
                                        ("end_date", "2023-12-31"),
                                        ("peak_must", "94.00"),
                                        ("peak_tax", "1.00"),
                                        ("off_peak_must", "91.00"),
                                        ("off_peak_tax", "1.00"),
                                    ]
                                ),
                            ],
                        ),
                        ("renovation_period", None),
                        ("audit_renovation", None),
                    ]
                ),
            ),
            ("start_date", "2020-01-01"),
            ("end_date", "2023-12-31"),
            ("observation", ""),
            ("create_date", "2020-06-07T22:44:46.910000Z"),
            ("status", "S"),
            ("upload_file", []),
            ("connection_point", "SE ITABIRA IV"),
        ]
    ),
    OrderedDict(
        [
            ("id_usage_contract", 5),
            (
                "usage_contract_type",
                OrderedDict(
                    [("id_usage_contract_type", 2), ("description", "Transmissão")]
                ),
            ),
            (
                "companys",
                OrderedDict(
                    [
                        ("id_company", 10135),
                        ("company_name", "Água Limpa"),
                        ("state_number", "33.592.510/0413-49"),
                        (
                            "id_address",
                            OrderedDict(
                                [
                                    (
                                        "url",
                                        "http://localhost:8080/core-api/address/10135/",
                                    ),
                                    ("id_address", 10135),
                                    (
                                        "id_city",
                                        OrderedDict(
                                            [
                                                (
                                                    "id_state",
                                                    OrderedDict(
                                                        [
                                                            ("name", "Minas Gerais"),
                                                            ("initials", "MG"),
                                                        ]
                                                    ),
                                                ),
                                                ("city_name", "Rio Piracicaba"),
                                            ]
                                        ),
                                    ),
                                    ("street", "Av. Gustavo Peffer"),
                                    ("number", None),
                                    ("zip_code", "35940-000"),
                                    ("complement", ""),
                                    ("neighborhood", ""),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
            (
                "energy_dealers",
                OrderedDict(
                    [
                        ("id_company", 10098),
                        ("company_name", "Cemig Geração e Transmissão S.A"),
                        ("state_number", "06.981.176/0001-58"),
                        (
                            "id_address",
                            OrderedDict(
                                [
                                    (
                                        "url",
                                        "http://localhost:8080/core-api/address/10098/",
                                    ),
                                    ("id_address", 10098),
                                    (
                                        "id_city",
                                        OrderedDict(
                                            [
                                                (
                                                    "id_state",
                                                    OrderedDict(
                                                        [
                                                            ("name", "Minas Gerais"),
                                                            ("initials", "MG"),
                                                        ]
                                                    ),
                                                ),
                                                ("city_name", "Belo Horizonte"),
                                            ]
                                        ),
                                    ),
                                    ("street", "Av. Barbacena"),
                                    ("number", "1200"),
                                    ("zip_code", "30190-131"),
                                    ("complement", "12º Andar"),
                                    ("neighborhood", ""),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
            ("contract_number", "0212005"),
            (
                "rated_voltage",
                OrderedDict(
                    [
                        ("id_rated_voltage", 5),
                        ("voltages", "230.00"),
                        ("group", "A"),
                        ("subgroup", "A1"),
                    ]
                ),
            ),
            ("bought_voltage", "230.00"),
            ("tolerance_range", "5.00"),
            ("power_factor", "95.00"),
            ("peak_begin_time", "17:00:00"),
            ("peak_end_time", "20:00:00"),
            ("contract_value", "816960.00"),
            ("rate_post_exception", []),
            ("energy_distributor", None),
            (
                "energy_transmitter",
                OrderedDict(
                    [
                        ("ons_code", "MGMONL230"),
                        ("aneel_resolution", ""),
                        ("aneel_publication", None),
                        (
                            "cct",
                            [
                                OrderedDict(
                                    [
                                        ("id_cct", 3),
                                        ("cct_number", None),
                                        ("length", None),
                                        ("destination", None),
                                        ("begin_date", "2020-01-01"),
                                        ("end_date", "2023-12-31"),
                                        ("contract_value", "1.00"),
                                    ]
                                )
                            ],
                        ),
                        (
                            "contract_cycles",
                            [
                                OrderedDict(
                                    [
                                        ("id_contract_cycles", 7),
                                        ("begin_date", "2020-01-01"),
                                        ("end_date", "2023-12-31"),
                                        ("peak_must", "8.40"),
                                        ("peak_tax", "1.00"),
                                        ("off_peak_must", "8.62"),
                                        ("off_peak_tax", "1.00"),
                                    ]
                                )
                            ],
                        ),
                        ("renovation_period", None),
                        ("audit_renovation", None),
                    ]
                ),
            ),
            ("start_date", "2020-01-01"),
            ("end_date", "2023-12-31"),
            ("observation", ""),
            ("create_date", "2020-06-07T22:46:53.167000Z"),
            ("status", "S"),
            ("upload_file", []),
            ("connection_point", "SE Joao Molevade II"),
        ]
    ),
    OrderedDict(
        [
            ("id_usage_contract", 6),
            (
                "usage_contract_type",
                OrderedDict(
                    [("id_usage_contract_type", 2), ("description", "Transmissão")]
                ),
            ),
            (
                "companys",
                OrderedDict(
                    [
                        ("id_company", 10137),
                        ("company_name", "Brucutu"),
                        ("state_number", "33.592.510/0447-98"),
                        (
                            "id_address",
                            OrderedDict(
                                [
                                    (
                                        "url",
                                        "http://localhost:8080/core-api/address/10137/",
                                    ),
                                    ("id_address", 10137),
                                    (
                                        "id_city",
                                        OrderedDict(
                                            [
                                                (
                                                    "id_state",
                                                    OrderedDict(
                                                        [
                                                            ("name", "Minas Gerais"),
                                                            ("initials", "MG"),
                                                        ]
                                                    ),
                                                ),
                                                (
                                                    "city_name",
                                                    "São Gonçalo do Rio Abaixo",
                                                ),
                                            ]
                                        ),
                                    ),
                                    ("street", "MG-436"),
                                    ("number", None),
                                    ("zip_code", "35935-000"),
                                    ("complement", ""),
                                    ("neighborhood", "Serra do Machado"),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
            (
                "energy_dealers",
                OrderedDict(
                    [
                        ("id_company", 10098),
                        ("company_name", "Cemig Geração e Transmissão S.A"),
                        ("state_number", "06.981.176/0001-58"),
                        (
                            "id_address",
                            OrderedDict(
                                [
                                    (
                                        "url",
                                        "http://localhost:8080/core-api/address/10098/",
                                    ),
                                    ("id_address", 10098),
                                    (
                                        "id_city",
                                        OrderedDict(
                                            [
                                                (
                                                    "id_state",
                                                    OrderedDict(
                                                        [
                                                            ("name", "Minas Gerais"),
                                                            ("initials", "MG"),
                                                        ]
                                                    ),
                                                ),
                                                ("city_name", "Belo Horizonte"),
                                            ]
                                        ),
                                    ),
                                    ("street", "Av. Barbacena"),
                                    ("number", "1200"),
                                    ("zip_code", "30190-131"),
                                    ("complement", "12º Andar"),
                                    ("neighborhood", ""),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
            ("contract_number", "0312004"),
            (
                "rated_voltage",
                OrderedDict(
                    [
                        ("id_rated_voltage", 5),
                        ("voltages", "230.00"),
                        ("group", "A"),
                        ("subgroup", "A1"),
                    ]
                ),
            ),
            ("bought_voltage", "230.00"),
            ("tolerance_range", "5.00"),
            ("power_factor", "95.00"),
            ("peak_begin_time", "17:00:00"),
            ("peak_end_time", "20:00:00"),
            ("contract_value", "7008000.00"),
            ("rate_post_exception", []),
            ("energy_distributor", None),
            (
                "energy_transmitter",
                OrderedDict(
                    [
                        ("ons_code", "MGCVBC230-A"),
                        ("aneel_resolution", ""),
                        ("aneel_publication", None),
                        (
                            "cct",
                            [
                                OrderedDict(
                                    [
                                        ("id_cct", 4),
                                        ("cct_number", "372007"),
                                        ("length", None),
                                        ("destination", "SE Barão de Cocais 3"),
                                        ("begin_date", "2005-12-12"),
                                        ("end_date", "2023-12-31"),
                                        ("contract_value", "311280.00"),
                                    ]
                                )
                            ],
                        ),
                        (
                            "contract_cycles",
                            [
                                OrderedDict(
                                    [
                                        ("id_contract_cycles", 8),
                                        ("begin_date", "2020-01-01"),
                                        ("end_date", "2023-12-31"),
                                        ("peak_must", "73.00"),
                                        ("peak_tax", "1.00"),
                                        ("off_peak_must", "73.00"),
                                        ("off_peak_tax", "1.00"),
                                    ]
                                )
                            ],
                        ),
                        ("renovation_period", None),
                        ("audit_renovation", None),
                    ]
                ),
            ),
            ("start_date", "2020-01-01"),
            ("end_date", "2023-12-31"),
            ("observation", ""),
            ("create_date", "2020-06-07T22:49:05.180000Z"),
            ("status", "S"),
            ("upload_file", []),
            ("connection_point", "SE Barão de Cocais 3"),
        ]
    ),
    OrderedDict(
        [
            ("id_usage_contract", 7),
            (
                "usage_contract_type",
                OrderedDict(
                    [("id_usage_contract_type", 2), ("description", "Transmissão")]
                ),
            ),
            (
                "companys",
                OrderedDict(
                    [
                        ("id_company", 10150),
                        ("company_name", "Nova Lima 6 SE"),
                        ("state_number", "33.592.510/0034-12"),
                        (
                            "id_address",
                            OrderedDict(
                                [
                                    (
                                        "url",
                                        "http://localhost:8080/core-api/address/10150/",
                                    ),
                                    ("id_address", 10150),
                                    (
                                        "id_city",
                                        OrderedDict(
                                            [
                                                (
                                                    "id_state",
                                                    OrderedDict(
                                                        [
                                                            ("name", "Minas Gerais"),
                                                            ("initials", "MG"),
                                                        ]
                                                    ),
                                                ),
                                                ("city_name", "Nova Lima"),
                                            ]
                                        ),
                                    ),
                                    ("street", "Fazenda Rio de Peixe"),
                                    ("number", None),
                                    ("zip_code", "34000-000"),
                                    ("complement", ""),
                                    ("neighborhood", "Zona rural"),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
            (
                "energy_dealers",
                OrderedDict(
                    [
                        ("id_company", 10098),
                        ("company_name", "Cemig Geração e Transmissão S.A"),
                        ("state_number", "06.981.176/0001-58"),
                        (
                            "id_address",
                            OrderedDict(
                                [
                                    (
                                        "url",
                                        "http://localhost:8080/core-api/address/10098/",
                                    ),
                                    ("id_address", 10098),
                                    (
                                        "id_city",
                                        OrderedDict(
                                            [
                                                (
                                                    "id_state",
                                                    OrderedDict(
                                                        [
                                                            ("name", "Minas Gerais"),
                                                            ("initials", "MG"),
                                                        ]
                                                    ),
                                                ),
                                                ("city_name", "Belo Horizonte"),
                                            ]
                                        ),
                                    ),
                                    ("street", "Av. Barbacena"),
                                    ("number", "1200"),
                                    ("zip_code", "30190-131"),
                                    ("complement", "12º Andar"),
                                    ("neighborhood", ""),
                                ]
                            ),
                        ),
                    ]
                ),
            ),
            ("contract_number", "1002013"),
            (
                "rated_voltage",
                OrderedDict(
                    [
                        ("id_rated_voltage", 6),
                        ("voltages", "345.00"),
                        ("group", "A"),
                        ("subgroup", "A1"),
                    ]
                ),
            ),
            ("bought_voltage", "345.00"),
            ("tolerance_range", "5.00"),
            ("power_factor", "95.00"),
            ("peak_begin_time", "17:00:00"),
            ("peak_end_time", "20:00:00"),
            ("contract_value", "17904000.00"),
            ("rate_post_exception", []),
            ("energy_distributor", None),
            (
                "energy_transmitter",
                OrderedDict(
                    [
                        ("ons_code", "MGCVBC230-A"),
                        ("aneel_resolution", ""),
                        ("aneel_publication", None),
                        (
                            "cct",
                            [
                                OrderedDict(
                                    [
                                        ("id_cct", 5),
                                        ("cct_number", "42009"),
                                        ("length", "58.00"),
                                        (
                                            "destination",
                                            "SE Ouro Preto/Taquaril - SE Nova Lima 6",
                                        ),
                                        ("begin_date", "2013-12-30"),
                                        ("end_date", "2023-12-31"),
                                        ("contract_value", "1.00"),
                                    ]
                                )
                            ],
                        ),
                        (
                            "contract_cycles",
                            [
                                OrderedDict(
                                    [
                                        ("id_contract_cycles", 9),
                                        ("begin_date", "2020-01-01"),
                                        ("end_date", "2021-12-31"),
                                        ("peak_must", "226.00"),
                                        ("peak_tax", "1.00"),
                                        ("off_peak_must", "226.00"),
                                        ("off_peak_tax", "1.00"),
                                    ]
                                ),
                                OrderedDict(
                                    [
                                        ("id_contract_cycles", 10),
                                        ("begin_date", "2022-01-01"),
                                        ("end_date", "2023-12-31"),
                                        ("peak_must", "147.00"),
                                        ("peak_tax", "1.00"),
                                        ("off_peak_must", "147.00"),
                                        ("off_peak_tax", "1.00"),
                                    ]
                                ),
                            ],
                        ),
                        ("renovation_period", None),
                        ("audit_renovation", None),
                    ]
                ),
            ),
            ("start_date", "2020-01-01"),
            ("end_date", "2023-12-31"),
            ("observation", ""),
            ("create_date", "2020-06-07T22:54:41.153000Z"),
            ("status", "S"),
            ("upload_file", []),
            ("connection_point", "SE Nova Lima 6"),
        ]
    ),
]

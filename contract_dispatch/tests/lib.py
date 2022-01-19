from contract_dispatch.models import ContractDispatch, CliqContract
from datetime import datetime


class MockQuerySet:
    def __init__(self, values=[]):
        self.raw_values = values
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):  # Python 2: def next(self)
        self._index += 1
        if self._index >= len(self.raw_values):
            raise StopIteration
        return self.raw_values[self._index]

    def __getitem__(self, item):
        return MockQuerySet(self.raw_values)

    def exclude(self, *args, **kwargs):
        return []

    def filter(self, *args, **kwargs):
        return MockQuerySet(self.raw_values)

    def values(self, *args, **kwargs):
        return MockQuerySet(self.raw_values)

    def annotate(self, *args, **kwargs):
        return MockQuerySet(self.raw_values)

    def order_by(self, *args, **kwargs):
        return MockQuerySet(self.raw_values)

    def distinct(self, *args, **kwargs):
        return MockQuerySet(self.raw_values)

    def all(self, *args, **kwargs):
        return MockQuerySet(self.raw_values)

    def query(self, *args, **kwargs):
        return MockQuerySet(self.raw_values)


class MockCliqContract(CliqContract, MockQuerySet):
    def get(self, *args, **kwargs):
        return datetime(2020, 1, 1)


class MockContractDispatch(ContractDispatch, MockQuerySet):
    contracts = MockCliqContract()


mock_query_set = MockQuerySet([])

contract_cliq_list = [MockCliqContract(), MockCliqContract()]

mock_generation_dict = [
    {
        "title": "Contratos enviados em 2020/07",
        "contracts": [
            {
                "values": [
                    "29/07/2020 21:40",
                    "30/07/2020 23:04",
                    "Rutvik Krushnakumar Pensionwar_CONTR",
                    "01/07/2020 00:00",
                    "CCEAL",
                    "1279720",
                    "Curto Prazo",
                    "0,00",
                    "CVE_6,0_VALE_AMERICA_0720",
                    "America",
                    "America",
                    "Vale",
                    "CVRD PIE",
                    "V",
                    "Registrado e Não Validado",
                    "Transferência",
                    "Registro",
                ]
            },
            {
                "values": [
                    "29/07/2020 19:10",
                    "30/07/2020 23:03",
                    "Rutvik Krushnakumar Pensionwar_CONTR",
                    "01/07/2020 00:00",
                    "CCEAL",
                    "",
                    "Curto Prazo",
                    "0,00",
                    "CCE_61,0_CASA DOS VENTOS_VALE ENERGIA_0720",
                    "Vale Energia",
                    "Vale Energia",
                    "Casa dos Ventos",
                    "Casa dos Ventos",
                    "C",
                    "Error",
                    "Venda",
                    "Validação de Registro",
                ]
            },
            {
                "values": [
                    "29/07/2020 19:10",
                    "30/07/2020 23:03",
                    "Rutvik Krushnakumar Pensionwar_CONTR",
                    "01/07/2020 00:00",
                    "CCEAL",
                    "",
                    "Curto Prazo",
                    "0,00",
                    "CVE_2,0_VALE ENERGIA_ARGON_0720",
                    "Argon",
                    "Argon",
                    "Vale Energia",
                    "Vale Energia",
                    "V",
                    "Error",
                    "Transferência",
                    "Registro",
                ]
            },
            {
                "values": [
                    "29/07/2020 19:10",
                    "30/07/2020 23:03",
                    "Rutvik Krushnakumar Pensionwar_CONTR",
                    "01/07/2020 00:00",
                    "CCEAL",
                    "",
                    "Curto Prazo",
                    "0,00",
                    "CVE_61,0_VALE ENERGIA_CASA DOS VENTOS_0720",
                    "Casa dos Ventos",
                    "Casa dos Ventos",
                    "Vale Energia",
                    "Vale Energia",
                    "V",
                    "Error",
                    "Transferência",
                    "Registro",
                ]
            },
            {
                "values": [
                    "29/07/2020 19:10",
                    "30/07/2020 23:03",
                    "Rutvik Krushnakumar Pensionwar_CONTR",
                    "01/07/2020 00:00",
                    "CCEAL",
                    "1279717",
                    "Curto Prazo",
                    "0,00",
                    "CVE_5,0_VALE ENERGIA_DEAL COMERCIALIZADORA_0720",
                    "Deal Comercializadora",
                    "Deal Comercializadora",
                    "Vale Energia",
                    "Vale Energia",
                    "V",
                    "Registrado e Não Validado",
                    "Transferência",
                    "Registro",
                ]
            },
        ],
        "fields": [
            {
                "value": "contract_dispatches__contract_dispatch__dispatch_date",
                "name": "Data de envio",
            },
            {
                "value": "contract_dispatches__contract_dispatch__last_status_update_date",
                "name": "Data da última atualização",
            },
            {
                "value": "contract_dispatches__contract_dispatch__dispatch_username",
                "name": "Usuário",
            },
            {
                "value": "contract_dispatches__contract_dispatch__supply_date",
                "name": "Data de suprimento",
            },
            {"value": "ccee_type_contract", "name": "Tipo de contrato CCEE"},
            {"value": "id_ccee__code_ccee", "name": "Código Cliq"},
            {"value": "id_contract__modality", "name": "Modalidade"},
            {"value": "contract_dispatches__volume_on_dispatch", "name": "Volume"},
            {"value": "id_contract__contract_name", "name": "Nome"},
            {
                "value": "id_contract__id_buyer_agents__vale_name_agent",
                "name": "Agente Comprador",
            },
            {"value": "id_buyer_profile__name_profile", "name": "Perfil Comprador"},
            {
                "value": "id_contract__id_seller_agents__vale_name_agent",
                "name": "Agente Vendedor",
            },
            {"value": "id_vendor_profile__name_profile", "name": "Perfil Vendedor"},
            {"value": "id_contract__type", "name": "Tipo de contrato"},
            {"value": "status_val", "name": "Status"},
            {"value": "category", "name": "Categoria"},
            {"value": "operation", "name": "Operação"},
        ],
    }
]


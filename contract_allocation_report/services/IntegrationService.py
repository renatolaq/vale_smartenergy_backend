from datetime import date

from balance_report_market_settlement.models import Report, DetailedBalance, PriorizedCliq
from global_variables.models import GlobalVariable
from company.models import Company
from cliq_contract.models import CliqContract
from agents.models import Agents
from ..ErrorWithCode import ErrorWithCode
from django.db.models import Q
from company.models import State


class IntegrationService:
    def get_balance_data(self, balance_id: int) -> dict:
        report: Report = Report.objects.filter(id=balance_id).first()
        if not report:
            return None
        agents_of_1001 = list(Agents.objects.filter(id_company__id_sap=1001).values_list('vale_name_agent', flat=True))

        def decode_consumer(detail: DetailedBalance):
            company: Company = Company.objects.get(company_name=detail.unity)
            if company.type == 'F' and company.characteristics == 'consumidora':
                return {
                    "unit_id": company.id_company,
                    "unit_name": company.company_name,
                    "state_id": company.id_address.id_city.id_state.id_state,
                    "state_name": company.id_address.id_city.id_state.name,
                    "volume": float(detail.volume)
                }
            return None

        consumers = list(map(decode_consumer,
                             DetailedBalance.objects.filter(
                                 id_detailed_balance_type__description="CONSUMPTION",
                                 id_balance__id_report=report,
                                 volume__gt=0)))

        consumers = list(filter(lambda c: c is not None, consumers))

        def decode_contract_provider(detail: DetailedBalance):
            report_cliq = PriorizedCliq.objects.get(id=detail.id_contract_cliq)
            
            cliq_contract = None
            if report_cliq.contract_cliq:
                cliq_contract = CliqContract.objects.get(
                    id_ccee__code_ccee=report_cliq.contract_cliq)
            else:
                try:
                    cliq_contract = CliqContract.objects.get(
                        id_contract__contract_name=report_cliq.contract_name)
                except:                    
                    raise ErrorWithCode.from_error("IMPOSSIBLE_DETERMINE_CLIQCONTRACT", f"Impossible to determine Cliq Contract Energy Contract '{report_cliq.contract_name}'")
            return {
                "type": "contract",
                "unit_id": cliq_contract.id_vendor_profile.id_agents.id_company.id_company,
                "state_id": cliq_contract.id_vendor_profile.id_agents.id_company.id_address.id_city.id_state.id_state,
                "state_name": cliq_contract.id_vendor_profile.id_agents.id_company.id_address.id_city.id_state.name,
                "contract_id": cliq_contract.id_contract_cliq,
                "available_power": float(detail.volume),
                "cost": float(detail.fare or 0.0),
                "provider_name": report_cliq.contract_name
            }

        contract_providers = list(map(decode_contract_provider,
                                      DetailedBalance.objects.filter(Q(
                                          id_detailed_balance_type__description="PURCHASE",
                                          id_balance__id_report=report,
                                          id_balance__id_agente__name__in=agents_of_1001,
                                          volume__gt=0), Q(contract_name__startswith='CCE') | Q(contract_name__startswith='CCI'))))

        def decode_generator(detail: DetailedBalance):
            company = Company.objects.get(company_name=detail.unity)
            return {
                "type": "generation",
                "unit_id": company.id_company,
                "state_id": company.id_address.id_city.id_state.id_state,
                "state_name": company.id_address.id_city.id_state.name,
                "available_power": float(detail.volume),
                "cost": float(detail.fare or 0.0),
                "provider_name": company.company_name
            }

        generators = list(map(decode_generator,
                              DetailedBalance.objects.filter(
                                  id_detailed_balance_type__description="GENERATION",
                                  id_balance__id_report=report,
                                  id_balance__id_agente__name__in=agents_of_1001,
                                  volume__gt=0)))

        return {
            "balance": balance_id,
            "referenceMonth": date(int(report.year), int(report.month), 1),
            "consumers": consumers,
            "contracts": contract_providers,
            "generators": generators
        }

    def get_icms(self) -> dict:
        return dict(map(lambda variable:
                        (
                            variable.state.id, float(variable.value / 100)
                        ),
                        GlobalVariable.objects.filter(status=1, variable=7)))

    def get_state_name(self, state_id):
        state = State.objects.filter(id_state=state_id).first()
        if state:
            return state.name
        return ""        

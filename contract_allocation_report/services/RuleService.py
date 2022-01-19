from datetime import date

from balance_report_market_settlement.models import Report, DetailedBalance, PriorizedCliq
from global_variables.models import GlobalVariable
from company.models import Company
from cliq_contract.models import CliqContract
from agents.models import Agents


class RuleService:
    def prioritize_contracts(self) -> dict:
        pass

    def get_icms_value(self, icms_cost_rules, source_type, source, consumer, balance_data, icms_by_state):
        def filter_direct_source_direct_destination(rule):
            pass
        
        compatible_rules = filter(filter_direct_source_direct_destination ,icms_cost_rules)
        compatible_rules = filter(filter_direct_source_generic_destination ,icms_cost_rules)
        compatible_rules = filter(filter_direct_source_destination ,icms_cost_rules)
        compatible_rules = filter(filter_direct_source_destination ,icms_cost_rules)
        compatible_rules = filter(filter_direct_source_destination ,icms_cost_rules)
        

        for rule in rules['icms_cost_rules']:
            if rule['provider_id'] and not compatible_rule: #regra geral para todos contratos ou gerador
                pass
            if rule['state_id'] and not compatible_rule: #regra geral para todos estados
                pass


            if (rule['state_id'] == consumer['state_id']
                    and ((rule['source_id'] == source['contract_id'] and source_type == rule['source_type'] and source_type == 'contract') or
                         (rule['source_id'] == source['unit_id'] and source_type == rule['source_type']) and source_type == 'generation')
                    and not compatible_rule):
                compatible_rule = rule

            if (rule['unit_id'] == consumer['unit_id']
                    and ((rule['source_id'] == source['contract_id'] and source_type == rule['source_type'] and source_type == 'contract') or
                         (rule['source_id'] == source['unit_id'] and source_type == rule['source_type']) and source_type == 'generation')
                    and not compatible_rule):
                compatible_rule = rule

            if (rule['source_id'] == source['contract_id']
                    and source_type == rule['source_type']):
                compatible_rule = rule

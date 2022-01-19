from copy import deepcopy, copy

from .IntegrationService import IntegrationService
from ..ErrorWithCode import ErrorWithCode


class GenerationService:
    def __init__(self, integration_service: IntegrationService):
        self.__integration_service = integration_service
        self.__icms_by_state = self.__integration_service.get_icms()

    def __get_icms_by_state(self, state_id: int):
        icms = self.__icms_by_state.get(state_id)
        if icms is None:
            raise ErrorWithCode.from_error(
                "ICMS_NOT_FOUND_FOR_STATE",
                f"ICMS not found to state {self.__integration_service.get_state_name(state_id)}",
                "",
                {
                    "state_id": state_id,
                    "state_name": self.__integration_service.get_state_name(state_id)
                })

        return icms

    def generate_allocations_from_balance(self, balance):
        balance_data = self.__integration_service.get_balance_data(
            balance) if not(type(balance) is dict) else balance
        
        all_providers = balance_data["contracts"] + \
            balance_data["generators"]
        consumers = balance_data["consumers"]

        return self.__generate_allocation(all_providers, consumers, balance_data)

    def add_new_contracts_from_balance(self, report, balance):
        balance_data = self.__integration_service.get_balance_data(
            balance) if not(type(balance) is dict) else balance

        providers = balance_data["contracts"] + \
            balance_data["generators"]
        consumers = copy(balance_data["consumers"])

        for consumer in consumers:
            consumer["available_to_consume"] = float(consumer["volume"])

        for source_data in report["sources"]:
            if source_data["type"] == "generation":
                source = self.__get_generator_from_balance(
                    source_data["sourceUnitId"], balance_data)
                if source in providers:
                    providers.remove(source)
            else:
                source = self.__get_contract_from_balance(
                    source_data["sourceContractId"], balance_data)
                if source in providers:
                    providers.remove(source)

            for destination_data in source_data["destinations"]:
                consumer = self.__get_consumer_from_balance(
                    destination_data["unitId"], balance_data)

                consumer["available_to_consume"] -= destination_data["allocatedPower"]
                if(consumer["available_to_consume"] <= 0 and consumer in consumers):
                    consumers.remove(consumer)

        def decode_destination(destination):
            return {
                "destination_id": destination["unitId"],
                "allocation": destination["allocatedPower"],
                "icms_cost": destination["ICMSCost"],
                "icms_cost_not_creditable": destination["ICMSCostNotCreditable"]
            }

        def decode_provider(provider):
            return {
                "type": provider["type"],
                "source_id": provider["sourceContractId"] or provider["sourceUnitId"],
                "available_power": provider["availablePower"],
                "for_sale": provider["availableForSale"],
                "cost": provider["cost"],
                "balance": provider["balance"],
                "allocations": list(map(decode_destination, provider["destinations"]))
            }

        new_allocations = self.__generate_allocation(
            providers, consumers, balance_data)
        old_allocations = list(map(decode_provider, report["sources"]))

        return old_allocations + new_allocations

    # deve retornar apenas o calculo do icms para cada alocação

    def calculate_from_allocations(self, allocations: dict, balance):
        balance_data = self.__integration_service.get_balance_data(
            balance) if not(type(balance) is dict) else balance

        allocations = deepcopy(allocations)

        for source_allocation in allocations:
            source_allocation['available_power'] = self.__get_generator_from_balance(
                source_allocation["source_id"], balance_data)['available_power'] if source_allocation["type"] == "generation" else self.__get_contract_from_balance(
                source_allocation["source_id"], balance_data)['available_power']

            data = source_allocation.get(
                "allocations") or source_allocation.get("destination") or []
            for destination_allocation in data:
                if(source_allocation["balance"] == balance_data["balance"]):
                    destination_allocation["icms_cost"] = destination_allocation["allocation"] * \
                        self.__apply_icms_to_cost(source_allocation["type"], source_allocation["source_id"],
                                                  destination_allocation["destination_id"], balance_data)  # passar regras para calcular
                    # Calcular com regra
                    destination_allocation["icms_cost_not_creditable"] = 0

        return allocations

    # Gerar visualizaçao por estado
    def mount_report_from_allocations(self, allocations: dict, balance):
        balance_data = self.__integration_service.get_balance_data(
            balance) if not(type(balance) is dict) else balance

        total_icms_cost = 0
        total_icms_not_creditable = 0
        allocation_result = []

        for source_allocation in allocations:
            generator = self.__get_generator_from_balance(
                source_allocation["source_id"], balance_data) if source_allocation["type"] == "generation" else None
            contract = self.__get_contract_from_balance(
                source_allocation["source_id"], balance_data) if source_allocation["type"] == "contract" else None

            allocation_data = {
                "sourceContractId": contract["contract_id"] if source_allocation["type"] == "contract" else None,
                "sourceUnitId": generator["unit_id"] if source_allocation["type"] == "generation" else contract["unit_id"],
                "sourceName": generator["provider_name"] if source_allocation["type"] == "generation" else contract["provider_name"],
                "type": source_allocation["type"],
                "availablePower": source_allocation["available_power"],
                "availableForSale": source_allocation["for_sale"],
                "cost": source_allocation["cost"],
                "balance": source_allocation["balance"],
                "destinations": [],
                "destinationStates": None
            }

            allocation_result.append(allocation_data)

            allocation_by_state = dict()

            for destination_allocation in source_allocation["allocations"]:
                consumer = self.__get_consumer_from_balance(
                    destination_allocation["destination_id"], balance_data)

                allocation_data["destinations"].append({
                    "unitId": consumer["unit_id"],
                    "unitName": consumer["unit_name"],
                    "allocatedPower": destination_allocation["allocation"],
                    "ICMSCost": destination_allocation["icms_cost"],
                    "ICMSCostNotCreditable": destination_allocation["icms_cost_not_creditable"]
                })

                state_allocation = allocation_by_state.get(consumer["state_id"], {
                    "stateId": consumer["state_id"],
                    "stateName": consumer["state_name"],
                    "allocatedPower": 0
                })
                state_allocation["allocatedPower"] += destination_allocation["allocation"]
                allocation_by_state[consumer["state_id"]] = state_allocation

            allocation_data["destinationStates"] = list(
                allocation_by_state.values())

        return {
            "ICMSCost": total_icms_cost,
            "ICMSCostNotCreditable": total_icms_not_creditable,
            "sources": allocation_result
        }

    def __apply_icms_to_cost(self, source_type, source_id, destination_id, balance_data):
        def icms_formula(icms_state_value, cost): return \
            (cost / (1 - icms_state_value)) * icms_state_value

        consumer = self.__get_consumer_from_balance(
            destination_id, balance_data)

        if source_type == "generation":
            generator = self.__get_generator_from_balance(
                source_id, balance_data)
            return icms_formula(self.__get_icms_by_state(consumer["state_id"]), generator["cost"])
        else:
            contract = self.__get_contract_from_balance(
                source_id, balance_data)
            return icms_formula(self.__get_icms_by_state(consumer["state_id"]), contract["cost"])

    def __get_consumer_from_balance(self, unit_id, balance_data):
        for consumer in balance_data["consumers"]:
            if consumer["unit_id"] == unit_id:
                return consumer
        return None

    def __get_generator_from_balance(self, unit_id, balance_data):
        for generator in balance_data["generators"]:
            if generator["unit_id"] == unit_id:
                return generator
        return None

    def __get_contract_from_balance(self, contract_id, balance_data):
        for contract in balance_data["contracts"]:
            if contract["contract_id"] == contract_id:
                return contract
        return None

    def __generate_allocation(self, providers, consumers, balance_data):
        providers_consumers_icms_cost = []
        for provider in providers:
            if not provider.get("available_to_allocate"):
                provider["available_to_allocate"] = provider["available_power"]
            for consumer in consumers:
                if not consumer.get("available_to_consume"):
                    consumer["available_to_consume"] = consumer["volume"]
                source_id = provider["contract_id"] if provider["type"] == "contract" else provider["unit_id"]
                providers_consumers_icms_cost.append({
                    "provider": provider,
                    "consumer": consumer,
                    # aplicar regra
                    "icms_cost": self.__apply_icms_to_cost(provider["type"], source_id, consumer["unit_id"], balance_data),
                    "allocated": 0
                })

        providers_consumers_icms_cost.sort(key=lambda x: x["icms_cost"])

        result = dict()

        def make_provider_key(p): return p["type"] + "_" + \
            str(p["unit_id"])+"_" + str(p.get("contract_id", ""))
        for data in providers_consumers_icms_cost:
            if make_provider_key(data["provider"]) not in result:
                result[make_provider_key(data["provider"])] = {
                    "type": data["provider"]["type"],
                    "source_id": data["provider"]["contract_id"] if data["provider"]["type"] == "contract" else data["provider"]["unit_id"],
                    "available_power": data["provider"]["available_power"],
                    "for_sale": data["provider"]["available_power"],
                    "cost": data["provider"]["cost"],
                    "balance": balance_data["balance"],
                    "allocations": []
                }

            if data["provider"]["available_to_allocate"] > 0 and data["consumer"]["available_to_consume"] > 0:
                value = min(data["provider"]["available_to_allocate"],
                            data["consumer"]["available_to_consume"])
                data["provider"]["available_to_allocate"] -= value
                data["consumer"]["available_to_consume"] -= value
                data["allocated"] = value

                data_result = result.get(make_provider_key(data["provider"]))

                data_result["for_sale"] -= value
                data_result["allocations"].append({
                    "destination_id": data["consumer"]["unit_id"],
                    "allocation": value,
                    "icms_cost": None,
                    "icms_cost_not_creditable": None
                })

        return list(result.values())

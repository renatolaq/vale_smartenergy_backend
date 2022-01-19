from datetime import datetime, timezone
from django.db import transaction
from collections import OrderedDict

from SmartEnergy.auth import has_permission, groups, permissions, is_administrator
from SmartEnergy.utils.exception.ErroWithCode import ErrorWithCode

from ..models.CompanyBudgetRevision import CompanyBudgetRevision, CompanyBudgetRevisionState
from ..models.CompanyBudget import CompanyBudget
from ..models.BudgetChangeTrack import BudgetChangeTrack

from ..serializers.CompanyBudgetRevisionSerializer import CompanyBudgetRevisionSerializer
from .SaveBudgetService import SaveBudgetService



class WorkflowBudgetService:
    __valid_empty_fields = [
        "loadFactorConsistencyPeakPower", 
        "loadFactorConsistencyOffPeakPower", 
        "uniqueLoadFactorConsistency", 
        "modulationFactorConsistency", 
        "specificConsumption"]
    def __validate_all_fields(self, data, source):
        ret = []
        if data is None:
            ret.append({
                "code": "EMPTY_FIELD",
                "source": source,
                "message": f"Field is empty, it is not allowed to continue"
            })
        elif issubclass(type(data), OrderedDict) or issubclass(type(data), dict):
            for key in data:
                if key in self.__valid_empty_fields:
                    continue
                ret.extend(self.__validate_all_fields(
                    data[key], f"{source}/{key}"))
        return ret

    def __init__(self, save_budget_service: SaveBudgetService) -> None:
        self.__save_budget_service = save_budget_service

    @transaction.atomic
    def release_to_analysis(self, company_budget: CompanyBudget, user: str, message: str):
        trans_savepoint = transaction.savepoint()
        last_revision: CompanyBudgetRevision = company_budget.companybudgetrevision_set.order_by(
            "-revision")[0]
        if(last_revision.state in (CompanyBudgetRevisionState.budgeting,
                                   CompanyBudgetRevisionState.disapproved)):
            new_revision = self.__save_budget_service.duplicate_revision(last_revision)

            new_revision.state = CompanyBudgetRevisionState.releasedto_analysis
            new_revision.revision += 1
            new_revision.save()

            BudgetChangeTrack.objects.create(
                company_budget=company_budget,
                budget_revision=new_revision.revision,
                comment=message,
                user=user,
                change_at=datetime.now(tz=timezone.utc),
                state=new_revision.state
            )
            transaction.savepoint_commit(trans_savepoint)
        else:
            raise ErrorWithCode.from_error(
                "BUDGET_STATE_NOT_ALLOWED", "Change in the state of the budget does not allow, budget in invalid state for operation", "")

        return company_budget

    @transaction.atomic
    def release_to_budget(self, company_budget: CompanyBudget, user: str, message: str):
        trans_savepoint = transaction.savepoint()
        last_revision: CompanyBudgetRevision = company_budget.companybudgetrevision_set.order_by(
            "-revision")[0]
        if(last_revision.state == CompanyBudgetRevisionState.in_creation_by_analyst):
            new_revision = self.__save_budget_service.duplicate_revision(last_revision)

            new_revision.state = CompanyBudgetRevisionState.budgeting
            new_revision.revision += 1
            new_revision.save()

            BudgetChangeTrack.objects.create(
                company_budget=company_budget,
                budget_revision=new_revision.revision,
                comment=message,
                user=user,
                change_at=datetime.now(tz=timezone.utc),
                state=new_revision.state
            )
            transaction.savepoint_commit(trans_savepoint)

        else:
            raise ErrorWithCode.from_error(
                "BUDGET_STATE_NOT_ALLOWED", "Change in the state of the budget does not allow, budget in invalid state for operation", "")
        return company_budget

    @transaction.atomic
    def release_to_operational_manager_approval(self, company_budget: CompanyBudget, user: str, message: str):
        trans_savepoint = transaction.savepoint()
        last_revision: CompanyBudgetRevision = company_budget.companybudgetrevision_set.order_by(
            "-revision")[0]
        if(last_revision.state == CompanyBudgetRevisionState.releasedto_analysis):
            validate_result = self.__validate_all_fields(CompanyBudgetRevisionSerializer(
                last_revision).data, f"/budgets/{last_revision.revision}")
            if validate_result:
                raise ErrorWithCode(validate_result)

            new_revision = self.__save_budget_service.duplicate_revision(last_revision)

            new_revision.state = CompanyBudgetRevisionState.releasedto_operational_manager_approval
            new_revision.revision += 1
            new_revision.save()

            BudgetChangeTrack.objects.create(
                company_budget=company_budget,
                budget_revision=new_revision.revision,
                comment=message,
                user=user,
                change_at=datetime.now(tz=timezone.utc),
                state=new_revision.state
            )
            transaction.savepoint_commit(trans_savepoint)

        else:
            raise ErrorWithCode.from_error(
                "BUDGET_STATE_NOT_ALLOWED", "Change in the state of the budget does not allow, budget in invalid state for operation", "")
        return company_budget

    @transaction.atomic
    def release_to_energy_manager_approval(self, company_budget: CompanyBudget, user: str, message: str):
        trans_savepoint = transaction.savepoint()
        last_revision: CompanyBudgetRevision = company_budget.companybudgetrevision_set.order_by(
            "-revision")[0]
        if(last_revision.state == CompanyBudgetRevisionState.releasedto_operational_manager_approval):
            new_revision = self.__save_budget_service.duplicate_revision(last_revision)

            new_revision.state = CompanyBudgetRevisionState.releasedto_energy_manager_approval
            new_revision.revision += 1
            new_revision.save()

            BudgetChangeTrack.objects.create(
                company_budget=company_budget,
                budget_revision=new_revision.revision,
                comment=message,
                user=user,
                change_at=datetime.now(tz=timezone.utc),
                state=new_revision.state
            )
            transaction.savepoint_commit(trans_savepoint)

        else:
            raise ErrorWithCode.from_error(
                "BUDGET_STATE_NOT_ALLOWED", "Change in the state of the budget does not allow, budget in invalid state for operation", "")

        return company_budget

    @transaction.atomic
    def energy_manager_approve(self, company_budget: CompanyBudget, user: str, message: str):
        trans_savepoint = transaction.savepoint()
        last_revision: CompanyBudgetRevision = company_budget.companybudgetrevision_set.order_by(
            "-revision")[0]
        if(last_revision.state == CompanyBudgetRevisionState.releasedto_energy_manager_approval):
            new_revision = self.__save_budget_service.duplicate_revision(last_revision)

            new_revision.state = CompanyBudgetRevisionState.energy_manager_approved
            new_revision.revision += 1
            new_revision.save()

            BudgetChangeTrack.objects.create(
                company_budget=company_budget,
                budget_revision=new_revision.revision,
                comment=message,
                user=user,
                change_at=datetime.now(tz=timezone.utc),
                state=new_revision.state
            )
            transaction.savepoint_commit(trans_savepoint)

        else:
            raise ErrorWithCode.from_error(
                "BUDGET_STATE_NOT_ALLOWED", "Change in the state of the budget does not allow, budget in invalid state for operation", "")

        return company_budget

    @transaction.atomic
    def disapprove(self, company_budget: CompanyBudget, user: str, message: str):
        trans_savepoint = transaction.savepoint()
        last_revision: CompanyBudgetRevision = company_budget.companybudgetrevision_set.order_by(
            "-revision")[0]
        if(last_revision.state not in (CompanyBudgetRevisionState.budgeting,
                                       CompanyBudgetRevisionState.disapproved)):
            new_revision = self.__save_budget_service.duplicate_revision(last_revision)

            new_revision.state = CompanyBudgetRevisionState.disapproved
            new_revision.revision += 1
            new_revision.save()

            BudgetChangeTrack.objects.create(
                company_budget=company_budget,
                budget_revision=new_revision.revision,
                comment=message,
                user=user,
                change_at=datetime.now(tz=timezone.utc),
                state=new_revision.state
            )
            transaction.savepoint_commit(trans_savepoint)

        else:
            raise ErrorWithCode.from_error(
                "BUDGET_STATE_NOT_ALLOWED", "Change in the state of the budget does not allow, budget in invalid state for operation", "")

        return company_budget

    def allow_disapprove(self, company_budget: CompanyBudget, user: dict):
        last_revision: CompanyBudgetRevision = company_budget.companybudgetrevision_set.order_by(
            "-revision")[0]

        if is_administrator(user):
            return True

        if last_revision.state == CompanyBudgetRevisionState.releasedto_analysis:
            return has_permission(user, groups.budget_projections, [permissions.EDITN2])
        
        if last_revision.state == CompanyBudgetRevisionState.releasedto_operational_manager_approval:
            return has_permission(user, groups.budget_projections, [permissions.APPROVALN1])
        
        if last_revision.state == CompanyBudgetRevisionState.releasedto_energy_manager_approval:
            return has_permission(user, groups.budget_projections, [permissions.APPROVALN2])

        if last_revision.state == CompanyBudgetRevisionState.energy_manager_approved:
            return has_permission(user, groups.budget_projections, [permissions.APPROVALN3])

        return True
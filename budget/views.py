from budget.serializers.CompanyBudgetRevisionSerializer import CompanyBudgetRevisionSerializer
from django.http import HttpRequest, FileResponse
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.db.models import Max, F, OuterRef, Subquery
from calendar import month_name, different_locale
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from SmartEnergy.auth import check_module, permissions, groups, modules, has_permission, is_administrator

from .serializers.CompanyBudgetSerializer import CompanyBudgetSerializer
from .serializers.CompanyBudgetSerializerSummary import CompanyBudgetSerializerSummary
from .serializers.SaveCompanyBudgetSerializer import SaveCompanyBudgetSerializer
from .serializers.SaveCompanyBudgetRevisionSerializer import SaveCompanyBudgetRevisionSerializer
from .serializers.SaveCalculatedCompanyBudgetSerializer import SaveCalculatedCompanyBudgetSerializer
from .services.BudgetCalculateService import BudgetCalculateService
from .services.SaveBudgetService import SaveBudgetService
from .services.IntegrationService import IntegrationService
from .services.WorkflowBudgetService import WorkflowBudgetService
from SmartEnergy.utils.exception.ErroWithCode import ErrorWithCode
from .services.ReportService import ReportService
from .models.CompanyBudget import CompanyBudget, CompanyBudgetCalculationMode
from .models.CompanyBudgetRevision import CompanyBudgetRevision, CompanyBudgetRevisionState
from .models.BudgetChangeTrack import BudgetChangeTrack


@check_module(modules.budget_budgets, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def export_company_budgets(request: HttpRequest):
    per_page = int(request.GET.get("perPage", 20) or 20)
    page = int(request.GET.get("page", 1) or 1)
    company_ids = request.GET.get("companies", None) or None
    year = request.GET.get("year", None) or None
    state = request.GET.get("state", None) or None
    sort = request.GET.get("sort", "-year") or "-year"
    id = request.GET.get("id", None) or None

    integration_service = IntegrationService()

    result = CompanyBudget.objects.all()

    if not is_administrator(request.user) and \
            not has_permission(request.user, groups.budget_projections, [permissions.EDITN2, permissions.APPROVALN2, permissions.APPROVALN3]):
        allowed_company_ids = integration_service.user_allowed_companies(
            request.user)
        result = result.filter(company_id__in=allowed_company_ids)

    if company_ids:
        company_ids = company_ids.split('|')
        result = result.filter(company_id__in=company_ids)

    if state != None:
        state_val = None
        for v in CompanyBudgetRevisionState:
            if state == v.verbose_name:
                state_val = v
                break
        result = result.annotate(last_revision_val=Max(
            'companybudgetrevision__revision'))
        result = result.filter(companybudgetrevision__state=state_val,
                               companybudgetrevision__revision=F("last_revision_val"))

    if year:
        result = result.filter(year=year)
    if id:
        result = result.filter(id=id)

    result = result.order_by(sort)
    result_paginator = Paginator(result, per_page)
    result_page = list(result_paginator.get_page(page)
                       .object_list) if result_paginator.num_pages >= page else []

    company_budget_ids = list(map(lambda v: v.id, result_page))

    def select_related(revs, field):
        return revs.select_related(field + "_budget") \
            .select_related(field + "_budget__january") \
            .select_related(field + "_budget__february") \
            .select_related(field + "_budget__march") \
            .select_related(field + "_budget__april") \
            .select_related(field + "_budget__may") \
            .select_related(field + "_budget__june") \
            .select_related(field + "_budget__july") \
            .select_related(field + "_budget__august") \
            .select_related(field + "_budget__september") \
            .select_related(field + "_budget__october") \
            .select_related(field + "_budget__november") \
            .select_related(field + "_budget__december")

    revisions = CompanyBudgetRevision.objects
    revisions = select_related(revisions, "firstyear")
    revisions = select_related(revisions, "secondyear")
    revisions = select_related(revisions, "thirdyear")
    revisions = select_related(revisions, "fourthyear")
    revisions = select_related(revisions, "fifthyear")

    newest_revision_query = CompanyBudgetRevision.objects.filter(
        company_budget_id=OuterRef("company_budget_id")).order_by('-revision')
    revisions = revisions.annotate(newest_revision=Subquery(
        newest_revision_query.values("id")[:1])).filter(id=F("newest_revision"))
    revisions = list(revisions.filter(
        company_budget_id__in=company_budget_ids))

    newest_change_query = BudgetChangeTrack.objects.filter(
        company_budget_id=OuterRef("company_budget_id")).order_by('-change_at')
    change_track = BudgetChangeTrack.objects.annotate(newest_change_id=Subquery(
        newest_change_query.values("id")[:1])).filter(id=F("newest_change_id"))
    change_track = list(change_track.filter(
        company_budget_id__in=company_budget_ids))

    integration_service = IntegrationService()

    result_page = list(map(lambda x: x.__dict__, result_page))
    for d in result_page:
        d["companybudgetrevision_set"] = list(
            filter(lambda v: v.company_budget_id == d["id"], revisions))
        d["budgetchangetrack_set"] = list(
            filter(lambda v: v.company_budget_id == d["id"], change_track))
        d["companybudgetrevision_set"][0].can_change_contract_usage_factor = integration_service.can_split_contract(
            d["company_id"])

    if len(result_page) == 0:
        raise ErrorWithCode.from_error(
            "NO_BUDGET_FOUND", "No budget found", "")

    report_service = ReportService()
    excel_bytes = report_service.generate_excel_report(result_page, "pt-BR")
    excel_bytes.seek(0)
    return FileResponse(excel_bytes, as_attachment=True, filename='export.xlsx', content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@check_module(modules.budget_budgets, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def list_company_budgets(request: HttpRequest):
    per_page = int(request.GET.get("perPage", 20) or 20)
    page = int(request.GET.get("page", 1) or 1)
    company_ids = request.GET.get("companies", None) or None
    year = request.GET.get("year", None) or None
    state = request.GET.get("state", None) or None
    sort = request.GET.get("sort", "-year") or "-year"

    integration_service = IntegrationService()

    result = CompanyBudget.objects.all()

    if not is_administrator(request.user) and \
            not has_permission(request.user, groups.budget_projections, [permissions.EDITN2, permissions.APPROVALN2, permissions.APPROVALN3]):
        allowed_company_ids = integration_service.user_allowed_companies(
            request.user)
        result = result.filter(company_id__in=allowed_company_ids)

    if company_ids:
        company_ids = company_ids.split('|')
        result = result.filter(company_id__in=company_ids)

    if state is not None:
        state_val = None
        for v in CompanyBudgetRevisionState:
            if state == v.verbose_name:
                state_val = v
                break
        result = result.annotate(last_revision_val=Max(
            'companybudgetrevision__revision'))
        result = result.filter(companybudgetrevision__state=state_val,
                               companybudgetrevision__revision=F("last_revision_val"))

    if year:
        result = result.filter(year=year)
    result = result.order_by(sort)
    result_paginator = Paginator(result, per_page)
    result_page = list(result_paginator.get_page(page)
                       .object_list) if result_paginator.num_pages >= page else []

    company_budget_ids = list(map(lambda v: v.id, result_page))
    revisions = CompanyBudgetRevision.objects

    newest_revision_query = CompanyBudgetRevision.objects.filter(
        company_budget_id=OuterRef("company_budget_id")).order_by('-revision')
    revisions = revisions.annotate(newest_revision=Subquery(
        newest_revision_query.values("id")[:1])).filter(id=F("newest_revision"))
    revisions = list(revisions.filter(
        company_budget_id__in=company_budget_ids))

    newest_change_query = BudgetChangeTrack.objects.filter(
        company_budget_id=OuterRef("company_budget_id")).order_by('-change_at')
    change_track = BudgetChangeTrack.objects.annotate(newest_change_id=Subquery(
        newest_change_query.values("id")[:1])).filter(id=F("newest_change_id"))
    change_track = list(change_track.filter(
        company_budget_id__in=company_budget_ids))

    integration_service = IntegrationService()

    result_page = list(map(lambda x: x.__dict__, result_page))
    for d in result_page:
        d["companybudgetrevision_set"] = list(
            filter(lambda v: v.company_budget_id == d["id"], revisions))
        d["budgetchangetrack_set"] = list(
            filter(lambda v: v.company_budget_id == d["id"], change_track))
        d["companybudgetrevision_set"][0].can_change_contract_usage_factor = integration_service.can_split_contract(
            d["company_id"])

    serializer = CompanyBudgetSerializerSummary(result_page, many=True)

    response = Response(serializer.data)
    response["X-Total-Count"] = result_paginator.count
    response["X-Total-Pages"] = result_paginator.num_pages
    response["Access-Control-Expose-Headers"] = "X-Total-Count, X-Total-Pages"
    return response


@check_module(modules.budget_budgets, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def get_company_budget(request, id):
    company_budget: CompanyBudget = CompanyBudget.objects.get(id=id)
    integration_service = IntegrationService()

    if not is_administrator(request.user) and \
            not has_permission(request.user, groups.budget_projections, [permissions.EDITN2, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3]):
        allowed_company_ids = integration_service.user_allowed_companies(
            request.user)
        if company_budget.company_id not in allowed_company_ids:
            raise PermissionDenied()

    last_revision = company_budget.companybudgetrevision_set.order_by(
        "-revision")[0]

    company_budget = {
        "id": company_budget.id,
        "year": company_budget.year,
        "company_id": company_budget.company_id,
        "calculation_mode": company_budget.calculation_mode,
        "companybudgetrevision_set": [last_revision],
        "budgetchangetrack_set": company_budget.budgetchangetrack_set.all()
    }

    integration_service = IntegrationService()

    for revision in company_budget['companybudgetrevision_set']:
        def update_month(month, month_data, production):
            month_data.production_readonly = False if production.get(
                month) is None else True

        def update_year(year_data, year):
            production = integration_service.get_production(
                company_budget["company_id"], int(year))
            update_month("january", year_data.january, production)
            update_month("february", year_data.february, production)
            update_month("march", year_data.march, production)
            update_month("april", year_data.april, production)
            update_month("may", year_data.may, production)
            update_month("june", year_data.june, production)
            update_month("july", year_data.july, production)
            update_month("august", year_data.august, production)
            update_month("september", year_data.september, production)
            update_month("october", year_data.october, production)
            update_month("november", year_data.november, production)
            update_month("december", year_data.december, production)

        update_year(revision.firstyear_budget, company_budget["year"])
        update_year(revision.secondyear_budget, company_budget["year"]+1)
        update_year(revision.thirdyear_budget, company_budget["year"]+2)
        update_year(revision.fourthyear_budget, company_budget["year"]+3)
        update_year(revision.fifthyear_budget, company_budget["year"]+4)

    can_change_contract_usage_factor = integration_service.can_split_contract(
        company_budget["company_id"])
    for rev in company_budget["companybudgetrevision_set"]:
        rev.can_change_contract_usage_factor = can_change_contract_usage_factor

    serializer = CompanyBudgetSerializer(company_budget)
    return Response(serializer.data)


@check_module(modules.budget_budgets, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def get_company_budget_revision(request, id: int, revision_number: int):
    company_budget: CompanyBudget = CompanyBudget.objects.get(id=id)
    integration_service = IntegrationService()

    if not is_administrator(request.user) and \
            not has_permission(request.user, groups.budget_projections, [permissions.EDITN2, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3]):
        allowed_company_ids = integration_service.user_allowed_companies(
            request.user)
        if company_budget.company_id not in allowed_company_ids:
            raise PermissionDenied()

    revision = company_budget.companybudgetrevision_set.get(
        revision=revision_number)

    def update_month(month, month_data, production):
        month_data.production_readonly = False if production.get(
            month) is None else True

    def update_year(year_data, year):
        production = integration_service.get_production(
            company_budget.company_id, int(year))
        update_month("january", year_data.january, production)
        update_month("february", year_data.february, production)
        update_month("march", year_data.march, production)
        update_month("april", year_data.april, production)
        update_month("may", year_data.may, production)
        update_month("june", year_data.june, production)
        update_month("july", year_data.july, production)
        update_month("august", year_data.august, production)
        update_month("september", year_data.september, production)
        update_month("october", year_data.october, production)
        update_month("november", year_data.november, production)
        update_month("december", year_data.december, production)

    update_year(revision.firstyear_budget, company_budget.year)
    update_year(revision.secondyear_budget, company_budget.year+1)
    update_year(revision.thirdyear_budget, company_budget.year+2)
    update_year(revision.fourthyear_budget, company_budget.year+3)
    update_year(revision.fifthyear_budget, company_budget.year+4)

    can_change_contract_usage_factor = integration_service.can_split_contract(
        company_budget.company_id)
    revision.can_change_contract_usage_factor = can_change_contract_usage_factor

    serializer = CompanyBudgetRevisionSerializer(revision)
    return Response(serializer.data)


@check_module(modules.budget_budgets, [permissions.EDITN2, permissions.EDITN1])
def create_company_budget(request):
    serializer = SaveCompanyBudgetSerializer(data=request.data)
    if serializer.is_valid(True):
        integration_service = IntegrationService()
        budget_calculate_service = BudgetCalculateService(integration_service)
        save_budget_service = SaveBudgetService(
            budget_calculate_service, integration_service)

        if not save_budget_service.is_allowed_year(serializer.validated_data.get("year")):
            raise ErrorWithCode.from_error(
                "BUDGET_YEAR_NOT_ALLOWED", "Changes in budget with year different from the next", "/year")

        create_state = CompanyBudgetRevisionState.budgeting
        if has_permission(request.user, groups.budget_projections, [permissions.EDITN2]) or is_administrator(request.user):
            create_state = CompanyBudgetRevisionState.in_creation_by_analyst

        company_budget = save_budget_service.create_budget(
            serializer.validated_data, f"{request.auth.get('cn')}-{request.auth.get('UserFullName')}", create_state)

        last_revision = company_budget.companybudgetrevision_set.order_by(
            "-revision")[0]
        company_budget = {
            "id": company_budget.id,
            "year": company_budget.year,
            "company_id": company_budget.company_id,
            "calculation_mode": company_budget.calculation_mode,
            "companybudgetrevision_set": [last_revision],
            "budgetchangetrack_set": company_budget.budgetchangetrack_set.all()
        }

        can_change_contract_usage_factor = integration_service.can_split_contract(
            company_budget["company_id"])
        for rev in company_budget["companybudgetrevision_set"]:
            rev.can_change_contract_usage_factor = can_change_contract_usage_factor

        serializer = CompanyBudgetSerializer(company_budget)
        return Response(serializer.data)


@check_module(modules.budget_budgets, [permissions.EDITN1, permissions.EDITN2])
def update_company_budget(request, id):
    serializer = SaveCompanyBudgetSerializer(data=request.data)
    if serializer.is_valid(True):
        company_budget = CompanyBudget.objects.get(id=id)

        integration_service = IntegrationService()
        budget_calculate_service = BudgetCalculateService(integration_service)
        save_budget_service = SaveBudgetService(
            budget_calculate_service, integration_service)

        if(not save_budget_service.is_allowed_year(company_budget.year)):
            raise ErrorWithCode.from_error(
                "BUDGET_YEAR_NOT_ALLOWED", "Changes in budget with year different from the next", "/year")

        user = request.user
        if not save_budget_service.allow_update(company_budget, user):
            raise PermissionDenied()

        company_budget = save_budget_service.update_budget(
            company_budget, serializer.validated_data, f"{request.auth.get('cn')}-{request.auth.get('UserFullName')}")

        last_revision = company_budget.companybudgetrevision_set.order_by(
            "-revision")[0]
        company_budget = {
            "id": company_budget.id,
            "year": company_budget.year,
            "company_id": company_budget.company_id,
            "calculation_mode": company_budget.calculation_mode,
            "companybudgetrevision_set": [last_revision],
            "budgetchangetrack_set": company_budget.budgetchangetrack_set.all()
        }

        can_change_contract_usage_factor = integration_service.can_split_contract(
            company_budget["company_id"])
        for rev in company_budget["companybudgetrevision_set"]:
            rev.can_change_contract_usage_factor = can_change_contract_usage_factor

        serializer = CompanyBudgetSerializer(company_budget)
        return Response(serializer.data)


@check_module(modules.budget_budgets, [permissions.EDITN2])
def release_to_technical_area(request, id):
    company_budget = CompanyBudget.objects.get(id=id)
    integration_service = IntegrationService()
    budget_calculate_service = BudgetCalculateService(integration_service)
    save_budget_service = SaveBudgetService(
        budget_calculate_service, integration_service)
    workflow_service = WorkflowBudgetService(save_budget_service)

    if(not save_budget_service.is_allowed_year(company_budget.year)):
        raise ErrorWithCode.from_error(
            "BUDGET_YEAR_NOT_ALLOWED", "Changes in budget with year different from the next", "/year")

    company_budget = workflow_service.release_to_budget(
        company_budget, f"{request.auth.get('cn')}-{request.auth.get('UserFullName')}", request.data.get("message"))

    last_revision = company_budget.companybudgetrevision_set.order_by(
        "-revision")[0]
    company_budget = {
        "id": company_budget.id,
        "year": company_budget.year,
        "company_id": company_budget.company_id,
        "calculation_mode": company_budget.calculation_mode,
        "companybudgetrevision_set": [last_revision],
        "budgetchangetrack_set": company_budget.budgetchangetrack_set.all()
    }

    can_change_contract_usage_factor = integration_service.can_split_contract(
        company_budget["company_id"])
    for rev in company_budget["companybudgetrevision_set"]:
        rev.can_change_contract_usage_factor = can_change_contract_usage_factor

    serializer = CompanyBudgetSerializer(company_budget)
    return Response(serializer.data)


@check_module(modules.budget_budgets, [permissions.EDITN1])
def release_company_budget_to_analysis(request, id):
    company_budget = CompanyBudget.objects.get(id=id)
    integration_service = IntegrationService()
    budget_calculate_service = BudgetCalculateService(integration_service)
    save_budget_service = SaveBudgetService(
        budget_calculate_service, integration_service)
    workflow_service = WorkflowBudgetService(save_budget_service)

    if(not save_budget_service.is_allowed_year(company_budget.year)):
        raise ErrorWithCode.from_error(
            "BUDGET_YEAR_NOT_ALLOWED", "Changes in budget with year different from the next", "/year")

    if not is_administrator(request.user):
        allowed_company_ids = integration_service.user_allowed_companies(
            request.user)
        if company_budget.company_id not in allowed_company_ids:
            raise PermissionDenied()

    company_budget = workflow_service.release_to_analysis(
        company_budget, f"{request.auth.get('cn')}-{request.auth.get('UserFullName')}", request.data.get("message"))

    last_revision = company_budget.companybudgetrevision_set.order_by(
        "-revision")[0]
    company_budget = {
        "id": company_budget.id,
        "year": company_budget.year,
        "company_id": company_budget.company_id,
        "calculation_mode": company_budget.calculation_mode,
        "companybudgetrevision_set": [last_revision],
        "budgetchangetrack_set": company_budget.budgetchangetrack_set.all()
    }

    can_change_contract_usage_factor = integration_service.can_split_contract(
        company_budget["company_id"])
    for rev in company_budget["companybudgetrevision_set"]:
        rev.can_change_contract_usage_factor = can_change_contract_usage_factor

    serializer = CompanyBudgetSerializer(company_budget)
    return Response(serializer.data)


@check_module(modules.budget_budgets, [permissions.EDITN2])
def release_company_budget_to_operational_manager_approval(request, id):
    company_budget = CompanyBudget.objects.get(id=id)
    integration_service = IntegrationService()
    budget_calculate_service = BudgetCalculateService(integration_service)
    save_budget_service = SaveBudgetService(
        budget_calculate_service, integration_service)
    workflow_service = WorkflowBudgetService(save_budget_service)

    if(not save_budget_service.is_allowed_year(company_budget.year)):
        raise ErrorWithCode.from_error(
            "BUDGET_YEAR_NOT_ALLOWED", "Changes in budget with year different from the next", "/year")

    company_budget = workflow_service.release_to_operational_manager_approval(
        company_budget, f"{request.auth.get('cn')}-{request.auth.get('UserFullName')}", request.data.get("message"))

    last_revision = company_budget.companybudgetrevision_set.order_by(
        "-revision")[0]
    company_budget = {
        "id": company_budget.id,
        "year": company_budget.year,
        "company_id": company_budget.company_id,
        "calculation_mode": company_budget.calculation_mode,
        "companybudgetrevision_set": [last_revision],
        "budgetchangetrack_set": company_budget.budgetchangetrack_set.all()
    }

    can_change_contract_usage_factor = integration_service.can_split_contract(
        company_budget["company_id"])
    for rev in company_budget["companybudgetrevision_set"]:
        rev.can_change_contract_usage_factor = can_change_contract_usage_factor

    serializer = CompanyBudgetSerializer(company_budget)
    return Response(serializer.data)


@check_module(modules.budget_budgets, [permissions.APPROVALN1])
def release_company_budget_to_energy_manager_approval(request, id):
    company_budget = CompanyBudget.objects.get(id=id)
    integration_service = IntegrationService()
    budget_calculate_service = BudgetCalculateService(integration_service)
    save_budget_service = SaveBudgetService(
        budget_calculate_service, integration_service)
    workflow_service = WorkflowBudgetService(save_budget_service)

    if(not save_budget_service.is_allowed_year(company_budget.year)):
        raise ErrorWithCode.from_error(
            "BUDGET_YEAR_NOT_ALLOWED", "Changes in budget with year different from the next", "/year")

    company_budget = workflow_service.release_to_energy_manager_approval(
        company_budget, f"{request.auth.get('cn')}-{request.auth.get('UserFullName')}", request.data.get("message"))
    last_revision = company_budget.companybudgetrevision_set.order_by(
        "-revision")[0]

    company_budget = {
        "id": company_budget.id,
        "year": company_budget.year,
        "company_id": company_budget.company_id,
        "calculation_mode": company_budget.calculation_mode,
        "companybudgetrevision_set": [last_revision],
        "budgetchangetrack_set": company_budget.budgetchangetrack_set.all()
    }

    can_change_contract_usage_factor = integration_service.can_split_contract(
        company_budget["company_id"])
    for rev in company_budget["companybudgetrevision_set"]:
        rev.can_change_contract_usage_factor = can_change_contract_usage_factor

    serializer = CompanyBudgetSerializer(company_budget)
    return Response(serializer.data)


@check_module(modules.budget_budgets, [permissions.APPROVALN2])
def energy_manager_company_budget_approve(request, id):
    company_budget = CompanyBudget.objects.get(id=id)
    integration_service = IntegrationService()
    budget_calculate_service = BudgetCalculateService(integration_service)
    save_budget_service = SaveBudgetService(
        budget_calculate_service, integration_service)
    workflow_service = WorkflowBudgetService(save_budget_service)

    if(not save_budget_service.is_allowed_year(company_budget.year)):
        raise ErrorWithCode.from_error(
            "BUDGET_YEAR_NOT_ALLOWED", "Changes in budget with year different from the next", "/year")

    user = request.user
    company_budget = workflow_service.energy_manager_approve(
        company_budget, f"{request.auth.get('cn')}-{request.auth.get('UserFullName')}", request.data.get("message"))
    last_revision = company_budget.companybudgetrevision_set.order_by(
        "-revision")[0]

    company_budget = {
        "id": company_budget.id,
        "year": company_budget.year,
        "company_id": company_budget.company_id,
        "calculation_mode": company_budget.calculation_mode,
        "companybudgetrevision_set": [last_revision],
        "budgetchangetrack_set": company_budget.budgetchangetrack_set.all()
    }

    can_change_contract_usage_factor = integration_service.can_split_contract(
        company_budget["company_id"])
    for rev in company_budget["companybudgetrevision_set"]:
        rev.can_change_contract_usage_factor = can_change_contract_usage_factor

    serializer = CompanyBudgetSerializer(company_budget)
    return Response(serializer.data)


@check_module(modules.budget_budgets, [permissions.EDITN2, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def disapprove_company_budget(request, id):
    company_budget = CompanyBudget.objects.get(id=id)
    integration_service = IntegrationService()
    budget_calculate_service = BudgetCalculateService(integration_service)
    save_budget_service = SaveBudgetService(
        budget_calculate_service, integration_service)
    workflow_service = WorkflowBudgetService(save_budget_service)

    if(not save_budget_service.is_allowed_year(company_budget.year)):
        raise ErrorWithCode.from_error(
            "BUDGET_YEAR_NOT_ALLOWED", "Changes in budget with year different from the next", "/year")

    user = request.user
    if not workflow_service.allow_disapprove(company_budget, user):
        raise PermissionDenied()

    company_budget = workflow_service.disapprove(
        company_budget, f"{request.auth.get('cn')}-{request.auth.get('UserFullName')}", request.data.get("message"))
    last_revision = company_budget.companybudgetrevision_set.order_by(
        "-revision")[0]

    company_budget = {
        "id": company_budget.id,
        "year": company_budget.year,
        "company_id": company_budget.company_id,
        "calculation_mode": company_budget.calculation_mode,
        "companybudgetrevision_set": [last_revision],
        "budgetchangetrack_set": company_budget.budgetchangetrack_set.all()
    }

    can_change_contract_usage_factor = integration_service.can_split_contract(
        company_budget["company_id"])
    for rev in company_budget["companybudgetrevision_set"]:
        rev.can_change_contract_usage_factor = can_change_contract_usage_factor

    serializer = CompanyBudgetSerializer(company_budget)
    return Response(serializer.data)


@check_module(modules.budget_budgets, [permissions.EDITN1, permissions.EDITN2])
def calculate_budget(request):
    integration_service = IntegrationService()
    budget_calculate_service = BudgetCalculateService(integration_service)

    serializer = SaveCompanyBudgetSerializer(data=request.data)
    if serializer.is_valid(True):
        consumption_limit = serializer.validated_data["budget"]["consumption_limit"]
        contract_usage_factor_peak = serializer.validated_data["budget"]["contract_usage_factor_peak"]
        contract_usage_factor_offpeak = serializer.validated_data[
            "budget"]["contract_usage_factor_offpeak"]

        calculation_mode = None
        for v in CompanyBudgetCalculationMode:
            if serializer.validated_data["calculation_mode"] == v.verbose_name:
                calculation_mode = v
                break

        firstyear_budget = serializer.validated_data["budget"]["firstyear_budget"]
        peak_hour_month_data, offpeak_hour_month_data = integration_service.get_hour_month(
            serializer.validated_data["year"])
        if(calculation_mode == CompanyBudgetCalculationMode.flat):
            budget_calculate_service.unflat_monthly_budget_data(firstyear_budget,
                                                                peak_hour_month_data, offpeak_hour_month_data)
        budget_calculate_service.calc_monthly_budget(
            firstyear_budget, consumption_limit, contract_usage_factor_offpeak, contract_usage_factor_peak, serializer.validated_data["company_id"], serializer.validated_data["year"])

        secondyear_budget = serializer.validated_data["budget"]["secondyear_budget"]
        peak_hour_month_data, offpeak_hour_month_data = integration_service.get_hour_month(
            serializer.validated_data["year"]+1)
        if(calculation_mode == CompanyBudgetCalculationMode.flat):
            budget_calculate_service.unflat_monthly_budget_data(secondyear_budget,
                                                                peak_hour_month_data, offpeak_hour_month_data)
        budget_calculate_service.calc_monthly_budget(
            secondyear_budget, consumption_limit, contract_usage_factor_offpeak, contract_usage_factor_peak, serializer.validated_data["company_id"], serializer.validated_data["year"]+1)

        peak_hour_month_data, offpeak_hour_month_data = integration_service.get_hour_month(
            serializer.validated_data["year"]+2)
        peak_hour_month_data = sum(peak_hour_month_data.values())
        offpeak_hour_month_data = sum(offpeak_hour_month_data.values())

        def clean_and_calc_avg(iterable, default): return default if all(
            value is None for value in iterable) else sum(filter(None, iterable)) / 12
        def clean_and_sum(iterable, default): return default if all(
            value is None for value in iterable) else sum(filter(None, iterable))

        thirdyear_budget = serializer.validated_data["budget"]["thirdyear_budget"]
        if(calculation_mode == CompanyBudgetCalculationMode.flat):
            budget_calculate_service.unflat_budget_data(thirdyear_budget,
                                                        peak_hour_month_data, offpeak_hour_month_data)
        thirdyear_budget["contracted_peak_power_demand"] = clean_and_calc_avg(integration_service.get_contracted_peak_power_demand(
            serializer.validated_data["company_id"], serializer.validated_data["year"]+2, contract_usage_factor_peak).values(), thirdyear_budget["contracted_peak_power_demand"])
        thirdyear_budget["contracted_offpeak_power_demand"] = clean_and_calc_avg(integration_service.get_contracted_offpeak_power_demand(
            serializer.validated_data["company_id"], serializer.validated_data["year"]+2, contract_usage_factor_offpeak).values(), thirdyear_budget["contracted_offpeak_power_demand"])
        productions = integration_service.get_production(
            serializer.validated_data["company_id"], serializer.validated_data["year"]+2).values()
        thirdyear_budget["production"] = clean_and_sum(
            productions, thirdyear_budget["production"])
        thirdyear_budget["production_readonly"] = not all(
            value is None for value in productions)

        budget_calculate_service.calc_budget(
            thirdyear_budget, consumption_limit, peak_hour_month_data, offpeak_hour_month_data)

        peak_hour_month_data, offpeak_hour_month_data = integration_service.get_hour_month(
            serializer.validated_data["year"]+3)
        peak_hour_month_data = sum(peak_hour_month_data.values())
        offpeak_hour_month_data = sum(offpeak_hour_month_data.values())
        fourthyear_budget = serializer.validated_data["budget"]["fourthyear_budget"]
        if(calculation_mode == CompanyBudgetCalculationMode.flat):
            budget_calculate_service.unflat_budget_data(fourthyear_budget,
                                                        peak_hour_month_data, offpeak_hour_month_data)
        fourthyear_budget["contracted_peak_power_demand"] = clean_and_calc_avg(integration_service.get_contracted_peak_power_demand(
            serializer.validated_data["company_id"], serializer.validated_data["year"]+3, contract_usage_factor_peak).values(), fourthyear_budget["contracted_peak_power_demand"])
        fourthyear_budget["contracted_offpeak_power_demand"] = clean_and_calc_avg(integration_service.get_contracted_offpeak_power_demand(
            serializer.validated_data["company_id"], serializer.validated_data["year"]+3, contract_usage_factor_offpeak).values(), fourthyear_budget["contracted_offpeak_power_demand"])
        productions = integration_service.get_production(
            serializer.validated_data["company_id"], serializer.validated_data["year"]+3).values()
        fourthyear_budget["production"] = clean_and_sum(
            productions, fourthyear_budget["production"])
        fourthyear_budget["production_readonly"] = not all(
            value is None for value in productions)

        budget_calculate_service.calc_budget(
            fourthyear_budget, consumption_limit, peak_hour_month_data, offpeak_hour_month_data)

        peak_hour_month_data, offpeak_hour_month_data = integration_service.get_hour_month(
            serializer.validated_data["year"]+4)
        peak_hour_month_data = sum(peak_hour_month_data.values())
        offpeak_hour_month_data = sum(offpeak_hour_month_data.values())
        fifthyear_budget = serializer.validated_data["budget"]["fifthyear_budget"]
        if(calculation_mode == CompanyBudgetCalculationMode.flat):
            budget_calculate_service.unflat_budget_data(fifthyear_budget,
                                                        peak_hour_month_data, offpeak_hour_month_data)
        fifthyear_budget["contracted_peak_power_demand"] = clean_and_calc_avg(integration_service.get_contracted_peak_power_demand(
            serializer.validated_data["company_id"], serializer.validated_data["year"]+4, contract_usage_factor_peak).values(), fifthyear_budget["contracted_peak_power_demand"])
        fifthyear_budget["contracted_offpeak_power_demand"] = clean_and_calc_avg(integration_service.get_contracted_offpeak_power_demand(
            serializer.validated_data["company_id"], serializer.validated_data["year"]+4, contract_usage_factor_offpeak).values(), fifthyear_budget["contracted_offpeak_power_demand"])
        productions = integration_service.get_production(
            serializer.validated_data["company_id"], serializer.validated_data["year"]+4).values()
        fifthyear_budget["production"] = clean_and_sum(
            productions, fifthyear_budget["production"])
        fifthyear_budget["production_readonly"] = not all(
            value is None for value in productions)

        budget_calculate_service.calc_budget(
            fifthyear_budget, consumption_limit, peak_hour_month_data, offpeak_hour_month_data)

        can_change_contract_usage_factor = integration_service.can_split_contract(
            serializer.validated_data["company_id"])
        serializer.validated_data["budget"]["can_change_contract_usage_factor"] = can_change_contract_usage_factor

        serializer = SaveCalculatedCompanyBudgetSerializer(
            serializer.validated_data)
        return Response(serializer.data)


@check_module(modules.budget_budgets, [permissions.EDITN1, permissions.EDITN2])
def autofilled_fields(request, company_id, year):
    integration_service = IntegrationService()

    english_month_names = []
    with different_locale('C.UTF-8'):
        english_month_names = list(map(lambda s: s.lower(), month_name[1:]))

    def init_monthly(year):
        ret = {}
        contracted_peak_power_demand = integration_service.get_contracted_peak_power_demand(
            company_id, year, 1)
        contracted_offpeak_power_demand = integration_service.get_contracted_offpeak_power_demand(
            company_id, year, 1)
        production = integration_service.get_production(company_id, year)

        for month in english_month_names:
            ret[month] = {
                "contractedPeakPowerDemand":  contracted_peak_power_demand[month],
                "contractedOffPeakPowerDemand": contracted_offpeak_power_demand[month],
                "production": production[month]
            }
        return ret

    def sum_year(data):
        ret = {
            "contractedPeakPowerDemand":  None,
            "contractedOffPeakPowerDemand": None,
            "production": None
        }
        for month in english_month_names:
            if data[month]["contractedPeakPowerDemand"] is not None:
                ret["contractedPeakPowerDemand"] = (
                    ret["contractedPeakPowerDemand"] or 0) + data[month]["contractedPeakPowerDemand"]
            if data[month]["contractedOffPeakPowerDemand"] is not None:
                ret["contractedOffPeakPowerDemand"] = (
                    ret["contractedOffPeakPowerDemand"] or 0) + data[month]["contractedOffPeakPowerDemand"]
            if data[month]["production"] is not None:
                ret["production"] = (ret["production"] or 0) + \
                    data[month]["production"]

        if ret["contractedPeakPowerDemand"]:
            ret["contractedPeakPowerDemand"] /= 12
        if ret["contractedOffPeakPowerDemand"]:
            ret["contractedOffPeakPowerDemand"] /= 12

        return ret

    data = {
        "consumptionLimit": 0.05,
        "contractUsageFactor": 1,
        "canChangeContractUsageFactor": integration_service.can_split_contract(company_id)
    }

    data["firstYearBudget"] = init_monthly(year)
    data["secondYearBudget"] = init_monthly(year+1)
    data["thirdYearBudget"] = sum_year(init_monthly(year+2))
    data["fourthYearBudget"] = sum_year(init_monthly(year+3))
    data["fifthYearBudget"] = sum_year(init_monthly(year+4))

    serializer = SaveCompanyBudgetRevisionSerializer(data=data)
    serializer.is_valid()
    return Response(serializer.data)


@check_module(modules.budget_budgets, [permissions.EDITN1, permissions.EDITN2])
def budget_already_exists(request, company_id, year):
    budget = CompanyBudget.objects.filter(
        company_id=company_id, year=year).first()
    if budget is None:
        integration_service = IntegrationService()
        if(integration_service.has_registered_contract(company_id, year) == {"has_contract": True, "in_effect": True}):
            return Response({"alerts": []}, status.HTTP_404_NOT_FOUND)
        elif (integration_service.has_registered_contract(company_id, year) == {"has_contract": True, "in_effect": False}):
            return Response({"alerts": ["THERE_IS_CONTRACT_OUT_OF_EFFECT"]}, status.HTTP_404_NOT_FOUND)
        else:
            return Response({"alerts": ["THERE_IS_NO_REGISTERED_CONTRACT"]}, status.HTTP_404_NOT_FOUND)
    return Response({"id": budget.id, "alerts": []})

from calendar import month_name, different_locale, datetime
import logging
from uuid import uuid4
from django.http import HttpRequest
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.db.models import F, OuterRef, Subquery
from django.http import HttpRequest, FileResponse
from datetime import date, datetime, timezone
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from typing import List

from SmartEnergy.auth import check_module, permissions, groups, modules, has_permission, is_administrator, get_user_companies

from .serializers.CompanyPlanMonitoringSerializer import CompanyPlanMonitoringSerializer
from .serializers.SaveCompanyPlanMonitoringSerializer import SaveCompanyPlanMonitoringSerializer
from .serializers.PlanMonitoringSerializer import PlanMonitoringSerializer
from .serializers.CompanyPlanMonitoringSummarySerializer import CompanyPlanMonitoringSummarySerializer

from .services.PlanMonitoringCalculateService import PlanMonitoringCalculateService
from .services.SavePlanMonitoringService import SavePlanMonitoringService
from .services.IntegrationService import IntegrationService
from .services.ErrorWithCode import ErrorWithCode
from .services.ReportService import ReportService

from .models.MonthlyPlanMonitoring import MonthlyPlanMonitoring
from .models.PlanMonitoring import PlanMonitoring
from .models.CompanyPlanMonitoring import CompanyPlanMonitoring, CompanyPlanMonitoringCalculationMode
from .models.CompanyPlanMonitoringRevision import CompanyPlanMonitoringRevision
from .models.PlanMonitoringChangeTrack import PlanMonitoringChangeTrack, CompanyPlanMonitoringChangeAction

@check_module(modules.budget_projections, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def export_plan_monitoring(request: HttpRequest):
    perPage = int(request.GET.get("perPage", 20) or 20)
    page = int(request.GET.get("page", 1) or 1)
    companyIds = request.GET.get("companies", None) or None
    year = request.GET.get("year", None) or None
    sort = request.GET.get("sort", "-year") or "-year"
    state = request.GET.get("state", None) or None
    id = request.GET.get("id", None) or None

    result = CompanyPlanMonitoring.objects.all()

    if state != None:  # WithOpenJustifications, NoOpenJustification
        result = result.filter(
            has_open_justification=state == "WithOpenJustifications")

    integration_service = IntegrationService()
    if not is_administrator(request.user)  and \
            not has_permission(request.user, groups.budget_projections, [permissions.EDITN2, permissions.APPROVALN2, permissions.APPROVALN3]):
        allowed_company_ids = integration_service.user_allowed_companies(request.user)
        result = result.filter(company_id__in=allowed_company_ids)

    if companyIds:
        companyIds = companyIds.split('|')
        result = result.filter(company_id__in=companyIds)
    if year:
        result = result.filter(year=year)
    if id:
        result = result.filter(id=id)

    result = result.order_by(sort)
    result_paginator = Paginator(result, perPage)
    result_page = list(result_paginator.get_page(page)
                       .object_list) if result_paginator.num_pages >= page else []

    company_planmonitoring_ids = list(map(lambda v: v.id, result_page))

    def select_related(revs, field):
        return revs.select_related(field + "_plan_monitoring") \
            .select_related(field + "_plan_monitoring__january") \
            .select_related(field + "_plan_monitoring__february") \
            .select_related(field + "_plan_monitoring__march") \
            .select_related(field + "_plan_monitoring__april") \
            .select_related(field + "_plan_monitoring__may") \
            .select_related(field + "_plan_monitoring__june") \
            .select_related(field + "_plan_monitoring__july") \
            .select_related(field + "_plan_monitoring__august") \
            .select_related(field + "_plan_monitoring__september") \
            .select_related(field + "_plan_monitoring__october") \
            .select_related(field + "_plan_monitoring__november") \
            .select_related(field + "_plan_monitoring__december")

    revisions = CompanyPlanMonitoringRevision.objects
    revisions = select_related(revisions, "firstyear")
    revisions = select_related(revisions, "secondyear")

    newest_revision_query = CompanyPlanMonitoringRevision.objects.filter(
        company_plan_monitoring_id=OuterRef("company_plan_monitoring_id")).order_by('-revision')
    revisions = revisions.annotate(newest_revision=Subquery(
        newest_revision_query.values("id")[:1])).filter(id=F("newest_revision"))
    revisions = list(revisions.filter(
        company_plan_monitoring_id__in=company_planmonitoring_ids))

    newest_change_query = PlanMonitoringChangeTrack.objects.filter(
        company_plan_monitoring_id=OuterRef("company_plan_monitoring_id")).order_by('-change_at')
    change_track = PlanMonitoringChangeTrack.objects.annotate(newest_change_id=Subquery(
        newest_change_query.values("id")[:1])).filter(id=F("newest_change_id"))
    change_track = list(change_track.filter(
        company_plan_monitoring_id__in=company_planmonitoring_ids))

    result_page = list(map(lambda x: x.__dict__, result_page))
    for d in result_page:
        d["companyplanmonitoringrevision_set"] = list(
            filter(lambda v: v.company_plan_monitoring_id == d["id"], revisions))
        d["planmonitoringchangetrack_set"] = list(
            filter(lambda v: v.company_plan_monitoring_id == d["id"], change_track))

    if len(result_page) == 0:
        raise ErrorWithCode.from_error(
                "NO_PLANMONITORING_FOUND", "No Plan Monitoring found", "")

    report_service = ReportService()
    excel_bytes = report_service.generate_excel_report(result_page, "pt-BR")
    excel_bytes.seek(0)
    return FileResponse(excel_bytes, as_attachment=True, filename='export.xlsx', content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@check_module(modules.budget_projections, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def list_company_plan_monitoring(request: HttpRequest):
    perPage = int(request.GET.get("perPage", 20) or 20)
    page = int(request.GET.get("page", 1) or 1)
    companyIds = request.GET.get("companies", None) or None
    year = request.GET.get("year", None) or None
    sort = request.GET.get("sort", "-year") or "-year"
    state = request.GET.get("state", None) or None

    result = CompanyPlanMonitoring.objects.all()

    if state != None:  # WithOpenJustifications, NoOpenJustification
        result = result.filter(
            has_open_justification=state == "WithOpenJustifications")

    integration_service = IntegrationService()
    if not is_administrator(request.user) and \
            not has_permission(request.user, groups.budget_projections, [permissions.EDITN2, permissions.APPROVALN2, permissions.APPROVALN3]):
        allowed_company_ids = integration_service.user_allowed_companies(request.user)
        result = result.filter(company_id__in=allowed_company_ids)

    if companyIds:
        companyIds = companyIds.split('|')
        result = result.filter(company_id__in=companyIds)
    if year:
        result = result.filter(year=year)
    result = result.order_by(sort)
    result_paginator = Paginator(result, perPage)
    result_page = list(result_paginator.get_page(page)
                       .object_list) if result_paginator.num_pages >= page else []

    result_page = list(map(lambda x: x.__dict__, result_page))    

    serializer = CompanyPlanMonitoringSummarySerializer(result_page, many=True)

    response = Response(serializer.data)
    response["X-Total-Count"] = result_paginator.count
    response["X-Total-Pages"] = result_paginator.num_pages
    response["Access-Control-Expose-Headers"] = "X-Total-Count, X-Total-Pages"
    return response


@check_module(modules.budget_projections, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def get_plan_monitoring(request, id):
    def select_related(revs, field):
        return revs.select_related(field + "_plan_monitoring") \
            .select_related(field + "_plan_monitoring__january") \
            .select_related(field + "_plan_monitoring__february") \
            .select_related(field + "_plan_monitoring__march") \
            .select_related(field + "_plan_monitoring__april") \
            .select_related(field + "_plan_monitoring__may") \
            .select_related(field + "_plan_monitoring__june") \
            .select_related(field + "_plan_monitoring__july") \
            .select_related(field + "_plan_monitoring__august") \
            .select_related(field + "_plan_monitoring__september") \
            .select_related(field + "_plan_monitoring__october") \
            .select_related(field + "_plan_monitoring__november") \
            .select_related(field + "_plan_monitoring__december")

    company_plan_monitoring = CompanyPlanMonitoring.objects.get(id=id)

    integration_service = IntegrationService()
    user = request.user
    if not integration_service.user_allowed_company(user, company_plan_monitoring.company_id) and  not is_administrator(request.user) and \
            not has_permission(request.user, groups.budget_projections, [permissions.EDITN2, permissions.APPROVALN2, permissions.APPROVALN3]):
        raise PermissionDenied()

    revisions = company_plan_monitoring.companyplanmonitoringrevision_set
    revisions = select_related(revisions, "firstyear")
    revisions = select_related(revisions, "secondyear")

    company_plan_monitoring = {
        "id": company_plan_monitoring.id,
        "year": company_plan_monitoring.year,
        "company_id": company_plan_monitoring.company_id,
        "calculation_mode": company_plan_monitoring.calculation_mode,
        "companyplanmonitoringrevision_set": list(revisions),
        "planmonitoringchangetrack_set": company_plan_monitoring.planmonitoringchangetrack_set
    }
    english_month_names = []
    with different_locale('C.UTF-8'):
        english_month_names = list(map(lambda s: s.lower(), month_name))
    current_year = datetime.now().year
    previos_month = english_month_names[datetime.now().month- 1]
    last_revision: CompanyPlanMonitoringRevision = sorted(company_plan_monitoring['companyplanmonitoringrevision_set'], key=lambda k: k.revision)[-1]

    realized_peakpower_demand = integration_service.get_realized_peak_power_demand(company_plan_monitoring["company_id"], int(current_year), last_revision.contract_usage_factor_peak)
    realized_offpeak_power_demand = integration_service.get_realized_offpeak_power_demand(company_plan_monitoring["company_id"], int(current_year), last_revision.contract_usage_factor_offpeak)
    realized_peak_power_consumption = integration_service.get_realized_peak_power_consumption(company_plan_monitoring["company_id"], int(current_year))
    realized_offpeak_power_consumption = integration_service.get_realized_offpeak_power_consumption(company_plan_monitoring["company_id"], int(current_year))
    realized_production = integration_service.get_realized_production(company_plan_monitoring["company_id"], int(current_year))
    
    def update_year(year_data, year):
        for i in range(1, 13):
            month_data = getattr(year_data, english_month_names[i])
            month_data.realized_peakpower_demand_readonly = True
            month_data.realized_offpeak_power_demand_readonly = True
            month_data.realized_peak_power_consumption_readonly = True
            month_data.realized_offpeak_power_consumption_readonly = True
            month_data.realized_production_readonly = True
            
            if year == current_year and english_month_names[i] == previos_month:
                month_data.realized_peakpower_demand_readonly = False if realized_peakpower_demand.get(english_month_names[i]) is None else True
                month_data.realized_offpeak_power_demand_readonly = False if realized_offpeak_power_demand.get(english_month_names[i]) is None else True
                month_data.realized_peak_power_consumption_readonly = False if realized_peak_power_consumption.get(english_month_names[i]) is None else True
                month_data.realized_offpeak_power_consumption_readonly = False if realized_offpeak_power_consumption.get(english_month_names[i]) is None else True
                month_data.realized_production_readonly = False if realized_production.get(english_month_names[i]) is None else True
                month_data.realized_total_consumption_readonly = month_data.realized_peak_power_consumption_readonly or \
                    month_data.realized_offpeak_power_consumption_readonly        

    update_year(last_revision.firstyear_plan_monitoring, company_plan_monitoring["year"])
    update_year(last_revision.secondyear_plan_monitoring, company_plan_monitoring["year"]+1)

    serializer = CompanyPlanMonitoringSerializer(company_plan_monitoring)
    return Response(serializer.data)


@check_module(modules.budget_projections, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def update_company_plan_monitoring(request, id):
    serializer = SaveCompanyPlanMonitoringSerializer(data=request.data)
    if serializer.is_valid(True):
        company_plan_monitoring = CompanyPlanMonitoring.objects.get(id=id)

        integration_service = IntegrationService()
        user = request.user
        if not integration_service.user_allowed_company(user, company_plan_monitoring.company_id) and  not is_administrator(request.user) and \
            not has_permission(request.user, groups.budget_projections, [permissions.EDITN2, permissions.APPROVALN2, permissions.APPROVALN3]):
            raise PermissionDenied()

        if(company_plan_monitoring.has_open_justification):
            raise ErrorWithCode.from_error(
                "PLAN_HAS_OPEN_JUSTIFICATION",
                "Changes in plan with open justifications are not allowed")

        current_year = datetime.now().year
        current_month = datetime.now().month
        if(company_plan_monitoring.year != current_year and 
            not (current_month == 12 and current_year + 1 == company_plan_monitoring.year) and 
            not (current_month == 1 and current_year - 1 == company_plan_monitoring.year)):
            raise ErrorWithCode.from_error(
                "PLAN_CHANGE_YEAR_NOT_ALLOWED",
                "Changes in plan with year different from the current",
                "/year")
        
        plan_monitoring_calculate_service = PlanMonitoringCalculateService()
        save_plan_monitoring_service = SavePlanMonitoringService(
            plan_monitoring_calculate_service, integration_service)

        company_plan_monitoring = save_plan_monitoring_service.update_plan_monitoring(
            company_plan_monitoring, serializer.validated_data, f"{request.auth.get('cn')}-{request.auth.get('UserFullName')}", serializer.validated_data["comment"])

        serializer = CompanyPlanMonitoringSerializer(company_plan_monitoring)
        return Response(serializer.data)


@check_module(modules.budget_projections, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
@transaction.atomic
def justify_plan_monitoring(request, id):
    company_plan_monitoring: CompanyPlanMonitoring = CompanyPlanMonitoring.objects.get(
        id=id)

    plan_monitoring_calculate_service = PlanMonitoringCalculateService()
    integration_service = IntegrationService()
    save_service = SavePlanMonitoringService(plan_monitoring_calculate_service, integration_service)

    user = request.user
    if not integration_service.user_allowed_company(user, company_plan_monitoring.company_id) and  not is_administrator(request.user) and \
            not has_permission(request.user, groups.budget_projections, [permissions.EDITN2, permissions.APPROVALN2, permissions.APPROVALN3]):
        raise PermissionDenied()

    trans_savepoint = transaction.savepoint()

    revision: CompanyPlanMonitoringRevision = company_plan_monitoring.companyplanmonitoringrevision_set.order_by(
        "-revision")[0]
    revision = save_service.duplicate_revision(revision)
    revision.revision += 1
    revision.save()

    firstyear = revision.firstyear_plan_monitoring

    field_extenal_name = request.data.get("field")
    message = request.data.get("message")
    alert = request.data.get("alert")
    month = request.data.get("month")

    plan_serializer = PlanMonitoringSerializer()
    field = plan_serializer.fields[field_extenal_name].local_field

    month_data = getattr(firstyear, month)
    field_alerts: List[str] = month_data.__dict__.get(field + "_alerts")

    if(not field_alerts):
        raise ErrorWithCode.from_error(
            "PLAN_HAS_NO_PROVIDED_JUSTIFIABLE_FIELD",
            f"There is no field provided {field}")

    justification = PlanMonitoringChangeTrack.objects.create(
        company_plan_monitoring=company_plan_monitoring,
        plan_monitoring_revision=revision.revision,
        comment=message,
        user=f"{request.auth.get('cn')}-{request.auth.get('UserFullName')}",
        change_at=datetime.now(tz=timezone.utc),
        action=CompanyPlanMonitoringChangeAction.justification
    )

    field_index = field_alerts.index(alert + ":")
    field_alerts[field_index] = alert + ":"+str(justification.id)

    month_data.save()

    company_plan_monitoring.has_open_justification = plan_monitoring_calculate_service.has_open_justification(firstyear)
    company_plan_monitoring.save()

    transaction.savepoint_commit(trans_savepoint)

    serializer = CompanyPlanMonitoringSerializer(company_plan_monitoring)
    return Response(serializer.data)


@check_module(modules.budget_projections, [permissions.VIEW, permissions.EDITN1, permissions.EDITN2, permissions.APPROVALN1, permissions.APPROVALN2, permissions.APPROVALN3])
def calculate_plan_monitoring(request, id):
    integration_service = IntegrationService()
    plan_monitoring_calculate_service = PlanMonitoringCalculateService()
    save_plan_monitoring_service = SavePlanMonitoringService(
        plan_monitoring_calculate_service, integration_service)

    serializer = SaveCompanyPlanMonitoringSerializer(data=request.data)
    if serializer.is_valid(True):
        company_plan_monitoring = CompanyPlanMonitoring.objects.get(
            id=id)
        revision = company_plan_monitoring.companyplanmonitoringrevision_set.order_by(
            "-revision")[0]

        firstyear_plan_monitoring = serializer.validated_data[
            "company_plan_monitoring"]["firstyear_plan_monitoring"]
        peak_hour_month_data, offpeak_hour_month_data = integration_service.get_hour_month(
            company_plan_monitoring.year)
        save_plan_monitoring_service.update_monthly_plan_monitoring(
            revision.firstyear_plan_monitoring, firstyear_plan_monitoring, peak_hour_month_data, offpeak_hour_month_data,
            company_plan_monitoring.company_id, company_plan_monitoring.year, company_plan_monitoring.calculation_mode, 
            revision.contract_usage_factor_offpeak, revision.contract_usage_factor_peak, False)

        secondyear_plan_monitoring = serializer.validated_data[
            "company_plan_monitoring"]["secondyear_plan_monitoring"]
        peak_hour_month_data, offpeak_hour_month_data = integration_service.get_hour_month(
            company_plan_monitoring.year+1)
        save_plan_monitoring_service.update_monthly_plan_monitoring(
            revision.secondyear_plan_monitoring, secondyear_plan_monitoring, peak_hour_month_data, offpeak_hour_month_data,
            company_plan_monitoring.company_id, company_plan_monitoring.year+1, company_plan_monitoring.calculation_mode, 
            revision.contract_usage_factor_offpeak, revision.contract_usage_factor_peak, False)

        company_plan_monitoring = {
            "id": company_plan_monitoring.id,
            "year": company_plan_monitoring.year,
            "company_id": company_plan_monitoring.company_id,
            "calculation_mode": company_plan_monitoring.calculation_mode,
            "companyplanmonitoringrevision_set": [revision],
            "planmonitoringchangetrack_set": [],
            "state": "WithOpenJustifications" if company_plan_monitoring.has_open_justification else "NoOpenJustification"
        }

        serializer = CompanyPlanMonitoringSerializer(company_plan_monitoring)
        return Response(serializer.data)


@transaction.atomic
def create_plan_monitoring_from_budget(request: HttpRequest, company, year):
    english_month_names = []
    with different_locale('C.UTF-8'):
        english_month_names = list(map(lambda s: s.lower(), month_name))[1:]

    integration_service = IntegrationService()
    user = request.user
    if not is_administrator(user):
        raise PermissionDenied()

    budget_data = integration_service.get_budget_by_company(company, year)

    trans_savepoint = transaction.savepoint()
    if budget_data:
        budget_revision_data = budget_data['budgets'][0]

        company_plan_monitoring = CompanyPlanMonitoring.objects.filter(
            company_id=company, year=year)[:1]
        if company_plan_monitoring:
            company_plan_monitoring: CompanyPlanMonitoring = company_plan_monitoring[0]
        else:
            company_plan_monitoring = CompanyPlanMonitoring()
            company_plan_monitoring.year = year
            company_plan_monitoring.company_id = company
            company_plan_monitoring.has_open_justification = False
            company_plan_monitoring.calculation_mode = CompanyPlanMonitoringCalculationMode.modular
            company_plan_monitoring.save()

            first_year_plan_monitoring = MonthlyPlanMonitoring()

            for month in english_month_names:
                plan_monitoring = PlanMonitoring()
                plan_monitoring.save()
                setattr(first_year_plan_monitoring, month, plan_monitoring)

            first_year_plan_monitoring.save()

            second_year_plan_monitoring = MonthlyPlanMonitoring()

            for month in english_month_names:
                plan_monitoring = PlanMonitoring()
                plan_monitoring.save()
                setattr(second_year_plan_monitoring, month, plan_monitoring)

            second_year_plan_monitoring.save()

            company_plan_monitoring_revision = CompanyPlanMonitoringRevision()
            company_plan_monitoring_revision.revision = 1
            company_plan_monitoring_revision.company_plan_monitoring = company_plan_monitoring
            company_plan_monitoring_revision.firstyear_plan_monitoring = first_year_plan_monitoring
            company_plan_monitoring_revision.secondyear_plan_monitoring = second_year_plan_monitoring
            company_plan_monitoring_revision.contract_usage_factor_offpeak = 1
            company_plan_monitoring_revision.contract_usage_factor_peak = 1
            company_plan_monitoring_revision.save()

        def update(monthly_plan_monitoring: MonthlyPlanMonitoring, monthly_budget_data: dict):
            for month in english_month_names:
                plan_monitoring: PlanMonitoring = getattr(
                    monthly_plan_monitoring, month)
                budget_data: dict = monthly_budget_data[month]

                plan_monitoring.estimated_peakpower_demand = budget_data[
                    'estimatedPeakPowerDemand']['value']
                if plan_monitoring.projected_peakpower_demand is None:
                    plan_monitoring.projected_peakpower_demand = plan_monitoring.estimated_peakpower_demand
                
                plan_monitoring.estimated_offpeak_power_demand = budget_data[
                    'estimatedOffPeakPowerDemand']['value']
                if plan_monitoring.projected_offpeak_power_demand is None:
                    plan_monitoring.projected_offpeak_power_demand = plan_monitoring.estimated_offpeak_power_demand
                
                plan_monitoring.estimated_peak_power_consumption = budget_data[
                    'consumptionPeakPowerDemand']['value']
                if plan_monitoring.projected_peak_power_consumption is None:
                    plan_monitoring.projected_peak_power_consumption = plan_monitoring.estimated_peak_power_consumption
                
                plan_monitoring.estimated_offpeak_power_consumption = budget_data[
                    'consumptionOffPeakPowerDemand']['value']
                if plan_monitoring.projected_offpeak_power_consumption is None:
                    plan_monitoring.projected_offpeak_power_consumption = plan_monitoring.estimated_offpeak_power_consumption
                
                plan_monitoring.estimated_production = budget_data['production']['value']
                if plan_monitoring.projected_production is None:
                    plan_monitoring.projected_production = plan_monitoring.estimated_production
                
                plan_monitoring.estimated_productive_stops = budget_data['productiveStops']['value']
                if plan_monitoring.projected_productive_stops is None:
                    plan_monitoring.projected_productive_stops = plan_monitoring.estimated_productive_stops

                if company_plan_monitoring.calculation_mode == CompanyPlanMonitoringCalculationMode.flat:
                    plan_monitoring.estimated_total_consumption = budget_data['totalConsumption']['value']
                    if plan_monitoring.projected_total_consumption is None:
                        plan_monitoring.projected_total_consumption = plan_monitoring.estimated_total_consumption

                plan_monitoring.save()

        company_plan_monitoring.calculation_mode = CompanyPlanMonitoringCalculationMode.modular \
            if budget_data["calculationMode"] == "Modular" \
            else CompanyPlanMonitoringCalculationMode.flat
        company_plan_monitoring.company_id = company
        company_plan_monitoring.year = year
        company_plan_monitoring.has_open_justification = False
        company_plan_monitoring.save()

        company_plan_monitoring_revision = company_plan_monitoring.companyplanmonitoringrevision_set.order_by(
            "-revision")[0]
        company_plan_monitoring_revision.contract_usage_factor_offpeak = budget_revision_data["contractUsageFactorOffpeak"]
        company_plan_monitoring_revision.contract_usage_factor_peak = budget_revision_data["contractUsageFactorPeak"]
        company_plan_monitoring_revision.save()

        update(company_plan_monitoring_revision.firstyear_plan_monitoring,
               budget_revision_data['firstYearBudget'])
        update(company_plan_monitoring_revision.secondyear_plan_monitoring,
               budget_revision_data['secondYearBudget'])

        transaction.savepoint_commit(trans_savepoint)
        return Response("ok")
    else:
        return Response({"erro": "Budget not found"}, status=status.HTTP_400_BAD_REQUEST)

def automatic_update_this_year_plan_monitoring(request: HttpRequest):
    years = [datetime.now().year]
    month = datetime.now().month

    if month == 1:
        years.append(years[0] - 1)
    elif month == 12:
        years.append(years[0] + 1)

    integration_service = IntegrationService()
    plan_monitoring_calculate_service = PlanMonitoringCalculateService()
    save_plan_monitoring_service = SavePlanMonitoringService(plan_monitoring_calculate_service, integration_service)

    user = request.user
    if not is_administrator(user):
        raise PermissionDenied()

    company_plan_monitorings: list[CompanyPlanMonitoring] = CompanyPlanMonitoring.objects.filter(year__in=years)
    result = {
        "updated": [],
        "notUpdated": []
    }

    for company_plan_monitoring in company_plan_monitorings:
        try:
            save_plan_monitoring_service.update_plan_monitoring(company_plan_monitoring, {}, "System", "Auto Update")

            result["updated"].append(company_plan_monitoring.id)
        except Exception as ex:
            error_id = uuid4()
            logging.error(f"Error while update company Plan Monitoring - error trace id ({error_id})",
                         exc_info=ex)
            result["notUpdated"].append({
                "id": company_plan_monitoring.id,
                "error": str(ex),
                "errorId": error_id
            })

    return Response(result, status=status.HTTP_200_OK)

@transaction.atomic
def create_all_plan_monitoring_from_budget(request: HttpRequest):
    year = datetime.now().year
    month = datetime.now().month

    if month == 12:
        year += 1

    english_month_names = []
    with different_locale('C.UTF-8'):
        english_month_names = list(map(lambda s: s.lower(), month_name))[1:]

    integration_service = IntegrationService()
    user = request.user
    if not is_administrator(user):
        raise PermissionDenied()

    budgets_data = integration_service.get_budgets_by_year(year)

    result = {
        "updated": [],
        "notUpdated": []
    }

    for budget_data in budgets_data:
        try:
            trans_savepoint = transaction.savepoint()
            if budget_data:
                budget_revision_data = budget_data['budgets'][0]

                company_plan_monitoring = CompanyPlanMonitoring.objects.filter(
                    company_id=budget_data["company"], year=year)[:1]
                if company_plan_monitoring:
                    company_plan_monitoring: CompanyPlanMonitoring = company_plan_monitoring[0]
                else:
                    company_plan_monitoring = CompanyPlanMonitoring()
                    company_plan_monitoring.year = year
                    company_plan_monitoring.company_id = budget_data["company"]
                    company_plan_monitoring.has_open_justification = False
                    company_plan_monitoring.calculation_mode = CompanyPlanMonitoringCalculationMode.modular
                    company_plan_monitoring.save()

                    first_year_plan_monitoring = MonthlyPlanMonitoring()

                    for month in english_month_names:
                        plan_monitoring = PlanMonitoring()
                        plan_monitoring.save()
                        setattr(first_year_plan_monitoring, month, plan_monitoring)

                    first_year_plan_monitoring.save()

                    second_year_plan_monitoring = MonthlyPlanMonitoring()

                    for month in english_month_names:
                        plan_monitoring = PlanMonitoring()
                        plan_monitoring.save()
                        setattr(second_year_plan_monitoring, month, plan_monitoring)

                    second_year_plan_monitoring.save()

                    company_plan_monitoring_revision = CompanyPlanMonitoringRevision()
                    company_plan_monitoring_revision.revision = 1
                    company_plan_monitoring_revision.company_plan_monitoring = company_plan_monitoring
                    company_plan_monitoring_revision.firstyear_plan_monitoring = first_year_plan_monitoring
                    company_plan_monitoring_revision.secondyear_plan_monitoring = second_year_plan_monitoring
                    company_plan_monitoring_revision.contract_usage_factor_offpeak = 1
                    company_plan_monitoring_revision.contract_usage_factor_peak = 1
                    company_plan_monitoring_revision.save()

                def update(monthly_plan_monitoring: MonthlyPlanMonitoring, monthly_budget_data: dict):
                    for month in english_month_names:
                        plan_monitoring: PlanMonitoring = getattr(
                            monthly_plan_monitoring, month)
                        budget_data: dict = monthly_budget_data[month]

                        plan_monitoring.estimated_peakpower_demand = budget_data[
                            'estimatedPeakPowerDemand']['value']
                        if plan_monitoring.projected_peakpower_demand is None:
                            plan_monitoring.projected_peakpower_demand = plan_monitoring.estimated_peakpower_demand
                        
                        plan_monitoring.estimated_offpeak_power_demand = budget_data[
                            'estimatedOffPeakPowerDemand']['value']
                        if plan_monitoring.projected_offpeak_power_demand is None:
                            plan_monitoring.projected_offpeak_power_demand = plan_monitoring.estimated_offpeak_power_demand
                        
                        plan_monitoring.estimated_peak_power_consumption = budget_data[
                            'consumptionPeakPowerDemand']['value']
                        if plan_monitoring.projected_peak_power_consumption is None:
                            plan_monitoring.projected_peak_power_consumption = plan_monitoring.estimated_peak_power_consumption
                        
                        plan_monitoring.estimated_offpeak_power_consumption = budget_data[
                            'consumptionOffPeakPowerDemand']['value']
                        if plan_monitoring.projected_offpeak_power_consumption is None:
                            plan_monitoring.projected_offpeak_power_consumption = plan_monitoring.estimated_offpeak_power_consumption
                        
                        plan_monitoring.estimated_production = budget_data['production']['value']
                        if plan_monitoring.projected_production is None:
                            plan_monitoring.projected_production = plan_monitoring.estimated_production
                        
                        plan_monitoring.estimated_productive_stops = budget_data['productiveStops']['value']
                        if plan_monitoring.projected_productive_stops is None:
                            plan_monitoring.projected_productive_stops = plan_monitoring.estimated_productive_stops

                        if company_plan_monitoring.calculation_mode == CompanyPlanMonitoringCalculationMode.flat:
                            plan_monitoring.estimated_total_consumption = budget_data['totalConsumption']['value']
                            if plan_monitoring.projected_total_consumption is None:
                                plan_monitoring.projected_total_consumption = plan_monitoring.estimated_total_consumption

                        plan_monitoring.save()

                company_plan_monitoring.calculation_mode = CompanyPlanMonitoringCalculationMode.modular \
                    if budget_data["calculationMode"] == "Modular" \
                    else CompanyPlanMonitoringCalculationMode.flat
                company_plan_monitoring.company_id = budget_data["company"]
                company_plan_monitoring.year = year
                company_plan_monitoring.has_open_justification = False
                company_plan_monitoring.save()

                company_plan_monitoring_revision = company_plan_monitoring.companyplanmonitoringrevision_set.order_by(
                    "-revision")[0]
                company_plan_monitoring_revision.contract_usage_factor_offpeak = budget_revision_data["contractUsageFactorOffpeak"]
                company_plan_monitoring_revision.contract_usage_factor_peak = budget_revision_data["contractUsageFactorPeak"]
                company_plan_monitoring_revision.save()

                update(company_plan_monitoring_revision.firstyear_plan_monitoring,
                    budget_revision_data['firstYearBudget'])
                update(company_plan_monitoring_revision.secondyear_plan_monitoring,
                    budget_revision_data['secondYearBudget'])

                transaction.savepoint_commit(trans_savepoint)

                result["updated"].append(budget_data["company"])
        except Exception as ex:
            error_id = uuid4()
            logging.error(f"Error while create/update company Plan Monitoring from budget - error trace id ({error_id})",
                         exc_info=ex)
            result["notUpdated"].append({
                "company_id": budget_data["company"],
                "error": str(ex),
                "errorId": error_id
            })
            
    return Response(result, status=status.HTTP_200_OK)
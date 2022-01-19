from SmartEnergy.utils.request.http_request_handling import http_method_handling

from django.urls import path

from . import views

urlpatterns = [
    path('occurrence', http_method_handling(
        get=views.get_occurrence_list,
        post=views.save_occurrence)),
    path('occurrence/<int:pk>', http_method_handling(
        get=views.get_occurrence,
        put=views.save_occurrence)),
    path('occurrence/event', http_method_handling(
        get=views.get_event_list)),
    path('occurrence/<int:occurrence_id>/attachment', http_method_handling(
        get=views.get_occurence_attachment_list,
        post=views.post_occurence_attachment)),
    path('occurrence/report', http_method_handling(
        get=views.get_occurrence_report)),
    path('occurrence/<int:pk>/log', http_method_handling(
        get=views.get_occurrence_log)),
    path('occurrence/company/withSEPP', http_method_handling(
        get=views.get_company_list_with_participation_sepp)),
    path('occurrence/cause', http_method_handling(
        get=views.get_occurrence_cause_list)),
    path('occurrence/type', http_method_handling(
        get=views.get_occurrence_type_list)),
    path('occurrence/appliedProtection', http_method_handling(
        get=views.get_applied_protection_list)),
    path('occurrence/event/type', http_method_handling(
        get=views.get_event_type_list)),  # ok
    path('occurrence/event/validBusiness', http_method_handling(
        get=views.get_valids_business_list)),  # ok
    path('occurrence/dashboard', http_method_handling(
        post=views.get_occurrence_dashboard))
]

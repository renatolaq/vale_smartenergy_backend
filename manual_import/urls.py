from django.urls import include, path
from django.contrib.staticfiles.urls import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from SmartEnergy import settings
from .views import UploadFileViewSet

from manual_import import views as view_ima


from rest_framework import routers
router = routers.DefaultRouter()
router.register('upload-list', UploadFileViewSet)

urlpatterns = [
    # path('api-core/manual-import/', UploadFileView.as_view(), name='uploads_list'),
    path('manual_import/', include(router.urls)),
    path('manual_import/get_ima_erro_log/<int:pk>/', view_ima.get_ima_erro_log),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

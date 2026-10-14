"""
URL configuration for factory_ops project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # 4 Core Modules
    path('', include('master_setup.urls')),             # Module 1 & Plant Dashboard
    path('calibration/', include('calibration.urls')),  # Module 2: Calibration & Workstation Lock
    path('materials/', include('material_intake.urls')),# Module 3: Raw Material Intake & MTC
    path('inspection/', include('inspection.urls')),    # Module 4: PDI & Measurement Validation
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

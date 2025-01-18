from django.urls import path

from .views import *


urlpatterns = [
    path("", ParserView.as_view(), name="parser"),
    path("delete_dublicate", delete_dublicate, name="del_dubl"),
    path("test_work_with_db", test_work_with_db, name="test_work_with_db"),
    path('download/<str:file_name>/', download_file, name='download_file'),
    path('all_data_to_calendar', all_data_to_calendar, name='all_data_to_calendar'),
    path('delete_sites_with_status_good_none', delete_sites_with_status_good_none, name='delete_sites_with_status_good_none'),
]
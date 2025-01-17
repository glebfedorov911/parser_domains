from django.urls import path

from .views import *


urlpatterns = [
    path("", ParserView.as_view(), name="parser"),
    path("delete_dublicate", delete_dublicate, name="del_dubl"),
]
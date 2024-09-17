from django.urls import path

from .views import *


urlpatterns = [
    path("", ParserView.as_view(), name="parser")
]
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import TemplateView
from django.core.cache import cache

from .forms import FileForm, DateForm
from .models import FileModel, DateModel
from .parser import parser, data_from_file, split_file
from siteparsershops.settings import MEDIA_ROOT

import re
import threading
import multiprocessing


#uvicorn siteparsershops.asgi:application --host 127.0.0.1 --port 8000

class ParserView(TemplateView):
    template_name = "parser/index.html"
    form_file = FileForm
    form_date = DateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lastdate = lastdate = DateModel.objects.all().order_by("-id")

        context["title"] = "Парсер доменов"
        context["form_file"] = self.form_file
        context["form_date"] = self.form_date
        context["date"] = lastdate[0] if len(lastdate) != 0 else ""
        return context

    def get(self, request):
        if self.request.GET.get('start') == "True":
            files = FileModel.objects.all().order_by("-id")
            if len(files) == 0:
                raise HttpResponse("<h1>Файл не загружен</h1> <br> <a href=''>Вернуться на главную страницу</a>")
            # try:
            all_data = data_from_file(f"{MEDIA_ROOT}/{files[0].file}")
            cache.set("count_data", len(all_data))
            all_data = split_file(16, all_data)
            for num in range(len(all_data)):
                thr = multiprocessing.Process(target=parser, args=(all_data[num], ))
                thr.start()
            cache.set("start_parser", True)

            # except:
            #     HttpResponse("<h1>Ошибка файла</h1> <br> <a href=''>Вернуться на главную страницу</a>")
            return redirect(reverse("parser"))
        return render(request, self.template_name, context=self.get_context_data())

    def post(self, request, *args, **kwargs):
        if not self.request.FILES.get("file", None) is None:
            file = self.request.FILES.get("file")
            if str(file).split(".")[-1] not in ('csv', ):
                return HttpResponse("<h1>Данный формат файла не поддерживается</h1> <br> <a href=''>Вернуться на главную страницу</a>")
            save_data = FileModel.objects.create(file=file)
            save_data.save()
        
        if not self.request.POST.get("date", None) is None:
            date = self.request.POST.get("date")
            if date == "" or not self.check_format(date):
                return HttpResponse("<h1>Плохой формат даты</h1> <br> <a href=''>Вернуться на главную страницу</a>")
            save_data = DateModel.objects.create(date=date)
            save_data.save()

        return redirect(reverse("parser"))
    
    def check_format(self, date):
        frmt = r"\d{2}.\d{2}.\d{4}-\d{2}.\d{2}.\d{4}"
        return len(re.findall(frmt, date)) != 0
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.views.generic import TemplateView
from django.core.cache import cache
from django.core.paginator import Paginator

from .forms import FileForm, DateForm, ShablonForm, CheckBoxForm
from .models import FileModel, DateModel, StatisticsModel, ShowDataModel, AgainDataModel, AgainShablonModel, DeleteShablonModel
from .parser import parser, data_from_file, split_file
from .settings import MEDIA_ROOT

import re
import threading
import multiprocessing


#uvicorn siteparsershops.asgi:application --host 127.0.0.1 --port 8000

class ParserView(TemplateView):
    template_name = "parser/index.html"
    form_file = FileForm
    form_date = DateForm
    form_shablon = ShablonForm
    form_checkbox = CheckBoxForm
    _is_start_parser = False


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lastdate = DateModel.objects.all().order_by("-id")
        lastfile = FileModel.objects.all().order_by("-id")

        context["title"] = "Парсер доменов"
        context["form_file"] = self.form_file
        context["form_date"] = self.form_date
        context["form_shablon"] = self.form_shablon
        context["form_checkbox"] = self.form_checkbox
        context["date"] = lastdate[0] if len(lastdate) != 0 else ""
        if len(lastfile) != 0:
            # context["showdata"] = ShowDataModel.objects.filter(file_id=lastfile[0].pk)
            showdata = ShowDataModel.objects.filter(file_id=lastfile[0].pk)
            paginator = Paginator(showdata, 10)
            
            page_number = self.request.GET.get("page")
            page_obj = paginator.get_page(page_number)

            context["showdata"] = page_obj
            
            stats = StatisticsModel.objects.filter(file_id=lastfile[0].pk).order_by("-id")
            if stats:
                context["stats"] = stats[0]

        return context

    def start_parser(self, all_data, delete, shablon):
        self._is_start_parser = True
        shared_data = multiprocessing.Manager().list([{} for _ in range(len(all_data))])
        processes = []
        for num in range(len(all_data)):
            process = multiprocessing.Process(target=parser, args=(all_data[num], shared_data, num, delete, shablon))
            process.start()
            processes.append(process)
        for process in processes:
            process.join()

        return list(shared_data)

    def get_url(self):
        url = reverse("parser")
        url_redirect = f"{url}?page={self.request.GET.get("page")}"
        return url_redirect

    def get(self, request):
        if (self.request.GET.get('start') == "True" or self.request.GET.get('again') == "True") and not self._is_start_parser:
            # try:
            if self.request.GET.get('again') == "True":
                files = AgainDataModel.objects.all()
                all_data = [eval(file.domain) for file in files]
            else:
                files = FileModel.objects.all().order_by("-id")
                all_data = data_from_file(f"{MEDIA_ROOT}/{files[0].file}")

            delete = [delete.code for delete in DeleteShablonModel.objects.all()]
            shablon = [again.code for again in AgainShablonModel.objects.all()]

            all_data = split_file(16, all_data)
            
            res = self.start_parser(all_data, delete, shablon)
            good = bad = check_again = 0
            again_domain = []
            data = []

            if self.request.GET.get('again') == "True":
                files = AgainDataModel.objects.all().delete()
                files = FileModel.objects.all().order_by("-id")

            for r in res:
                again_domain += r["again_domain"]
                good += r["good"]
                check_again += r["check_again"]
                bad += r["bad"]
                data += [(i, r["data"][i]) for i in r["data"]]

            StatisticsModel.objects.create(good=good, bad=bad, check_again=check_again, file=files[0]).save()
            for row in data:
                ShowDataModel.objects.create(domain=row[0], phone=row[1]["phone"], email=row[1]["email"], inn=row[1]["inn"],
                                            ooo=row[1]["ooo"], ip=row[1]["individual"], file=files[0]).save()
            for row in again_domain:
                AgainDataModel.objects.create(domain=row)
            
            self._is_start_parser = False   
            url_redirect = self.get_url()

            return HttpResponseRedirect(url_redirect)
            # except:
            #     return HttpResponse("<h1>Файл не загружен либо загружен неправильно</h1> <br> <a href=''>Вернуться на главную страницу</a>")
        return render(request, self.template_name, context=self.get_context_data())

    def post(self, request, *args, **kwargs):
        print(self.request.POST)
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

        if self.request.POST.get("select") == "DELETE":
            delete = DeleteShablonModel.objects.create(code=self.request.POST.get("code"))
            delete.save()

        if self.request.POST.get("select") == "CHECK":
           again = AgainShablonModel.objects.create(code=self.request.POST.get("code"))
           again.save()
        
        if not self.request.POST.get("id", None) is None:
            data = ShowDataModel.objects.get(id=self.request.POST.get("id"))
            if not self.request.POST.get("is_check", None) is None:
                data.is_check = True
            else:
                data.is_check = False
            data.save(update_fields=["is_check"])
        
        url_redirect = self.get_url()

        return HttpResponseRedirect(url_redirect)

    
    def check_format(self, date):
        frmt = r"\d{2}.\d{2}.\d{4}-\d{2}.\d{2}.\d{4}"
        return len(re.findall(frmt, date)) != 0
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from django.template.loader import render_to_string
from django.views.generic import TemplateView
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q, Count, Min
from django.db import connection

from .forms import FileForm, DateForm, ShablonForm, CheckBoxForm
from .models import (
    FileModel, DateModel, StatisticsModel,
    AgainShablonModel, DeleteShablonModel, UploadDataModel,
    DateForCalendar
)
from .parser import parser, data_from_file, split_file
from siteparsershops.settings import MEDIA_ROOT

import re
import threading
import json
import multiprocessing
import os


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

        context.update({
            "title": "Парсер доменов",
            "form_file": self.form_file,
            "form_date": self.form_date,
            "form_shablon": self.form_shablon,
            "form_checkbox": self.form_checkbox,
            "is_start_parser": self._is_start_parser,
            "date_in_parser_with_nth_status": ','.join(list({date.date for date in DateForCalendar.objects.filter(status='NTH')})),
            "date_in_parser_already_parse": ','.join(list({date.date for date in DateForCalendar.objects.filter(~Q(status='NTH'))})),
            "showdata": self.get_paginated_data(),
            "type_check": self.get_type(),
            **self.get_statistics(),
        })

        return context

    def get_paginated_data(self):
        showdata = self.get_data_by_type()
        paginator = Paginator(showdata, 50)
        page_number = self.request.GET.get("page", 1)
        return paginator.get_page(page_number)

    def get_data_by_type(self):
        _type = self.request.GET.get("type_check")
        if _type == "NOTSHOW":
            return UploadDataModel.objects.filter(is_showing=False, status="GOOD", status_good=None).order_by('id')
        return UploadDataModel.objects.filter(is_showing=True, status="GOOD").order_by('id')

    def get_type(self):
        return self.request.GET.get("type_check", None)

    def get_statistics(self):
        stats_full = StatisticsModel.objects.filter(status="FULL").order_by("-id").first()
        stats_again = StatisticsModel.objects.filter(status="AGAINDATA").order_by("-id").first()
        check = UploadDataModel.objects.all()
        count_data = {
            "count_check_shop_store": sum(1 for data in check if 'shop' in data.domain.lower() or 'store' in data.domain.lower()),
            "count_check_good": sum(1 for data in check if data.status == 'GOOD'),
            "count_check_bad": sum(1 for data in check if data.status == 'BAD'),
            "count_check_again": sum(1 for data in check if data.status == 'AGAIN'),
            "count_check": len(check),
        }
        return {
            "stats_full": stats_full,
            "stats_again": stats_again,
            **count_data,
        }

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
        url_redirect = f"{url}?page={self.request.GET.get('page')}&type_check={self.request.GET.get('type_check')}"
        return url_redirect

    def get_data_with_status(self):
        if self.request.GET.get('again', None) == "True":
            return UploadDataModel.objects.filter(status="AGAIN")
        elif self.request.GET.get('check_good_again', None) == "True":
            return UploadDataModel.objects.filter(status="GOOD", is_showing=True)
        return UploadDataModel.objects.filter(status="NTH")

    def get_delete_again(self):
        if self.request.GET.get('again', None) == "True":
            delete_again = UploadDataModel.objects.filter(status="AGAIN")
        elif self.request.GET.get('check_good_again', None) == "True":
            delete_again = UploadDataModel.objects.filter(status="GOOD", is_showing=True)
        return None
    
    def save_statistic(self, good, bad, check_again, count_shop_store_domains, count_all_domains, status):
        StatisticsModel.objects.create(good=good, bad=bad, check_again=check_again, count_shop_store_domains=count_shop_store_domains, 
            count_domains=count_all_domains, status=status).save()
        
    def save_good(self, data_from_parser):
        upload = [
            UploadDataModel(domain=row[0], date=row[1]["date"], domain_for_parsing = [row[1]["date"], row[0]], phone='\n'.join(row[1]["phone"]), email='\n'.join(row[1]["email"]), inn='\n'.join(row[1]["inn"]),
                                            ooo='\n'.join(row[1]["ooo"]), ip='\n'.join(row[1]["individual"]), it_was_good=True, is_showing=True, status="GOOD")
            if any([row[1][r] != [] for r in row[1] if r != "date"]) else 
            UploadDataModel(domain=row[0], date=row[1]["date"], domain_for_parsing = [row[1]["date"], row[0]], phone='\n'.join(row[1]["phone"]), email='\n'.join(row[1]["email"]), inn='\n'.join(row[1]["inn"]),
                                            ooo='\n'.join(row[1]["ooo"]), ip='\n'.join(row[1]["individual"]), it_was_good=True, is_showing=False, status="GOOD")
            for row in data_from_parser 
        ]
        return upload
    
    def save_date(self, data_from_parser):
        all_data = [i[0] for i in data_from_parser]
        date = self.create_collection_with_skip_dates(all_data=all_data, status="SCF") 
        date = self.delete_skip(date)
        self.delete_all_date(all_data)
        self.bulk_create_data_for_calendare(data=date)

    def delete_all_date(self, all_data) -> None:
        date = self.get_data_from_all_data(all_data=all_data)
        DateForCalendar.objects.filter(date__in=date, status="NTH").delete()
    
    def save_another_list(self, rows, status):
        upload = [
            UploadDataModel(domain=row[1], date=row[0], domain_for_parsing = [row[0], row[1]], is_showing=False, status=status)
            for row in rows
        ]
        
        return upload

    def save_bulk_create(self, upload):
        UploadDataModel.objects.bulk_create(upload)

    def from_parser_date(self, res):
        good = bad = check_again = count_shop_store_domains = 0
        again_domain = []
        data_from_parser = []
        bad_list = []

        for r in res:
            again_domain += r["again_domain"]
            good += r["good"]
            check_again += r["check_again"]
            bad += r["bad"]
            count_shop_store_domains += r["count_shop_store_domains"]
            data_from_parser += [(i, r["data"][i]) for i in r["data"]]
            bad_list += r["bad_list"]
        
        return good, bad, check_again, again_domain, bad_list, count_shop_store_domains, data_from_parser

    def handler_upload_file(self, request):
        file = request.FILES.get("file")
        if not file.name.endswith('.csv'):
            return HttpResponse("<h1>Данный формат файла не поддерживается</h1> <br> <a href='/parser/'>Вернуться на главную страницу</a>")
        save_data = FileModel.objects.create(file=file)
        save_data.save()

        all_data = data_from_file(f"{MEDIA_ROOT}/{save_data.file}")
        domains = [
            UploadDataModel(date=row[0], domain_for_parsing=row, domain=row[1], status="NTH")
            for row in all_data
        ]
        date = self.create_collection_with_skip_dates(all_data=all_data) 
        date = self.delete_skip(date)
        self.bulk_create_data_for_calendare(data=date)

        self.save_bulk_create(domains)

        date = f"{all_data[0][0]}-{all_data[-1][0]}"
        save_data = DateModel.objects.create(date=date)
        save_data.save()

    def create_collection_with_skip_dates(self, all_data, status="NTH") -> list:
        return [
            "skip" if self.get_date_for_calendar_data(date=date, status=status) else DateForCalendar(date=date, status=status) 
            for date in self.get_data_from_all_data(all_data=all_data) 
        ]

    def get_data_from_all_data(self, all_data) -> set:
        return {row[0] for row in all_data} 

    def get_date_for_calendar_data(self, date, status="NTH") -> list[DateForCalendar]:
        return DateForCalendar.objects.filter(date=date, status=status)
    
    def delete_skip(self, date: list) -> list:
        return [
            d for d in date if d != 'skip'
        ] 
    
    def bulk_create_data_for_calendare(self, data: list) -> None:
        DateForCalendar.objects.bulk_create(data)

    def save_shablon(self, obj, code):
        delete = obj.objects.create(code=code)
        delete.save()

    def save_status(self, id_domain, status="GOOD", status_good=None, is_showing=False):
        try:
            query_domain = UploadDataModel.objects.get(id=int(id_domain))
            query_domain.status = status
            query_domain.status_good = status_good
            query_domain.is_showing = is_showing

            query_domain.save()
        except Exception as e:
            print(e)

    def get(self, request):
        start = self.request.GET.get('start', None) == "True"
        again = self.request.GET.get('again', None) == "True"
        check_good_again = self.request.GET.get('check_good_again', None) == "True"
        if (start or again or check_good_again) and not self._is_start_parser:
            try:
                data = self.get_data_with_status()
                all_data = [eval(string.domain_for_parsing) for string in data]

                delete = [delete.code for delete in DeleteShablonModel.objects.all()]
                shablon = [again.code for again in AgainShablonModel.objects.all()]
                print(delete)
                print(shablon)

                count_all_domains = len(all_data)
                if len(all_data) < 16:
                    all_data = split_file(len(all_data) if len(all_data) != 0 else 1, all_data)
                else:
                    all_data = split_file(16, all_data)

                res = self.start_parser(all_data, delete, shablon)

                delete_again = self.get_delete_again()
                data.delete()
                if delete_again:
                    delete_again.delete()

                good, bad, check_again, again_domain, bad_list, count_shop_store_domains, data_from_parser = self.from_parser_date(res)
                data_for_saving = {"good": good, "bad": bad, "check_again": check_again, "count_shop_store_domains": count_shop_store_domains,
                                   "count_all_domains": count_all_domains}
                if self.request.GET.get('again', None) == "True" or self.request.GET.get('check_good_again', None) == "True":
                    self.save_statistic(**data_for_saving, status="AGAINDATA")
                else:
                    self.save_statistic(**data_for_saving, status="FULL")

                upload = self.save_good(data_from_parser=data_from_parser)
                self.save_bulk_create(upload)

                upload = self.save_another_list(rows=again_domain, status="AGAIN")
                self.save_bulk_create(upload)

                self.save_date(data_from_parser=all_data)

                upload = self.save_another_list(rows=bad_list, status="BAD")
                self.save_bulk_create(upload)

                self._is_start_parser = False   
                
                url_redirect = self.get_url()
                
                return HttpResponseRedirect(url_redirect)

            except Exception as e:
                print(e)
                return HttpResponse("""<h1>Файл не загружен либо загружен неправильно</h1> <br> <a href='/parser/'>Вернуться на главную страницу</a>""")
        return render(request, self.template_name, context=self.get_context_data())

    def post(self, request, *args, **kwargs):
        if not self.request.FILES.get("file", None) is None:
            self.handler_upload_file(request=request)

        if self.request.POST.get("select") == "DELETE":
            self.save_shablon(DeleteShablonModel, self.request.POST.get("code"))

        if self.request.POST.get("select") == "CHECK":
            self.save_shablon(AgainShablonModel, self.request.POST.get("code"))

        if self.request.POST.get("check_again_ids") != '' and not self.request.POST.get("check_again_ids") is None:
            for id_domain in self.request.POST.get("check_again_ids").split(","):
                self.save_status(id_domain=id_domain, status="AGAIN", is_showing=False)

        if self.request.POST.get("is_check_ids") != '' and not self.request.POST.get("is_check_ids") is None and self.request.POST.get("is_check_ids") != {}:
            is_check_ids = eval(self.request.POST.get("is_check_ids"))
            for id_domain in is_check_ids:
                self.save_status(id_domain=id_domain, status_good=is_check_ids[id_domain], is_showing=False)

        if self.request.POST.get("del_self_ids") != '' and not self.request.POST.get("del_self_ids") is None:
            for id_domain in self.request.POST.get("del_self_ids").split(","):
                self.save_status(id_domain=id_domain, status="DEL", is_showing=False)

        url_redirect = self.get_url()

        return HttpResponseRedirect(url_redirect)

def page_not_found(request, exception):
    print(exception)
    return HttpResponse("<h1>Такой страницы не существует =)</h1> <br> <a href='/parser/'>Перейти на главную страницу</a>")

def delete_dublicate(request):
    dublicates = UploadDataModel.objects.values('domain').annotate(name_count=Count('domain')).filter(name_count__gt=1)

    for dublicate in dublicates:
        duplicates_queryset = UploadDataModel.objects.filter(domain=dublicate['domain'])
        
        with_status = duplicates_queryset.filter(~Q(status_good=None))
        
        if with_status.exists():
            to_keep = with_status.order_by('id').first()
        else:
            to_keep = duplicates_queryset.order_by('id').first()

        duplicates_queryset.exclude(id=to_keep.id).delete()

    return HttpResponse('Good')

def test_work_with_db(request):
    try:
        data = [
            UploadDataModel.objects.filter(is_showing=True, status="GOOD")[:200],
            UploadDataModel.objects.filter(is_showing=True, status="BAD")[:200],
            UploadDataModel.objects.filter(is_showing=True, status="AGAIN")[:200],
            UploadDataModel.objects.filter(is_showing=True, status="NTH")[:200],
            UploadDataModel.objects.filter(is_showing=True, status="DEL")[:200],
            UploadDataModel.objects.filter(is_showing=False, status="GOOD")[:200],
            UploadDataModel.objects.filter(is_showing=False, status="BAD")[:200],
            UploadDataModel.objects.filter(is_showing=False, status="AGAIN")[:200],
            UploadDataModel.objects.filter(is_showing=False, status="NTH")[:200],
            UploadDataModel.objects.filter(is_showing=False, status="DEL")[:200],
            UploadDataModel.objects.filter(is_showing=True, status="GOOD", status_good=None)[:200],
            UploadDataModel.objects.filter(is_showing=True, status="GOOD", status_good="TAKE")[:200],
            UploadDataModel.objects.filter(is_showing=True, status="GOOD", status_good="ALREADY")[:200],
            UploadDataModel.objects.filter(is_showing=True, status="GOOD", status_good="NOTNEED")[:200],
            UploadDataModel.objects.filter(is_showing=True, status="GOOD", status_good="DOESNOT")[:200],
            UploadDataModel.objects.filter(is_showing=False, status="GOOD", status_good=None)[:200],
            UploadDataModel.objects.filter(is_showing=False, status="GOOD", status_good="TAKE")[:200],
            UploadDataModel.objects.filter(is_showing=False, status="GOOD", status_good="ALREADY")[:200],
            UploadDataModel.objects.filter(is_showing=False, status="GOOD", status_good="NOTNEED")[:200],
            UploadDataModel.objects.filter(is_showing=False, status="GOOD", status_good="DOESNOT")[:200],
        ]

        if os.path.exists(r'data1.txt'):
            os.remove(r'data1.txt')
        with open(r'data1.txt', 'a') as file:
            for i in data:
                for j in i:
                    tabulation_data = f"Дата: {j.date}\tДомен для парсинга: {j.domain_for_parsing}\tДомен: {j.domain}\tТелефон: {j.phone}\tПочта: {j.email}\tИНН: {j.inn}\tООО: {j.ooo}\tИП: {j.ip}\tПроверено: {j.is_check}\tПоказывать: {j.is_showing}\tБыл успешно спаршен: {j.it_was_good}\tСтатус парсинга: {j.status}\tСтатус успешного: {j.status_good}\t"
                    file.write('-='*20+'\n')
                    file.write(tabulation_data)
                    file.write('\n')
                    file.write('-='*20+'\n')
        print("готово")
        return HttpResponse("kaif")
    except Exception as e:
        print(e)


def download_file(request, file_name):
    if not os.path.exists(file_name):
        return HttpResponse("Файл не найден.")

    response = FileResponse(open(file_name, 'rb'), as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response

def all_data_to_calendar(request):
    upload = UploadDataModel.objects.all()
    dates = {up.date for up in upload}
    date = [
        DateForCalendar(date=d, status='SCF')
        for d in dates
    ]
    DateForCalendar.objects.bulk_create(date)
    return HttpResponse('success')

def check_count_status_good(request):
    print("None", len(UploadDataModel.objects.filter(status_good=None)))
    print("not None", len(UploadDataModel.objects.filter(~Q(status_good=None))))

    return HttpResponse('success')
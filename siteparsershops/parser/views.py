from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.views.generic import TemplateView
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q

from .forms import FileForm, DateForm, ShablonForm, CheckBoxForm
from .models import FileModel, DateModel, StatisticsModel, AgainShablonModel, DeleteShablonModel, UploadDataModel
from .parser import parser, data_from_file, split_file
from siteparsershops.settings import MEDIA_ROOT

import re
import threading
import json
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
        context["is_start_parser"] = self._is_start_parser
        context["date"] = lastdate[0] if len(lastdate) != 0 else ""
        if len(lastfile) != 0:
            # context["showdata"] = ShowDataModel.objects.filter(file_id=lastfile[0].pk)
            showdata = UploadDataModel.objects.filter(is_showing=True, status="GOOD")
            context["date_in_parser_with_nth_status"] = ','.join(list({date.date for date in UploadDataModel.objects.filter(status='NTH')}))
            context["date_in_parser_already_parse"] = ','.join(list({date.date for date in UploadDataModel.objects.filter(~Q(status='NTH'))}))
            paginator = Paginator(showdata, 50)
            
            page_number = self.request.GET.get("page", None)
            page_obj = paginator.get_page(page_number)

            context["showdata"] = page_obj
            
            stats_full = StatisticsModel.objects.filter(status="FULL").order_by("-id")
            stats_again = StatisticsModel.objects.filter(status="AGAINDATA").order_by("-id")
            check = UploadDataModel.objects.all()
            check_shop_store = [data for data in check if 'shop' in data.domain.lower() or 'store' in data.domain.lower()]
            check_good = [data for data in check if data.status == 'GOOD']
            check_bad = [data for data in check if data.status == 'BAD']
            check_again= [data for data in check if data.status == 'AGAIN']
            if stats_full:
                context["stats_full"] = stats_full[0]
            if stats_again:
                context["stats_again"] = stats_again[0]
            context['count_check_shop_store'] = len(check_shop_store) if check else 0
            context['count_check_good'] = len(check_good) if check else 0
            context['count_check_bad'] = len(check_bad) if check else 0
            context['count_check_again'] = len(check_again) if check else 0
            context['count_check'] = len(check) if check else 0

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
        if (self.request.GET.get('start', None) == "True" or self.request.GET.get('again', None) == "True" or self.request.GET.get('check_good_again', None) == "True") and not self._is_start_parser:
            try:
                if self.request.GET.get('again', None) == "True":
                    data = UploadDataModel.objects.filter(status="AGAIN")
                elif self.request.GET.get('check_good_again', None) == "True":
                    data = UploadDataModel.objects.filter(status="GOOD", is_showing=True)
                else:
                    data = UploadDataModel.objects.filter(status="NTH")
                
                all_data = [eval(string.domain_for_parsing) for string in data]

                delete = [delete.code for delete in DeleteShablonModel.objects.all()]
                shablon = [again.code for again in AgainShablonModel.objects.all()]

                count_all_domains = len(all_data)

                if len(all_data) < 16:
                    all_data = split_file(len(all_data) if len(all_data) != 0 else 1, all_data)
                else:
                    all_data = split_file(16, all_data)
                res = self.start_parser(all_data, delete, shablon)
                good = bad = check_again = count_shop_store_domains = 0
                again_domain = []
                data_from_parser = []
                bad_list = []
                delete_again = None
                if self.request.GET.get('again', None) == "True":
                    delete_again = UploadDataModel.objects.filter(status="AGAIN")
                elif self.request.GET.get('check_good_again', None) == "True":
                    delete_again = UploadDataModel.objects.filter(status="GOOD", is_showing=True)

                data.delete()
                if delete_again:
                    delete_again.delete()

                for r in res:
                    again_domain += r["again_domain"]
                    good += r["good"]
                    check_again += r["check_again"]
                    bad += r["bad"]
                    count_shop_store_domains += r["count_shop_store_domains"]
                    data_from_parser += [(i, r["data"][i]) for i in r["data"]]
                    bad_list += r["bad_list"]
                print('1')
                if self.request.GET.get('again', None) == "True" or self.request.GET.get('check_good_again', None) == "True":
                    StatisticsModel.objects.create(good=good, bad=bad, check_again=check_again, count_shop_store_domains=count_shop_store_domains, 
                        count_domains=count_all_domains, status="AGAINDATA").save()
                else:
                    StatisticsModel.objects.create(good=good, bad=bad, check_again=check_again, count_shop_store_domains=count_shop_store_domains, 
                        count_domains=count_all_domains, status="FULL").save()
                print('2')
                upload = [
                    UploadDataModel(domain=row[0], date=row[1]["date"], domain_for_parsing = [row[1]["date"], row[0]], phone='\n'.join(row[1]["phone"]), email='\n'.join(row[1]["email"]), inn='\n'.join(row[1]["inn"]),
                                                    ooo='\n'.join(row[1]["ooo"]), ip='\n'.join(row[1]["individual"]), is_showing=True, status="GOOD")
                    if any([row[1][r] != [] for r in row[1] if r != "date"]) else 
                    UploadDataModel(domain=row[0], date=row[1]["date"], domain_for_parsing = [row[1]["date"], row[0]], phone='\n'.join(row[1]["phone"]), email='\n'.join(row[1]["email"]), inn='\n'.join(row[1]["inn"]),
                                                    ooo='\n'.join(row[1]["ooo"]), ip='\n'.join(row[1]["individual"]), is_showing=False, status="GOOD")
                    for row in data_from_parser 
                ]
                print('3')
                UploadDataModel.objects.bulk_create(upload)

                upload = [
                    UploadDataModel(domain=row[1], date=row[0], domain_for_parsing = [row[0], row[1]], is_showing=False, status="AGAIN")
                    for row in again_domain
                ]
                print('4')
                    # AgainDataModel.objects.create(domain=row)
                UploadDataModel.objects.bulk_create(upload)

                upload = [
                    UploadDataModel(domain=row[1], date=row[0], domain_for_parsing = [row[0], row[1]], is_showing=False, status="BAD")
                    for row in bad_list
                ]
                print('5')
                UploadDataModel.objects.bulk_create(upload)


                self._is_start_parser = False   
                
                url_redirect = self.get_url()
                
                return HttpResponseRedirect(url_redirect)

            except Exception as e:
                print(e)
                return HttpResponse("""<h1>Файл не загружен либо загружен неправильно</h1> <br> <a href='/parser'>Вернуться на главную страницу</a>""")
        return render(request, self.template_name, context=self.get_context_data())

    def post(self, request, *args, **kwargs):
        if not self.request.FILES.get("file", None) is None:
            file = self.request.FILES.get("file")
            if str(file).split(".")[-1] not in ('csv', ):
                return HttpResponse("<h1>Данный формат файла не поддерживается</h1> <br> <a href='/parser'>Вернуться на главную страницу</a>")
            save_data = FileModel.objects.create(file=file)
            save_data.save()

            all_data = data_from_file(f"{MEDIA_ROOT}/{save_data.file}")

            domains = [
                UploadDataModel(date=row[0], domain_for_parsing=row, domain=row[1], status="NTH")
                for row in all_data
            ]

            UploadDataModel.objects.bulk_create(domains)

            date = f"{all_data[0][0]}-{all_data[-1][0]}"
            save_data = DateModel.objects.create(date=date)
            save_data.save()
        
        # if not self.request.POST.get("date", None) is None:
        #     date = self.request.POST.get("date")
        #     if date == "" or not self.check_format(date):
        #         return HttpResponse("<h1>Плохой формат даты</h1> \n <a href='/parser'>Вернуться на главную страницу</a>")
        #     save_data = DateModel.objects.create(date=date)
        #     save_data.save()

        if self.request.POST.get("select") == "DELETE":
            delete = DeleteShablonModel.objects.create(code=self.request.POST.get("code"))
            delete.save()

        if self.request.POST.get("select") == "CHECK":
           again = AgainShablonModel.objects.create(code=self.request.POST.get("code"))
           again.save()

        if self.request.POST.get("check_again_ids") != '' and not self.request.POST.get("check_again_ids") is None:
            for id_domain in self.request.POST.get("check_again_ids").split(","):
                query_domain = UploadDataModel.objects.get(id=int(id_domain))
                # domain = ["", query_domain.domain]
                query_domain.status = "AGAIN"
                query_domain.save()
                # query_domain.delete()
                # AgainDataModel.objects.create(domain=domain).save()

        if self.request.POST.get("is_check_ids") != '' and not self.request.POST.get("is_check_ids") is None and self.request.POST.get("is_check_ids") != {}:
            is_check_ids = eval(self.request.POST.get("is_check_ids"))
            for id_domain in is_check_ids:
                show = UploadDataModel.objects.get(id=int(id_domain))
                show.is_showing = False
                show.status_good = is_check_ids[id_domain]
                show.save()
            # for id_domain in self.request.POST.get("is_check_ids").split(","):
            #     try:
            #         # show = ShowDataModel.objects.get(id=int(id_domain))
            #         show = UploadDataModel.objects.get(id=int(id_domain))
            #         show.is_showing = False
            #         show.save()
            #     except:
            #         pass

        if self.request.POST.get("del_self_ids") != '' and not self.request.POST.get("del_self_ids") is None:
            for id_domain in self.request.POST.get("del_self_ids").split(","):
                try:
                    # show = ShowDataModel.objects.get(id=int(id_domain))
                    show = UploadDataModel.objects.get(id=int(id_domain))
                    show.is_showing = False
                    show.status = "DEL"
                    show.save()
                except:
                    pass

        # if not self.request.POST.get("id", None) is None:
        #     data = ShowDataModel.objects.get(id=self.request.POST.get("id"))
        #     if not self.request.POST.get("is_check", None) is None:
        #         data.is_check = True
        #     else:
        #         data.is_check = False
        #     data.save(update_fields=["is_check"])
        
        url_redirect = self.get_url()

        return HttpResponseRedirect(url_redirect)

    
    def check_format(self, date):
        frmt = r"\d{2}.\d{2}.\d{4}-\d{2}.\d{2}.\d{4}"
        return len(re.findall(frmt, date)) != 0

def page_not_found(request, exception):
    return HttpResponse("<h1>Такой страницы не существует =)</h1> <br> <a href='/parser'>Перейти на главную страницу</a>")
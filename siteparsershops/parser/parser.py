import csv
import requests
import re 
import threading
import time

from bs4 import BeautifulSoup

from django.core.cache import cache


#если есть данные и/или сайт не пустышка - успешно
#если сайт пустышка/стандартный - перепроверка
#если бан от служб рф - удаление

message = 1

# def data_from_file(filename: str) -> list:
#     with open(filename, "r", newline="") as file:
#         reader = csv.reader(file, delimiter=' ', quotechar="|")
#         return [row[0].split(";")[:-1] for row in list(reader)[1:] if row[0].split(";")[:-1][0] == "2024-07-15"]

def data_from_file(filename: str) -> list:
    with open(filename, "r", newline="") as file:
        reader = csv.reader(file)
        result = [row[0].split(';')[:-1] if len(row[0].split(';')) == 3 else row[0].split(';') for row in reader if row[0] != ";"]
        return result[1:]

def find_email(html: str):
    return [res for res in re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,5}(?=\s|$|>|<|»|«|,)", html) if res.split(".")[-1] not in ["png", "webp", "jpeg", "jpg", "svg"]]

def find_phone(html: str):
    pat1 = r"(?<=[\s><:])\+[0-9]{9,15}(?=\s|$|>|<)"
    pat2 = r"(?<=[\s><:])\+\d{1,3} \d{3} \d{3}-\d{2}-\d{2}" 
    pat3 = r"(?<=[\s><:])8 \(\d{3}\) \d{3}-\d{2}-\d{2}"
    pat4 = r"(?<=[\s><:])8\d{10}"
    pat5 = r"\+7\s?[0-9\s‑]{10,}"
    return [res.replace("xa0", "") for res in (re.findall(pat1, html) + re.findall(pat2, html) + re.findall(pat3, html) + re.findall(pat4, html) + re.findall(pat5, html))]

def find_inn(html: str):
    return re.findall(r"ИНН [a-zA-Z0-9.-«»]{10,12}(?=\s|$|>|<|»|«|,)", html)

def find_ooo(html: str):
    clean_html = re.sub(r'<[^>]+>', ' ', html)

    pat1 = r"ООО [a-zA-Zа-яА-Я0-9.-«»&;]{1,100}(?=\s|$|>|<|»|«|,)"
    pat2 = r"ООО [a-zA-Zа-яА-Я0-9.-«»&;]{1,100} [a-zA-Zа-яА-Я0-9.-«»&;]{1,100}(?=\s|$|>|<|»|«|,)"
    pat3 = r"ООО [a-zA-Zа-яА-Я0-9.-«»&;]{1,100} [a-zA-Zа-яА-Я0-9.-«»&;]{1,100} [a-zA-Zа-яА-Я0-9.-«»&;]{1,100}(?=\s|$|>|<|»|«|,)"
    pat4 = r"ООО [a-zA-Zа-яА-Я0-9.-«»&;]{1,100} [a-zA-Zа-яА-Я0-9.-«»&;]{1,100} [a-zA-Zа-яА-Я0-9.-«»&;]{1,100} [a-zA-Zа-яА-Я0-9.-«»&;]{1,100}(?=\s|$|>|<|»|«|,)"
    pat5 = r"ООО [a-zA-Zа-яА-Я0-9.-«»&;]{1,100} [a-zA-Zа-яА-Я0-9.-«»&;]{1,100} [a-zA-Zа-яА-Я0-9.-«»&;]{1,100} [a-zA-Zа-яА-Я0-9.-«»&;]{1,100} [a-zA-Zа-яА-Я0-9.-«»&;]{1,100}(?=\s|$|>|<|»|«|,)"

    results = re.findall(pat1, clean_html) + re.findall(pat2, clean_html) + re.findall(pat3, clean_html) + re.findall(pat4, clean_html) + re.findall(pat5, clean_html)

    unique_results = []
    for result in sorted(results, key=len, reverse=True):
        if not any(result in longer for longer in unique_results):
            unique_results.append(result)
    
    return [res.replace("&laquo;", "").replace("&raquo;", "").replace("&quot;", "")[:res.find("»")+1] if res.find("»") != -1 else res.replace("&laquo;", "").replace("&raquo;", "").replace("&quot;", "") for res in unique_results]

def find_individual(html: str):
    clean_html = re.sub(r'<[^>]+>', ' ', html)
    
    return re.findall(r"ИП [a-zA-Zа-яА-Я0-9.-«»&;]{1,50} [a-zA-Zа-яА-Я0-9.-«»&;]{1,50} [a-zA-Zа-яА-Я0-9.-«»&;]{1,50}(?=\s|$|>|<|»|«|,)", clean_html)

def find_urls(html: str, url: str):
    soup = BeautifulSoup(html, "html.parser")
    hrefs = [a.get("href") for a in soup.find_all("a", href=True)]
    final_hrefs = []
    for idx in range(len(hrefs)):
        if any([True if exp in hrefs[idx] else False for exp in ("javascript", "js", "src", "io", "png", "jpg", "svg", "webp", "html")]):
            continue
        elif not "http" in hrefs[idx]:
            if hrefs[idx] != '':
                if url[-1] == hrefs[idx][0] == "/":
                    final_hrefs.append(url + hrefs[idx][1:])
                else:
                    final_hrefs.append(url + hrefs[idx])
            else:
                final_hrefs.append(url + hrefs[idx])
        else:
            final_hrefs.append(hrefs[idx])

        if hrefs[idx][:-1].count('/') >= 4:
            if hrefs[idx] in final_hrefs:
                final_hrefs.remove(hrefs[idx])

    return list(set(final_hrefs))

# SHABLON = [
#     """
    # <div class="tw-col tw-col_pb0 tw-col-12 tw-col-lg-6">
    #     <div class="dummy-alert__info">
    #             <span class="svg-icon">
    #                 <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
    #                     <path fill-rule="evenodd" clip-rule="evenodd" d="M9 6C9 5.448 9.448 5 10 5C10.552 5 11 5.448 11 6V11C11 11.552 10.552 12 10 12C9.448 12 9 11.552 9 11V6ZM9 14C9 13.448 9.448 13 10 13C10.552 13 11 13.448 11 14C11 14.552 10.552 15 10 15C9.448 15 9 14.552 9 14ZM10 18C5.589 18 2 14.411 2 10C2 5.589 5.589 2 10 2C14.411 2 18 5.589 18 10C18 14.411 14.411 18 10 18ZM10 0C4.477 0 0 4.477 0 10C0 15.523 4.477 20 10 20C15.523 20 20 15.523 20 10C20 4.477 15.523 0 10 0Z" fill="white"/>
    #                 </svg>
    #             </span>
    #         <span><strong>Домен припаркован</strong></span>
    #     </div>
    # </div>
#     """,
#     """
#     lostdomain 
#     """,
#     """
#     <strong class="mh">.masterhost</strong>
#     """,
#     """
#     <p class="lead">This page is used to test the proper operation of the <a href="http://apache.org">Apache HTTP server</a> after it has been installed. If you can read this page it means that this site is working properly.
#     """,
#     """
#   <g class="ds-site-logo__icon">
#     <path d="M26.3618 10.5399H17.6244L14.7667 7.68225C14.0077 6.92323 12.9829 6.5 11.909 6.5H4.08105V10.5399H11.9125L14.7702 13.3976C15.5292 14.1566 16.5541 14.5799 17.6279 14.5799H25.4594V28.0148H29.4993V13.6774C29.4993 11.946 28.0967 10.5399 26.3618 10.5399Z" fill="#3755FA"></path>
#     <path d="M4.08093 10.5398H0.0410156V28.9171C0.0410156 30.6485 1.44362 32.0546 3.17851 32.0546H25.4592V28.0147H4.08093V10.5398Z" fill="#3755FA"></path>
#   </g>
#     """,
#         """
#   <g class="ds-site-logo__icon">
#     <path d="M26.3618 10.5399H17.6244L14.7667 7.68225C14.0077 6.92323 12.9829 6.5 11.909 6.5H4.08105V10.5399H11.9125L14.7702 13.3976C15.5292 14.1566 16.5541 14.5799 17.6279 14.5799H25.4594V28.0148H29.4993V13.6774C29.4993 11.946 28.0967 10.5399 26.3618 10.5399Z" fill="#3755FA" />
#     <path d="M4.08093 10.5398H0.0410156V28.9171C0.0410156 30.6485 1.44362 32.0546 3.17851 32.0546H25.4592V28.0147H4.08093V10.5398Z" fill="#3755FA" />
#   </g>
#     """,
#     """
#     <img src="https://handyhost.ru/tpl/img/logo2.png" alt="Удобный хостинг - HandyHost.ru">
#     """,
#     """
#   <g class="ds-site-logo__letters">
#     <path d="M97.3967 23.3381C95.9662 23.3381 94.9238 24.363 94.9238 25.7761C94.9238 27.1892 95.9627 28.214 97.3967 28.214C98.8308 28.214 99.9011 27.1892 99.9011 25.7761C99.9011 24.363 98.8483 23.3381 97.3967 23.3381Z" fill="#2B2F33"></path>
#     <path d="M71.6299 10.3403C66.4812 10.3403 63.0254 13.9465 63.0254 19.3156C63.0254 24.6847 66.5336 28.2175 71.9622 28.2175C75.8727 28.2175 79.311 25.9544 80.0035 22.3027H75.9566C75.4844 23.9816 74.0783 24.9505 71.7628 24.9505C68.9716 24.9505 67.1597 22.9813 67.1318 20.211H80.042C80.878 14.7545 77.2683 10.2179 71.6299 10.3403ZM67.1807 17.5702C67.1807 17.5247 67.1842 17.4688 67.1912 17.4128C67.1947 17.3988 67.1947 17.3813 67.1982 17.3673C67.1982 17.3604 67.1982 17.3499 67.2017 17.3429C67.2087 17.2939 67.2157 17.2484 67.2262 17.1995C67.2367 17.161 67.2472 17.1155 67.2577 17.0735C67.2647 17.0246 67.2787 16.9756 67.2892 16.9301C67.3311 16.7517 67.3871 16.5734 67.4536 16.402C67.485 16.318 67.52 16.2376 67.5515 16.1606C67.583 16.0907 67.6144 16.0277 67.6494 15.9612C68.3909 14.5027 69.8705 13.5758 71.6614 13.5758C73.76 13.5758 75.278 14.6006 75.9111 16.3705C75.9181 16.388 75.9251 16.409 75.9321 16.4334C75.9461 16.4719 75.9601 16.5139 75.9706 16.5559C75.9741 16.5594 75.9776 16.5664 75.9776 16.5733C75.9951 16.6223 76.0091 16.6748 76.0231 16.7238C76.065 16.8742 76.1 17.0386 76.128 17.189C76.163 17.3464 76.1805 17.4863 76.184 17.5702H67.1807Z" fill="#2B2F33"></path>
#     <path d="M83.4375 10.5398V28.0147H87.376V14.0341H95.0676V10.5398H83.4375Z" fill="#2B2F33"></path>
#     <path d="M136.825 10.5401L132.302 23.1951L127.65 10.5401H123.516L130.186 27.8052L129.542 29.4176C129.011 30.8097 128.696 31.0546 127.416 31.0546H124.743V34.4999H128.745C131.312 34.4999 132.099 33.1917 133.169 30.418L140.959 10.5366H136.821L136.825 10.5401Z" fill="#2B2F33"></path>
#     <path d="M114.613 10.3333C111.875 10.3333 109.849 11.9562 109.01 13.7541H108.324L107.768 10.5326H104.421V34.4994H108.324V25.1778H109.115C110.364 27.0142 112.137 28.074 114.613 28.074C119.136 28.074 122.497 24.2719 122.427 19.2036C122.427 13.9779 119.038 10.3333 114.613 10.3333ZM113.358 24.7056C110.465 24.7056 108.324 22.523 108.324 19.2701C108.324 16.0171 110.465 13.7016 113.358 13.7016C116.25 13.7016 118.387 15.9122 118.387 19.2036C118.387 22.495 116.247 24.7056 113.358 24.7056Z" fill="#2B2F33"></path>
#     <path d="M52.7735 10.3333C50.0348 10.3333 48.0096 11.9562 47.1701 13.7541H46.4846L45.9284 10.5326H42.5811V34.4994H46.4846V25.1778H47.275C48.5237 27.0142 50.2971 28.074 52.7735 28.074C57.2961 28.074 60.6575 24.2719 60.5875 19.2036C60.5875 13.9779 57.1982 10.3333 52.7735 10.3333ZM51.5178 24.7056C48.6252 24.7056 46.4846 22.523 46.4846 19.2701C46.4846 16.0171 48.6252 13.7016 51.5178 13.7016C54.4105 13.7016 56.5476 15.9122 56.5476 19.2036C56.5476 22.495 54.407 24.7056 51.5178 24.7056Z" fill="#2B2F33"></path>
#   </g>
#   <g class="ds-site-logo__icon">
#     <path d="M26.3618 10.5399H17.6244L14.7667 7.68225C14.0077 6.92323 12.9829 6.5 11.909 6.5H4.08105V10.5399H11.9125L14.7702 13.3976C15.5292 14.1566 16.5541 14.5799 17.6279 14.5799H25.4594V28.0148H29.4993V13.6774C29.4993 11.946 28.0967 10.5399 26.3618 10.5399Z" fill="#3755FA"></path>
#     <path d="M4.08093 10.5398H0.0410156V28.9171C0.0410156 30.6485 1.44362 32.0546 3.17851 32.0546H25.4592V28.0147H4.08093V10.5398Z" fill="#3755FA"></path>
#   </g>
#     """,
#     """
#     <span class="b-parking-shopfront__header-text b-parking-shopfront__header-text_mode_additional tooltip" title="по&nbsp;данным StatOnline.ru, занимает первое место по&nbsp;количеству зарегистрированных доменов и&nbsp;размещённых сайтов в&nbsp;национальных зонах .RU и .РФ.">
#                         Хостинг-провайдер и регистратор доменных имён №1 в России
#                     </span>
#     """,
# ]

# DELETE = [
#     """
# <html><head><script>functionset_cookie(){varnow=newDate();vartime=now.getTime();time+=19360000*1000;now.setTime(time);document.cookie='beget=begetok'+';expires='+now.toGMTString()+';path=/';}set_cookie();location.reload();;</script></head><body></body></html>
#     """,
#     """
#                 <div class="octo">
#                 <img src="https://cp.beget.com/img/octo/octo_error.png">
#             </div>
#     """,
#     """
#     <td style="vertical-align: middle; text-align: center;"><a href="https://tilda.cc"><img src="https://tilda.ws/img/logo404.png" border="0" alt="Tilda"></a><br><br><br><br><b>Domain has been assigned.</b><br>Please go to the site settings and put the domain name in the Domain tab.<br><br></td>
#     """
# ]

def unique(data: list, src: list):
    data[src[1]]["email"] = list(set(data[src[1]]["email"]))
    data[src[1]]["phone"] = list(set(data[src[1]]["phone"]))
    data[src[1]]["inn"] = list(set(data[src[1]]["inn"]))
    data[src[1]]["ooo"] = list(set(data[src[1]]["ooo"]))
    data[src[1]]["individual"] = list(set(data[src[1]]["individual"]))
    del data[src[1]]["domain"]

def parser(all_data: list, shared, index, delete, shablon):
    bad = 0
    good = 0
    check_again = 0
    again_domain = []
    data = {}
    
    for src in all_data:
        if not ("shop" in src[1].lower() or "store" in src[1].lower()):
            print("skip")
            continue
        print("not under", src[1])
        try:
            req = requests.get("http://" + src[1], timeout=10)
        except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.TooManyRedirects,
            requests.exceptions.InvalidSchema, requests.exceptions.ContentDecodingError, requests.exceptions.InvalidURL) as e:
            # print(e, src)
            bad += 1
            continue
        
        # if any([str(i.replace("   ", "").replace(" ", "")).strip() in str(str(req.text).replace("   ", "").replace(" ", "")).strip() for i in delete]):
        if any([re.sub(r'\s+', '', i) in re.sub(r'\s+', '', req.text) for i in delete]):
            # print("ОШИБКА", src)
            bad += 1
            continue
        
        if any([re.sub(r'\s+', '', i) in re.sub(r'\s+', '', req.text) for i in shablon]):
            # print("ОШИБКА", src)
            again_domain.append(src)
            check_again += 1
            continue

        data[src[1]] = {}
        data[src[1]]["email"] = find_email(req.text)
        data[src[1]]["phone"] = find_phone(req.text)
        data[src[1]]["inn"] = find_inn(req.text)
        data[src[1]]["ooo"] = find_ooo(req.text)
        data[src[1]]["individual"] = find_individual(req.text)
        data[src[1]]["domain"] = find_urls(req.text, req.url)
        good += 1
        for under_src in data[src[1]]["domain"]:
            try:
                print("under11", under_src)
                under_req = requests.get(under_src, timeout=7)
                data[src[1]]["email"] += find_email(under_req.text)
                data[src[1]]["phone"] += find_phone(under_req.text)
                data[src[1]]["inn"] += find_inn(under_req.text)
                data[src[1]]["ooo"] += find_ooo(under_req.text)
                data[src[1]]["individual"] += find_individual(under_req.text)
            except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.TooManyRedirects,
            requests.exceptions.InvalidSchema, requests.exceptions.ContentDecodingError, requests.exceptions.InvalidURL) as e:
                # print("ОШИБКА", src, e)
                continue
        unique(data, src)
    shared[index] = {"data": data, "good": good, "bad": bad, "check_again": check_again, "again_domain": again_domain}

def split_file(nums: int, data: list):
    start = 0
    end = start + len(data) // nums
    new_data = []
    while start <= len(data):
        if (start + len(data) // nums) >= len(data):
            new_data.append(data[start:])
            break
        new_data.append(data[start:end])
        start = end
        end = start + len(data) // nums
    return new_data

# cache.set("bad", 0)
# cache.set("good", 0)
# cache.set("check_again", 0)
# cache.set("again_domain", [])
# cache.set("data", {})
cache.set("count_data", 1)
cache.set("start_parser", False)
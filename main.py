import csv
import requests
import re 
import threading

from bs4 import BeautifulSoup


#если есть данные и/или сайт не пустышка - успешно
#если сайт пустышка/стандартный - перепроверка
#если бан от служб рф - удаление

#переделать домены

def data_from_file(filename: str) -> list:
    with open(filename, "r", newline="") as file:
        reader = csv.reader(file, delimiter=' ', quotechar="|")
        return [row[0].split(";")[:-1] for row in list(reader)[1:] if row[0].split(";")[:-1][0] == "2024-07-15"]

def get_src(html: str, url: str):
    split_comma = html.split("\"")
    return [http for data in split_comma for http in data.split(" ") if "http" in http and http not in (url, url[:-1]) if "http" in data and "://" in data]

def find_email(html: str):
    return re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,5}(?=\s|$|>|<)", html)

def find_phone(html: str):
    return re.findall(r"\+[0-9]{9,15}(?=\s|$|>|<)", html) + re.findall(r"\+\d{1,3} \(\d{3}\) \d{3}-\d{2}-\d{2}", html) + re.findall(r"8 \(\d{3}\) \d{3}-\d{2}-\d{2}", html) + re.findall(r"8\d{10}", html)

def find_inn(html: str):
    return re.findall(r"ИНН [a-zA-Z0-9.-]{12}(?=\s|$|>|<)", html)

def find_ooo(html: str):
    return re.findall(r"ООО [a-zA-Zа-яА-Я0-9.-]{1,100} [a-zA-Zа-яА-Я0-9.-]{1,100}(?=\s|$|>|<)", html)

def find_individual(html: str):
    return re.findall(r"ИП [a-zA-Zа-яА-Я0-9.-]{1,50} [a-zA-Zа-яА-Я0-9.-]{1,50} [a-zA-Zа-яА-Я0-9.-]{1,50}(?=\s|$|>|<)", html)

def find_ip(html: str):
    return re.findall(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(?=\s|$|>|<)", html)

def find_urls(html: str, url: str):
    soup = BeautifulSoup(html, "html.parser")
    hrefs = [a.get("href") for a in soup.find_all("a", href=True)]
    for idx in range(len(hrefs)):
        if "http" not in hrefs[idx]:
            hrefs[idx] = "http://" + url + hrefs[idx]
    return hrefs


# def find_domain(html: str):
    # domains = re.findall(r"(?:\s|$|>|<)[a-zA-Zа-яА-Я0-9.-]{1,100}\.[a-zA-Zа-яА-Я]{1,3}(?=\s|$|>|<)", html)
    # for domain in domains:
        # if "src" in domain or 'js' in domain or "io" in domain:
    # return 

SHABLON = [
    """
    <div class="tw-col tw-col_pb0 tw-col-12 tw-col-lg-6">
        <div class="dummy-alert__info">
                <span class="svg-icon">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path fill-rule="evenodd" clip-rule="evenodd" d="M9 6C9 5.448 9.448 5 10 5C10.552 5 11 5.448 11 6V11C11 11.552 10.552 12 10 12C9.448 12 9 11.552 9 11V6ZM9 14C9 13.448 9.448 13 10 13C10.552 13 11 13.448 11 14C11 14.552 10.552 15 10 15C9.448 15 9 14.552 9 14ZM10 18C5.589 18 2 14.411 2 10C2 5.589 5.589 2 10 2C14.411 2 18 5.589 18 10C18 14.411 14.411 18 10 18ZM10 0C4.477 0 0 4.477 0 10C0 15.523 4.477 20 10 20C15.523 20 20 15.523 20 10C20 4.477 15.523 0 10 0Z" fill="white"/>
                    </svg>
                </span>
            <span><strong>Домен припаркован</strong></span>
        </div>
    </div>
    """,
    """
    lostdomain 
    """,
    """
    <strong class="mh">.masterhost</strong>
    """,
    """
    <p class="lead">This page is used to test the proper operation of the <a href="http://apache.org">Apache HTTP server</a> after it has been installed. If you can read this page it means that this site is working properly.
    """
]

DELETE = [
    """
<html><head><script>functionset_cookie(){varnow=newDate();vartime=now.getTime();time+=19360000*1000;now.setTime(time);document.cookie='beget=begetok'+';expires='+now.toGMTString()+';path=/';}set_cookie();location.reload();;</script></head><body></body></html>
    """,
    """
                <div class="octo">
                <img src="https://cp.beget.com/img/octo/octo_error.png">
            </div>
    """
]
# print(str(DELETE[0].replace("   ", "").replace(" ", "")).strip() == str(str(req.text).replace("   ", "").replace(" ", "")).strip())

# dummy-alert dummy-alert--margin-negative dummy-alert--success
# 24AUTOEXPERT24.ru
# for i in ("http://akolokoltsev.ru/", ):
#     try:
#         req = requests.get(i)
#     except requests.exceptions.ConnectionError:
#         print("exp")

def parser(all_data: list):
    global data, bad, good, check_again
    for src in all_data:
        print(src[1])
        try:
            req = requests.get("http://" + src[1], timeout=5)
        except requests.exceptions.ConnectionError:
            bad += 1
            continue
        except requests.exceptions.Timeout:
            bad += 1
            continue
        except requests.exceptions.TooManyRedirects:
            bad += 1
            continue
        
        if any([str(i.replace("   ", "").replace(" ", "")).strip() in str(str(req.text).replace("   ", "").replace(" ", "")).strip() for i in DELETE]):
            bad += 1
            continue
        
        if any([str(i.replace("   ", "").replace(" ", "")).strip() in str(str(req.text).replace("   ", "").replace(" ", "")).strip() for i in SHABLON]):
            check_again += 1
            continue

        data[src[1]] = {}
        data[src[1]]["email"] = " ".join(find_email(req.text))
        data[src[1]]["phone"] = " ".join(find_phone(req.text))
        data[src[1]]["inn"] = " ".join(find_inn(req.text))
        data[src[1]]["ooo"] = " ".join(find_ooo(req.text))
        data[src[1]]["individual"] = " ".join(find_individual(req.text))
        data[src[1]]["ip"] = " ".join(find_ip(req.text))
        data[src[1]]["domain"] = " ".join(find_urls(req.text, req.url))
        good += 1

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

# data = {}
# bad = good = check_again = 0
# filename = "ihead_domains_1725961813_4457.csv"
# all_data = data_from_file(filename)

# thrs = []
# for num in range(16):
#     thr = threading.Thread(target=parser, args=(split_file(16, all_data)[num], ))
#     thr.start()
#     thrs.append(thr)
    
# for thr in thrs:
#     thr.join()

# print("-=-=-=-=-=-=")
# print(data)
# with open("test.txt", "w", encoding="UTF-8") as file:
#     file.write(str(data))
# print("-=-=-=-=-=-=")

# print("-=-=-=-=-=-=")
# print("good:", good)
# print("bad:", bad)
# print("check again:", check_again)
# print("-=-=-=-=-=-=")

req = requests.get("http://MOSTLINGSIBOWRARA.ru")
with open('test1.txt', "w", encoding="UTF-8") as file:
    file.write(req.text)

# test = "big@desktop +79869466585 fedorov22134@gmail.com ИНН 012345678912 ООО ПАРАМ ПАРАМ ИП ПАРАМ ПАРАМ ПАРАМ ПАРААМ 25.255.25.1 aaaa.ru"

# print(find_email(test))
# print(find_phone(test))
# print(find_inn(test))
# print(find_ooo(test))
# print(find_individual(test))
# print(find_ip(test))
# print(find_domain(test))
import csv
import requests
import re 

from bs4 import BeautifulSoup


#если есть данные и/или сайт не пустышка - успешно
#если сайт пустышка/стандартный - перепроверка
#если бан от служб рф - удаление

def data_from_file(filename: str) -> list:
    with open(filename, "r", newline="") as file:
        reader = csv.reader(file, delimiter=' ', quotechar="|")
        return [row[0].split(";")[:-1] for row in list(reader)[1:] if row[0].split(";")[:-1][0] == "2024-07-15"]

def get_src(html: str, url: str):
    split_comma = html.split("\"")
    return [http for data in split_comma for http in data.split(" ") if "http" in http and http not in (url, url[:-1]) if "http" in data and "://" in data]

def find_email(html: str):
    return re.findall(r"[a-zA-Z0-9.-]{0,1024}@[a-zA-Z0-9.-]{0,1024}", html)

def find_phone(html: str):
    return re.findall(r"\+[0-9]{9,15}", html)

def find_inn(html: str):
    return re.findall(r"ИНН [a-zA-Z0-9.-]{12}", html)

def find_ooo(html: str):
    return re.findall(r"ООО [a-zA-Zа-яА-Я0-9.-]{0,100} [a-zA-Zа-яА-Я0-9.-]{0,100}", html)

def find_individual(html: str):
    return re.findall(r"ИП [a-zA-Zа-яА-Я0-9.-]{0,50} [a-zA-Zа-яА-Я0-9.-]{0,50} [a-zA-Zа-яА-Я0-9.-]{0,50}", html)

def find_ip(html: str):
    return re.findall(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", html)

def find_domain(html: str):
    return re.findall(r"\ [a-zA-Zа-яА-Я0-9.-]{0,100}\.[a-zA-Zа-яА-Я]{1,5}", html)

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
    """
]

DELETE = [
    """
<html><head><script>functionset_cookie(){varnow=newDate();vartime=now.getTime();time+=19360000*1000;now.setTime(time);document.cookie='beget=begetok'+';expires='+now.toGMTString()+';path=/';}set_cookie();location.reload();;</script></head><body></body></html>
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
all_data = data_from_file("ihead_domains_1725961813_4457.csv")
for src in all_data:
    ...

# test = "+79869466585 fedorov22134@gmail.com ИНН 012345678912 ООО ПАРАМ ПАРАМ ИП ПАРАМ ПАРАМ ПАРАМ ПАРААМ 25.255.25.1 aaaa.ru"

# site1 = all_data[1]
# req = requests.get(url="http://"+site1)

# print(find_email(test))
# print(find_phone(test))
# print(find_inn(test))
# print(find_ooo(test))
# print(find_individual(test))
# print(find_ip(test))
# print(find_domain(test))
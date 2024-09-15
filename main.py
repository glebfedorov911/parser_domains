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

def find_email(html: str):
    return re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,5}(?=\s|$|>|<)", html)

def find_phone(html: str):
    pat1 = r"(?<=[\s><:])\+[0-9]{9,15}(?=\s|$|>|<)"
    pat2 = r"(?<=[\s><:])\+\d{1,3} \(\d{3}\) \d{3}-\d{2}-\d{2}"
    pat3 = r"(?<=[\s><:])8 \(\d{3}\) \d{3}-\d{2}-\d{2}"
    pat4 = r"(?<=[\s><:])8\d{10}"
    return re.findall(pat1, html) + re.findall(pat2, html) + re.findall(pat3, html) + re.findall(pat4, html)

def find_inn(html: str):
    return re.findall(r"ИНН [a-zA-Z0-9.-]{12}(?=\s|$|>|<)", html)

def find_ooo(html: str):
    return re.findall(r"ООО [a-zA-Zа-яА-Я0-9.-]{1,100} [a-zA-Zа-яА-Я0-9.-]{1,100} [a-zA-Zа-яА-Я0-9.-]{1,100} [a-zA-Zа-яА-Я0-9.-]{1,100} [a-zA-Zа-яА-Я0-9.-]{1,100}(?=\s|$|>|<)", html)

def find_individual(html: str):
    return re.findall(r"ИП [a-zA-Zа-яА-Я0-9.-]{1,50} [a-zA-Zа-яА-Я0-9.-]{1,50} [a-zA-Zа-яА-Я0-9.-]{1,50}(?=\s|$|>|<)", html)

def find_urls(html: str, url: str):
    soup = BeautifulSoup(html, "html.parser")
    hrefs = [a.get("href") for a in soup.find_all("a", href=True)]
    final_hrefs = []
    for idx in range(len(hrefs)):
        if any([True if exp in hrefs[idx] else False for exp in ("javascript", "js", "src", "io", "png", "jpg", "svg", "webp")]):
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
            final_hrefs.append(url)
    return list(set(final_hrefs))


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
    """,
    """
  <g class="ds-site-logo__icon">
    <path d="M26.3618 10.5399H17.6244L14.7667 7.68225C14.0077 6.92323 12.9829 6.5 11.909 6.5H4.08105V10.5399H11.9125L14.7702 13.3976C15.5292 14.1566 16.5541 14.5799 17.6279 14.5799H25.4594V28.0148H29.4993V13.6774C29.4993 11.946 28.0967 10.5399 26.3618 10.5399Z" fill="#3755FA"></path>
    <path d="M4.08093 10.5398H0.0410156V28.9171C0.0410156 30.6485 1.44362 32.0546 3.17851 32.0546H25.4592V28.0147H4.08093V10.5398Z" fill="#3755FA"></path>
  </g>
    """,
        """
  <g class="ds-site-logo__icon">
    <path d="M26.3618 10.5399H17.6244L14.7667 7.68225C14.0077 6.92323 12.9829 6.5 11.909 6.5H4.08105V10.5399H11.9125L14.7702 13.3976C15.5292 14.1566 16.5541 14.5799 17.6279 14.5799H25.4594V28.0148H29.4993V13.6774C29.4993 11.946 28.0967 10.5399 26.3618 10.5399Z" fill="#3755FA" />
    <path d="M4.08093 10.5398H0.0410156V28.9171C0.0410156 30.6485 1.44362 32.0546 3.17851 32.0546H25.4592V28.0147H4.08093V10.5398Z" fill="#3755FA" />
  </g>
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

def unique(data: list, src: list):
    data[src[1]]["email"] = list(set(data[src[1]]["email"]))
    data[src[1]]["phone"] = list(set(data[src[1]]["phone"]))
    data[src[1]]["inn"] = list(set(data[src[1]]["inn"]))
    data[src[1]]["ooo"] = list(set(data[src[1]]["ooo"]))
    data[src[1]]["individual"] = list(set(data[src[1]]["individual"]))
    del data[src[1]]["domain"]

def parser(all_data: list):
    global data, bad, good, check_again, total
    for src in all_data:
        print("not under", src[1])
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
        data[src[1]]["email"] = find_email(req.text)
        data[src[1]]["phone"] = find_phone(req.text)
        data[src[1]]["inn"] = find_inn(req.text)
        data[src[1]]["ooo"] = find_ooo(req.text)
        data[src[1]]["individual"] = find_individual(req.text)
        data[src[1]]["domain"] = find_urls(req.text, req.url)
        good += 1
        for under_src in data[src[1]]["domain"]:
            try: #переписать в потоки
                print("under", under_src)
                under_req = requests.get(under_src, timeout=3)
                data[src[1]]["email"] += find_email(under_req.text)
                data[src[1]]["phone"] += find_phone(under_req.text)
                data[src[1]]["inn"] += find_inn(under_req.text)
                data[src[1]]["ooo"] += find_ooo(under_req.text)
                data[src[1]]["individual"] += find_individual(under_req.text)
            except requests.exceptions.MissingSchema:
                continue
            except requests.exceptions.ConnectionError:
                continue
            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.TooManyRedirects:
                continue
            except requests.exceptions.InvalidSchema:
                continue
        unique(data, src)
        total += 1
        print(total, "/ 2361")

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

data = {}
total = 0
bad = good = check_again = 0
filename = "ihead_domains_1725961813_4457.csv"
all_data = data_from_file(filename)

# with open("test1.txt", "w", encoding="UTF-8") as file:
#     req = requests.get("http://GIGASTOR.ru")
#     file.write(str(req.text))

thrs = []
for num in range(16):
    thr = threading.Thread(target=parser, args=(split_file(16, all_data)[num], ))
    thr.start()
    thrs.append(thr)
    
for thr in thrs:
    thr.join()

print("-=-=-=-=-=-=")
print(data)
with open("test.txt", "w", encoding="UTF-8") as file:
    file.write(str(data))
print("-=-=-=-=-=-=")

print("-=-=-=-=-=-=")
print("good:", good)
print("bad:", bad)
print("check again:", check_again)
print("-=-=-=-=-=-=")

# test = "big@desktop +79869466585 fedorov22134@gmail.com ИНН 012345678912 ООО ПАРАМ ПАРАМ ИП ПАРАМ ПАРАМ ПАРАМ ПАРААМ 25.255.25.1 aaaa.ru"

# print(find_email(test))
# print(find_phone(test))
# print(find_inn(test))
# print(find_ooo(test))
# print(find_individual(test))
# print(find_ip(test))
# print(find_domain(test))
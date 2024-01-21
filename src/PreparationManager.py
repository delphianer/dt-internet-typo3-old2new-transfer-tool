import base64
import datetime
import json
import os.path
import pickle
import re

from bs4 import BeautifulSoup


def load_the_page(filename):
    with open(filename, "r") as file:
        page_data = file.read()
    return page_data


def get_created_datetime_from_page(page_html):
    soup = BeautifulSoup(page_html, "html.parser")
    date_div = soup.find("div", {"class": "news-single-timedata"})
    if date_div:
        datestring = date_div.text
        # content: 8. Oktober 2023 12:29 Uhr. Alter: 102 Tage
        search_result = re.search(r'(\d+)\. (\w+) (\d+) (\d+:\d+)', datestring)
        if search_result:
            day = int(search_result.group(1))
            month_str = search_result.group(2)
            month_dict = dict(januar=1, februar=2, märz=3, april=4, mai=5, juni=6,
                              juli=7, august=8, september=9, oktober=10, november=11, dezember=12)
            month = month_dict[month_str.lower()]
            year = int(search_result.group(3))
            time_str = search_result.group(4)
            hour, minute = map(int, time_str.split(':'))
            date_time = datetime.datetime(year, month, day, hour, minute)
            return date_time, datestring
    return None, None


class PreparationManager:

    def __init__(self):
        self.files_processed = None

        self.other_files = None
        self.image_files = None
        self.standard_pages = None
        self.news_pages = None

    def set_files_processed(self, files_processed):
        self.files_processed = files_processed

    def print_download_stats(self):
        # print stats first
        files_count_by_content_type = {}
        self.news_pages = []
        self.standard_pages = []
        self.image_files = []
        self.other_files = []
        for i, file_data in enumerate(self.files_processed, start=1):
            # dict_keys(['filename', 'url', 'headers', 'data', 'image_list'])
            headers = file_data["headers"]
            content_type = headers["Content-Type"]
            if content_type not in files_count_by_content_type:
                files_count_by_content_type[content_type] = 1
            else:
                files_count_by_content_type[content_type] += 1
            if "/newsdetails/" in file_data["url"]:
                self.news_pages.append(file_data)
            elif content_type == "text/html;charset=utf-8":
                self.standard_pages.append(file_data)
            elif content_type in ["image/jpeg","image/png","image/gif","image/tiff"]:
                self.image_files.append(file_data)
            else:
                self.other_files.append(file_data)
                print( f"{i}:", file_data["url"])
            if i==1:
                print(file_data.keys())
        print("\n\nStatistik:")
        for content_type in files_count_by_content_type.keys():
            print("Content Type:", content_type, " Count:", files_count_by_content_type[content_type])
        print("\nStandard-Seiten:", len(self.standard_pages))
        print("news-pages:", len(self.news_pages))
        print("images:", len(self.image_files))
        print("other_files:", len(self.other_files))
        print("\nInsgesamt:", len(self.files_processed), "\n\n")

    def prepare_pages(self):

        # dict_keys(['filename', 'url', 'headers', 'data', 'image_list'])
        for page in self.standard_pages:
            # TODO: extract the Text Only - remove unnecessary Tags
            page_data = load_the_page(page["filename"])
            page_data_repaired = self.extractTextAndMainTags(page_data)
            #print(page_data)
            #print(page_data_repaired)
        for num, page in enumerate(self.news_pages,start=1):
            page_data = load_the_page(page["filename"])
            created_datetime, orig_date_string = get_created_datetime_from_page(page_data)
            filename = page["filename"].split("/")[-1]
            print(num, filename,"-> created_datetime=",created_datetime)
            # todo: hier weiter
            #for f in page:
            #    print("key=",f)
            #    print("data=")
            #    print(page[f])
            #    print("-"*50,"\n")
            # todo: get date and time of each page -> <div class="news-single-timedata"> 8. Oktober 2023 12:29 Uhr. Alter: 102 Tage<br/></div>
            # page["data"] -> class="news-single-timedata"  -> datum Uhrzeit
            # page["data"] -> h1 => Überschrift
        # TODO: feature: check encoding! all german special chars are wrong... just change them to html-special-chars!

    def extractTextAndMainTags(self, page):

        return page
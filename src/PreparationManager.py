import base64
import datetime
import json
import os.path
import pickle
import re

from bs4 import BeautifulSoup, Comment


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

    debug_enabled = False

    def __init__(self):
        self.page_number = None
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
        # 1. get extra info for news articles
        self.extract_created_datetime_from_news_pages()
        # 2. all pages - extract the Text Only - remove unnecessary Tags
        self.prepare_the_files(self.standard_pages)
        self.prepare_the_files(self.news_pages)
        # TODO: feature: check encoding! some german special chars at old pages are wrong... just change them to html-special-chars!

    def extract_created_datetime_from_news_pages(self):
        for num, page in enumerate(self.news_pages, start=1):
            page_data = load_the_page(page["filename"])
            # orig_date_string for debugging
            created_datetime, orig_date_string = get_created_datetime_from_page(page_data)
            if PreparationManager.debug_enabled:
                filename = page["filename"].split("/")[-1]
                print(num, filename, "-> ", orig_date_string, " => created_datetime=", created_datetime)
            page["created_datetime"] = created_datetime

    def prepare_the_files(self, pages):
        self.page_number = 1
        for page in pages:
            page_data = load_the_page(page["filename"])
            page_data_prepared_filename = page["filename"] + "_prepared.txt"
            page["filename_prepared"] = page_data_prepared_filename
            page_data_prepared_data = self.extract_text_and_main_tags(page_data)
            page_data_prepared_data = self.repair_encoding_and_use_html_special_chars(page_data_prepared_data)
            if not PreparationManager.debug_enabled:
                with open(page_data_prepared_filename, "w") as file:
                    file.write(page_data_prepared_data)
            self.page_number += 1

    def extract_text_and_main_tags(self, page_data):
        if self.page_number == 1:
            print("Original extract_text_and_main_tags:")
            print(page_data)
            print("-"*50)
            # command: delete all unnecessary div-tags in the html-text in page_data
            soup = BeautifulSoup(page_data, "html.parser")

            # Get rid of HTML-Comments
            for element in soup(text=lambda text: isinstance(text, Comment)):
                element.extract()

            # Get rid of div tags but keep their content
            for div_tag in soup.find_all("div"):
                div_tag.replace_with(*div_tag.contents)

            page_data = soup.prettify()
        if self.page_number == 1:
            print("Cleaned html:")
            print(page_data)
            print("-"*50)
        return page_data

    def repair_encoding_and_use_html_special_chars(self, page_data_prepared_data):
        #if self.page_number == 1:
        #    print("Original:")
        #    print(page_data_prepared_data)
        #    print("-" * 50)

        # Dictionary of German umlauts and special character to replace
        german_chars = {
            'ä': '&auml;',
            'ö': '&ouml;',
            'ü': '&uuml;',
            'ß': '&szlig;',
            'Ä': '&Auml;',
            'Ö': '&Ouml;',
            'Ü': '&Uuml;',
            '«': '&laquo;'
        }

        # beautiful soup parse html
        soup = BeautifulSoup(page_data_prepared_data, "html.parser")

        # Recursive function to replace umlauts in text nodes
        def replace_in_text_nodes(node):
            if node.string:
                for char, replacement in german_chars.items():
                    node.string = node.string.replace(char, replacement)
            if hasattr(node, "children"):
                for child in node.children:
                    if isinstance(child, Comment):
                        continue
                    replace_in_text_nodes(child)

        replace_in_text_nodes(soup)
        page_data_prepared_data = soup.prettify()

        #if self.page_number == 1:
        #    print(":")
        #    print(page_data_prepared_data)
        #    print("-" * 50)

        return page_data_prepared_data
import base64
import json
import os
import pickle
import random
import time
from urllib.parse import urlparse
import html2text
import requests
from bs4 import BeautifulSoup
from common import F
from UniqueStack import UniqueStack
import re

NO_FILE_NAME = '_no_file_name'

IGNORE_DOWNLOAD = "ignore-download"

class DownloadManager:

    debug_enabled = False
    maximum_downloads = -1
    # wait a second after x files:
    pause_each_file = 100

    def __init__(self,  global_config, download_to_directory):
        self.config = global_config
        self.base_download_directory = download_to_directory
        self.urls_to_download = UniqueStack()
        self.files_processed = []

    def download_files(self):
        try:
            self.urls_to_download.push("http://ovetze.drkcms.de/aktuelles/news.html")
            self.urls_to_download.push_all(self.config["extra_paths"], self.config["page_base"])

            # if a Test is needed - pass url like this
            self.urls_to_download.push(self.config['page_base']+self.config['page_sitemap'])
            # self.urls_to_download.push("http://ovetze.drkcms.de/index.php?eID=tx_cms_showpic&file=285&md5=deac577160968a505000907066ca9aa98ebff496&parameters%5B0%5D=eyJ3aWR0aCI6Ijc5MiIsImhlaWdodCI6IjYwMG0iLCJib2R5VGFnIjoiPGJvZHkg&parameters%5B1%5D=c3R5bGU9XCJtYXJnaW46MDsgYmFja2dyb3VuZDojZmZmO1wiPiIsIndyYXAiOiI8&parameters%5B2%5D=YSBocmVmPVwiamF2YXNjcmlwdDpjbG9zZSgpO1wiPiB8IDxcL2E%2BIn0%3D")

            self.print_todo_list()

            self.process_urls()
        except Exception as e:
            self.print_todo_list()
            print(e)
            raise e

    def print_todo_list(self):
        if DownloadManager.debug_enabled:
            F.print_und_log("TODO:")
            F.print_und_log("-" * 50)
            self.urls_to_download.print_stack()
            F.print_und_log(("-" * 50) + "\n\n")

    def process_urls(self):
        pause_each_file_num = 0
        status_file = 100
        while not self.urls_to_download.is_empty() and (self.maximum_downloads < 0 or self.maximum_downloads > 0):
            self.download_url(self.urls_to_download.pop())
            # wait a sec -> do not go to fast with the server of dt-internet
            if self.maximum_downloads > 0: # is like a small "debug-mode", so print always:
                print("Files to download:", self.maximum_downloads, " - files as result:", len(self.files_processed))
            else:
                status_file -= 1
                if status_file == 0:
                    print("Files downloaded:", len(self.files_processed))
                    status_file = 100
            pause_each_file_num += 1
            if  pause_each_file_num >= DownloadManager.pause_each_file:
                time.sleep(1)
                pause_each_file_num = 0
            self.maximum_downloads -= 1

    def __get_download_dir_structure_from(self, url):
        parsed_url = urlparse(url)
        paths = [path for path in parsed_url.path.split('/') if path]
        paths = paths[:-1]
        dir_name = os.path.sep.join(paths)
        return dir_name

    def __get_file_name_from(self, url):
        parsed_url = urlparse(url)
        paths = [path for path in parsed_url.path.split('/') if path]
        try:
            dl_file_name = paths[-1].split('#')[0]
        except IndexError :
            dl_file_name = NO_FILE_NAME + str(random.randint(100000, 1000000))
        return dl_file_name

    def download_url(self, url):
        F.logInfo("\nNew URL: " + url)
        if self.url_is_valid(url):
            page_data = self.download_the_page_data(url)

            if page_data:
                self.process_page_data(page_data, url)
            else:
                F.logError("No page data found in URL:"+ url)


    def process_page_data(self, page_data, url):
        relativ_download_directory = self.__get_download_dir_structure_from(url)
        file_name = self.__get_file_name_from(url)
        full_download_path = os.path.join(self.base_download_directory, relativ_download_directory)

        if not DownloadManager.debug_enabled:
            os.makedirs(full_download_path, exist_ok=True)

        file_path_page = os.path.join(full_download_path, url.split('/')[-1])
        #file_path_pickle = os.path.join(full_download_path, url.split('/')[-1] + ".pkl")

        if DownloadManager.debug_enabled:
            F.print_und_log("\n\nNew File:", file_path_page)
            #F.print_und_log("Pickle File:", file_path_pickle)
            F.print_und_log("Directory:", relativ_download_directory)
            F.print_und_log("file_name:", file_name)
            F.print_und_log("content-type:", page_data["content-type"])
            F.print_und_log("Headers:", page_data["headers"])
            F.print_und_log("Encoding:", page_data["encoding"])
            F.print_und_log("page_title:", page_data["page_title"])
            F.print_und_log("-" * 50, "\n\n")
            F.print_und_log("Bilder:")
            for i, img in enumerate( page_data["images"], start=1):
                F.print_und_log(f"{i}.",img)
            F.print_und_log("os.path.basename(file_path_page)", os.path.basename(file_path_page))
            F.print_und_log("-" * 50, "\n\n")

        if len(page_data["images"])>0:
            self.urls_to_download.push_all(page_data["images"], self.config["page_base"])
            F.print_und_log("Bilder in Todo-Liste eingefügt - TODOs: "+ str(self.urls_to_download.count()))
            self.print_todo_list()

        if "text/html" in page_data["content-type"]:
            if not DownloadManager.debug_enabled:

                with open(file_path_page, 'w') as file:
                    file.write(page_data["data"])

                html_file_data = {"filename": file_path_page,
                                  "url": page_data["url"],
                                  "headers": page_data["headers"],
                                  "image_list": page_data["images"]
                                 }
                self.files_processed.append(html_file_data)
        elif IGNORE_DOWNLOAD in page_data["content-type"]:
            pass # happens if the picture is embedded in an iframe or a popup
        else:
            if not DownloadManager.debug_enabled:
                with open(file_path_page, 'wb') as file:
                    file.write(page_data['data'])
                image_file_data = {"filename": file_path_page,
                                   "url": page_data["url"],
                                   "headers": page_data["headers"]
                            }
                self.files_processed.append(image_file_data)

    def get_absolute_url(self, base_url, relative_url):
        return base_url + relative_url if not relative_url.startswith('http') else relative_url

    def extract_new_download_links_from_html_content(self, html_content):
        links = html_content.find_all('a') if html_content else []

        valid_urls = []
        for link in links:
            if 'href' in link.attrs:
                if not any(excluded_path in link['href'] for excluded_path in self.config["excluded_paths"]):
                    if link['href'].startswith(self.config["page_base"]):  # absolute url from the same base
                        valid_urls.append(self.get_absolute_url(self.config["page_base"], link['href']).split('#')[0])
                    elif not link['href'].startswith(('http://', 'https://')):  # relative url
                        valid_urls.append(self.get_absolute_url(self.config["page_base"], link['href']).split('#')[0])
                else:
                    F.print_und_log("Link in Excluded_paths! Link:"+link["href"])

        self.urls_to_download.push_all(valid_urls, self.config["page_base"])

        if len(valid_urls) > 0:
            print("Number of links: "+ str(self.urls_to_download.count()))

        if DownloadManager.debug_enabled:
            self.print_todo_list()

    def download_the_page_data(self, url):
        # todo: setup:
        get_content_as_html = True
        get_content_as_markdown = False
        # end setup
        try:
            response = requests.get(url)
            if response.status_code == 404:
                F.logError('Page Not Found:'+url)
                F.logError('Ignoring this download')
                page_data_content_type = IGNORE_DOWNLOAD
                if self.maximum_downloads > 0:
                    self.maximum_downloads += 1
            else:
                response.raise_for_status()
                page_data_content_type = response.headers['content-type']

            if "text/html" in page_data_content_type:
                #F.print_und_log("A html/text to download ->",page_data_content_type)

                soup = BeautifulSoup(response.text, 'html.parser')
                page_title = soup.title.string
                body = soup.find('body')
                self.extract_new_download_links_from_html_content(body)
                col3_content = soup.find('div', id='col3_content')

                if not col3_content:
                    F.logError("Kein konkreten Inhalt gefunden:"+url)
                    # search for another a-tags:
                    html = soup.find("html")
                    self.extract_new_download_links_from_html_content(html)
                    images = [img['src'] for img in body.find_all('img') if 'src' in img.attrs]
                    content = "No Data -> it is an image!"
                    page_data_content_type = IGNORE_DOWNLOAD
                    if self.maximum_downloads > 0:
                        self.maximum_downloads += 1
                else:
                    images = [img['src'] for img in col3_content.find_all('img') if 'src' in img.attrs]

                    # Extrahieren der Bild-URLs aus onclick-Events
                    for a_tag in col3_content.find_all('a', onclick=True):
                        onclick_text = a_tag.get('onclick', '')
                        match = re.search(r"openPic\('([^']*)'", onclick_text)
                        if match:
                            image_url = match.group(1)
                            images.append(image_url)

                    if get_content_as_html:
                        content = str(col3_content)
                    elif get_content_as_markdown:
                        markdown_converter = html2text.HTML2Text()
                        markdown_converter.ignore_links = False
                        content = markdown_converter.handle(str(col3_content))
                    else:
                        content = col3_content.get_text()
            else:
                #F.print_und_log("A Picture or binary to download ->",page_data_content_type)
                page_title = 'FileDownload'
                content = response.content
                images = []

            return {"url": url,
                    "encoding":response.encoding,
                    "content-type": page_data_content_type,
                    "headers": response.headers,
                    # TODO: if it is a news-page - extract the timestamp of the news insert - that can be inserted later with correct timestamp
                    "page_title": page_title,
                    "data": content,
                    "images": images}
        except requests.exceptions.RequestException as e:
            F.logException(f"Fehler beim Abrufen der Seite {url}: {e}")
            raise e

    def url_is_valid(self, url):
        file_path = self.__get_download_dir_structure_from(url)+"/"+self.__get_file_name_from(url)
        if ":" in file_path\
                or file_path.startswith("/"+NO_FILE_NAME):
            F.logError("URL is not valid: "+ url)
            return False
        return True

    def save_filelist_to_pickle(self, pickle_filename):
        with open(pickle_filename, 'wb') as f_output:
            pickle.dump(self.files_processed, f_output)

    def load_filelist_from(self, filename):
        with open(filename, 'rb') as f_input:
            self.files_processed = pickle.load(f_input)

    def get_files_to_prepare_for_upload(self):
        return self.files_processed

    def has_files_downloaded(self):
        return len(self.files_processed) > 0

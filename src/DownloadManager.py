import os
import time
from urllib.parse import urlparse
import html2text
import requests
from bs4 import BeautifulSoup
import transferFuncs
from common import F
from UniqueStack import UniqueStack
import re

class DownloadManager:

    #debug_enabled = True
    debug_enabled = False

    def __init__(self,  global_config, download_to_directory):
        self.config = global_config
        self.base_download_directory = download_to_directory
        self.urls_to_download = UniqueStack()
        self.files_processed = UniqueStack()

    def download_files(self):
        # TODO: set the sitemap as first URL to download => all other URLs will be parsed after that
        urls = transferFuncs.get_all_urls_from_sitemap(self.config['page_base'],
                                                       self.config['page_sitemap'],
                                                       self.config["excluded_paths"])

        self.urls_to_download.push_all(urls)
        self.urls_to_download.push_all(self.config["extra_paths"], self.config["page_base"])

        self.debug_todo_list()

        self.process_urls()

        return self.files_processed

    def debug_todo_list(self):
        if DownloadManager.debug_enabled:
            F.print_und_log("TODO:")
            F.print_und_log("-" * 50)
            self.urls_to_download.print_stack()
            F.print_und_log(("-" * 50) + "\n\n")

    def process_urls(self):
        while not self.urls_to_download.is_empty():
            # TODO: Use 'Content-Type'-Header-Info for choosing Download and process the html-file or an other datatype (like picture)
            #       -> 'text/html;charset=utf-8'
            self.download_url(self.urls_to_download.pop())
            # wait a sec -> do not go to fast with the server of dt-internet
            time.sleep(1)

    # def __get_download_dir_structure_and_file_name_from(self, url):
    #     parsed_url = urlparse(url)
    #     paths = [path for path in parsed_url.path.split('/') if path]
    #     dl_file_name = paths[-1].split('#')[0]
    #
    #     paths = paths[:-1]
    #     dir_name = os.path.sep.join(paths)
    #
    #     return dir_name, dl_file_name

    def __get_download_dir_structure_from(self, url):
        parsed_url = urlparse(url)
        paths = [path for path in parsed_url.path.split('/') if path]
        paths = paths[:-1]
        dir_name = os.path.sep.join(paths)
        return dir_name

    def __get_file_name_from(self, url):
        parsed_url = urlparse(url)
        paths = [path for path in parsed_url.path.split('/') if path]
        dl_file_name = paths[-1].split('#')[0]
        return dl_file_name

    def download_url(self, url):
        F.print_und_log("\nNew URL: " + url)
        if self.url_is_valid(url):
            #page_data, new_urls = transferFuncs.scrape_page(url, self.config)
            page_data, new_urls = self.download_the_page_data(url)

            self.urls_to_download.push_all(new_urls)

            if len(new_urls) > 0:
                self.debug_todo_list()

            if page_data:
                self.process_page_data(page_data, url)
            else:
                F.print_und_log("No page data found in URL:"+ url)


    def process_page_data(self, page_data, url):
        relativ_download_directory = self.__get_download_dir_structure_from(url)
        file_name = self.__get_file_name_from(url)
        full_download_path = os.path.join(self.base_download_directory, relativ_download_directory)

        if not DownloadManager.debug_enabled:
            os.makedirs(full_download_path, exist_ok=True)

        file_path_page = os.path.join(full_download_path, url.split('/')[-1])
        file_path_json = os.path.join(full_download_path, url.split('/')[-1] + ".json")

        if DownloadManager.debug_enabled:
            F.print_und_log("\n\nNew File:", file_path_page)
            F.print_und_log("JSON File:", file_path_json)
            F.print_und_log("Directory:", relativ_download_directory)
            F.print_und_log("file_name:", file_name)
            F.print_und_log("page_title:", page_data["page_title"])
            F.print_und_log("Encoding:", page_data["encoding"])
            F.print_und_log("Headers:", page_data["headers"])
            F.print_und_log("-" * 50, "\n\n")
            F.print_und_log("Bilder:")
            for i, img in enumerate( page_data["images"], start=1):
                F.print_und_log(f"{i}.",img)
            F.print_und_log("os.path.basename(file_path_page)", os.path.basename(file_path_page))
            F.print_und_log("-" * 50, "\n\n")

        if "text/html" in page_data["content-type"]:
            if not DownloadManager.debug_enabled:
                with open(file_path_page, 'w') as file:
                    file.write(page_data["data"])
                with open(file_path_json, 'w') as file:
                    file.write(str(page_data))
                #new_urls, picture_files = transferFuncs.download_all_pictures(page_data["images"],
                #                                                              os.path.basename(file_path_page),
                #                                                              full_download_path,
                #                                                              self.config,
                #                                                              DownloadManager.debug_enabled)
                #self.urls_to_download.push_all(new_urls)
            if len(page_data["images"])>0:
                self.urls_to_download.push_all(page_data["images"], self.config["page_base"])
                F.print_und_log("Bilder in Todo-Liste eingefügt!")
                self.debug_todo_list()
        else:
            F.print_und_log("#### BILD ZU LADEN: image_filename:", file_path_page)
            if not DownloadManager.debug_enabled:
                with open(file_path_page, 'wb') as file:
                    file.write(page_data['data'])
                # also write headers and URL of picture-File:
                picture_page_data = {"url": page_data["url"],
                                     "headers": page_data["headers"],
                                     "data": "picture file"
                                    }
                with open(file_path_json, 'w') as file:
                    file.write(str(picture_page_data))


    def get_absolute_url(self, base_url, relative_url):
        return base_url + relative_url if not relative_url.startswith('http') else relative_url

    def gather_urls(self, body_content):
        links = body_content.find_all('a') if body_content else []
        urls = [self.get_absolute_url(self.config["page_base"], link['href']) for link in links if
                'href' in link.attrs and link['href'].startswith(self.config["page_base"])
                and not any(excluded_path.lower() in [l.lower for l in link['href']]
                            for excluded_path in self.config["excluded_paths"])]
        return urls

    def download_the_page_data(self, url):
        # todo: setup:
        get_content_as_html = True
        get_content_as_markdown = False
        # end setup
        try:
            response = requests.get(url)
            response.raise_for_status()
            page_data_content_type = response.headers['content-type']

            if "text/html" in page_data_content_type:
                #F.print_und_log("A html/text to download ->",page_data_content_type)

                soup = BeautifulSoup(response.text, 'html.parser')
                page_title = soup.title.string
                col3_content = soup.find('div', id='col3_content')

                if not col3_content:
                    return {"url": url, "data": "Kein Inhalt gefunden"}, None

                images = [img['src'] for img in col3_content.find_all('img') if 'src' in img.attrs]

                # Extrahieren der Bild-URLs aus onclick-Events
                for a_tag in col3_content.find_all('a', onclick=True):
                    onclick_text = a_tag.get('onclick', '')
                    match = re.search(r"openPic\('([^']*)'", onclick_text)
                    if match:
                        image_url = match.group(1)
                        images.append(image_url)

                if self.config["follow_links_on_same_page"]:
                    urls = self.gather_urls(col3_content)
                else:
                    urls = []

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
                urls = []

            return ({"url": url,
                    "encoding":response.encoding,
                    "content-type": page_data_content_type,
                    "headers": response.headers,
                    "page_title": page_title,
                    "data": content,
                    "images": images}, urls)
        except requests.exceptions.RequestException as e:
            F.print_und_log(f"Fehler beim Abrufen der Seite {url}: {e}")
            return None

    def url_is_valid(self, url):
        file_path = self.__get_download_dir_structure_from(url)+"/"+self.__get_file_name_from(url)
        if ":" in file_path:
            F.print_und_log("#### !!!! #### \n URL is not valid: ", url)
            return False
        #F.print_und_log("URL ist valide mit Pfad:", file_path)
        return True

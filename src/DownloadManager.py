import os
import time
from urllib.parse import urlparse
import transferFuncs
from common import F
from UniqueStack import UniqueStack

class DownloadManager:

    debug_enabled = True
    #debug_enabled = True

    def __init__(self,  global_config, download_to_directory):
        self.config = global_config
        self.base_download_directory = download_to_directory
        self.urls_to_download = UniqueStack()
        self.files_processed = UniqueStack()

    def download_files(self):
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
            print("TODO:")
            print("-" * 50)
            self.urls_to_download.print_stack()
            print("-" * 50, "\n\n")

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
        print("Bearbeite", url)
        page_data, new_urls = transferFuncs.scrape_page(url, self.config)
        # todo: page_data = self.download_the_page_data(url)
        # todo: new_urls = self.perform_analyze_page_data(page_data)

        self.urls_to_download.push_all(new_urls)

        if len(new_urls) > 0:
            self.debug_todo_list()

        if page_data:
            self.process_page_data(page_data, url)
        else:
            print("No page data found in URL", url)


    def process_page_data(self, page_data, url):
        relativ_download_directory = self.__get_download_dir_structure_from(url)
        file_name = self.__get_file_name_from(url)
        full_download_path = os.path.join(self.base_download_directory, relativ_download_directory)

        if not DownloadManager.debug_enabled:
            os.makedirs(full_download_path, exist_ok=True)

        file_path_page = os.path.join(full_download_path, url.split('/')[-1])
        file_path_json = os.path.join(full_download_path, url.split('/')[-1] + ".json")

        if DownloadManager.debug_enabled:
            print("\n\nNew File:", file_path_page)
            print("JSON File:", file_path_json)
            print("Directory:", relativ_download_directory)
            print("file_name:", file_name)
            print("page_title:", page_data["page_title"])
            print("Encoding:", page_data["encoding"])
            print("Headers:", page_data["headers"])
            print("-" * 50, "\n\n")
            print("Bilder:")
            for img in page_data["images"]:
                print(img)
            print("os.path.basename(file_path_page)",os.path.basename(file_path_page))
            print("-" * 50, "\n\n")
            new_urls, picture_files = transferFuncs.download_all_pictures(page_data["images"],
                                                                          os.path.basename(file_path_page),
                                                                          full_download_path,
                                                                          self.config,
                                                                          DownloadManager.debug_enabled)
            self.urls_to_download.push_all(new_urls)

            if len(new_urls) > 0:
                print("\n\nNEW TODOs at PICTURE DOWNLOADS!:")
                print("+" * 50)
                self.urls_to_download.print_stack()
                print("+" * 50, "\n\n")

        else:
            with open(file_path_page, 'w') as file:
                file.write(page_data["data"])
            with open(file_path_json, 'w') as file:
                file.write(str(page_data))
            new_urls, picture_files = transferFuncs.download_all_pictures(page_data["images"],
                                                                          os.path.basename(file_path_page),
                                                                          full_download_path,
                                                                          self.config,
                                                                          DownloadManager.debug_enabled)
            self.urls_to_download.push_all(new_urls)

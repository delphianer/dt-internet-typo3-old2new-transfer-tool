import os
import pickle
import random
import time
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from common import F
from UniqueStack import UniqueStack
import re

NO_FILE_NAME = '_no_file_name'

IGNORE_DOWNLOAD = "ignore-download"


class DownloadManager:
    """
    DownloadManager class

    This class is responsible for downloading files from a list of URLs.

    Attributes:
        debug_enabled (bool): Flag to enable debug mode.
        maximum_downloads (int): Maximum number of downloads. If set to -1, there is no limit.
        pause_each_file (int): Number of files to wait for before pausing.

    Methods:
        __init__(self, global_config, download_to_directory)
            Initializes a new instance of the DownloadManager class.

        download_files(self) -> None:
            Downloads files from a list of URLs.

        print_todo_list(self) -> None:
            Prints the todolist of the DownloadManager.

        process_urls(self) -> None:
            Process the URLs in the download manager.

        __get_download_dir_structure_from(self, url:str) -> None:
            Get the download directory structure from a given URL.

        __get_file_name_from(self, url: str) -> str:
            Extracts the file name from a given URL.

        download_url(self, url : str) -> None:
            Downloads URL and process page data.

        process_page_data(self, page_data: Dict[str, Any], url: str) -> None:
            Process the page data and save it to the appropriate location.

    """

    debug_enabled = False
    maximum_downloads = -1
    # wait a second after x files:
    pause_each_file = 100

    def __init__(self, global_config, download_to_directory):
        self.config = global_config
        self.base_download_directory = download_to_directory
        print("download_to_directory",download_to_directory)
        self.urls_to_download = UniqueStack()
        self.files_processed = []
        self.print_todo_list()

    def download_files(self) -> None:
        """
        Downloads files from a list of URLs.

        .. note::
           This method modifies the instance variable `urls_to_download` by pushing URLs to it.
           The URLs to be downloaded are passed as parameters to the method.

        :return: None

        Example usage:
            >>> dlMan = DownloadManager()
            >>> dlMan.download_files()

        Raises:
            Exception: If there was an error while downloading the files.
        """
        try:
            self.urls_to_download.push(self.config["page_base"] + self.config['page_sitemap'])
            self.urls_to_download.push_all(self.config["extra_paths"], self.config["page_base"])

            # if a Test is needed - pass url like this
            # self.urls_to_download.push(self.config['page_base']+self.config['page_sitemap'])
            # self.urls_to_download.push("http://ovetze.drkcms.de/index.php?eID=tx_cms_showpic&file=285&md5=deac577160968a505000907066ca9aa98ebff496&parameters%5B0%5D=eyJ3aWR0aCI6Ijc5MiIsImhlaWdodCI6IjYwMG0iLCJib2R5VGFnIjoiPGJvZHkg&parameters%5B1%5D=c3R5bGU9XCJtYXJnaW46MDsgYmFja2dyb3VuZDojZmZmO1wiPiIsIndyYXAiOiI8&parameters%5B2%5D=YSBocmVmPVwiamF2YXNjcmlwdDpjbG9zZSgpO1wiPiB8IDxcL2E%2BIn0%3D")

            self.print_todo_list()

            self.process_urls()
        except Exception as e:
            self.print_todo_list()
            print(e)
            raise e

    def print_todo_list(self) -> None:
        """
        Prints the todolist of the DownloadManager.

        :return: None
        """
        F.print_und_log("TODO:")
        F.print_und_log("-" * 50)
        self.urls_to_download.print_stack()
        F.print_und_log(("-" * 50) + "\n\n")

    def process_urls(self) -> None:
        """
        Process the URLs in the download manager.

        This method iterates through the URLs to download until there are no more URLs or the maximum number of downloads has been reached.

        :return: None
        """
        pause_each_file_num = 0
        status_file = 100
        while not self.urls_to_download.is_empty() and (self.maximum_downloads < 0 or self.maximum_downloads > 0):
            self.download_url(self.urls_to_download.pop())
            # wait a sec -> do not go to fast with the server of dt-internet
            if self.maximum_downloads > 0:  # is like a small "debug-mode", so print always:
                print("Files to download:", self.maximum_downloads, " - files as result:", len(self.files_processed))
            else:
                status_file -= 1
                if status_file == 0:
                    print("Files downloaded:", len(self.files_processed))
                    status_file = 100
            pause_each_file_num += 1
            if pause_each_file_num >= DownloadManager.pause_each_file:
                time.sleep(1)
                pause_each_file_num = 0
            self.maximum_downloads -= 1

    def __get_download_dir_structure_from(self, url: str) -> None:
        """
        Get the download directory structure from a given URL.

        :param url: The URL to parse.
        :return: The directory structure derived from the URL.
        """
        parsed_url = urlparse(url)
        paths = [path for path in parsed_url.path.split('/') if path]
        paths = paths[:-1]
        dir_name = os.path.sep.join(paths)
        return dir_name

    def __get_file_name_from(self, url: str) -> str:
        """
        :param url: The URL from which to extract the file name.
        :return: The extracted file name.
        """
        parsed_url = urlparse(url)
        paths = [path for path in parsed_url.path.split('/') if path]
        try:
            dl_file_name = paths[-1].split('#')[0]
        except IndexError:
            dl_file_name = NO_FILE_NAME + str(random.randint(100000, 1000000))
        return dl_file_name

    def download_url(self, url: str) -> None:
        """
        Download URL and process page data.

        :param url: The URL to download.
        :return: None

        """
        F.logInfo("\nNew URL: " + url)
        if self.url_is_valid(url):
            page_data = self.download_the_page_data(url)

            if page_data:
                self.process_page_data(page_data, url)
            else:
                F.logError("No page data found in URL:" + url)

    def process_page_data(self, page_data: Dict[str, Any], url: str) -> None:
        """
        Process the page data and save it to the appropriate location.

        :param page_data: A dictionary containing the data of the page.
        :param url: The URL of the page.
        :return: None

        """
        relativ_download_directory = self.__get_download_dir_structure_from(url)
        file_name = self.__get_file_name_from(url)
        full_download_path = os.path.join(self.base_download_directory, relativ_download_directory)

        if not DownloadManager.debug_enabled:
            os.makedirs(full_download_path, exist_ok=True)

        file_path_page = os.path.join(full_download_path, url.split('/')[-1])
        # file_path_pickle = os.path.join(full_download_path, url.split('/')[-1] + ".pkl")

        if DownloadManager.debug_enabled:
            F.print_und_log("\n\nNew File:", file_path_page)
            # F.print_und_log("Pickle File:", file_path_pickle)
            F.print_und_log("Directory:", relativ_download_directory)
            F.print_und_log("file_name:", file_name)
            F.print_und_log("content-type:", page_data["content-type"])
            F.print_und_log("Headers:", page_data["headers"])
            F.print_und_log("Encoding:", page_data["encoding"])
            F.print_und_log("page_title:", page_data["page_title"])
            F.print_und_log("-" * 50, "\n\n")
            F.print_und_log("Bilder:")
            for i, img in enumerate(page_data["images"], start=1):
                F.print_und_log(f"{i}.", img)
            F.print_und_log("os.path.basename(file_path_page)", os.path.basename(file_path_page))
            F.print_und_log("-" * 50, "\n\n")

        if len(page_data["images"]) > 0:
            self.urls_to_download.push_all(page_data["images"], self.config["page_base"])
            F.print_und_log("Bilder in Todo-Liste eingefügt - TODOs: " + str(self.urls_to_download.count()))
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
            pass  # happens if the picture is embedded in an iframe or a popup

        else:
            if not DownloadManager.debug_enabled:
                with open(file_path_page, 'wb') as file:
                    file.write(page_data['data'])
                image_file_data = {"filename": file_path_page,
                                   "url": page_data["url"],
                                   "headers": page_data["headers"]
                                   }
                self.files_processed.append(image_file_data)

    def get_absolute_url(self, base_url: str, relative_url: str) -> str:
        """
        :param base_url: The base URL to be used for constructing the absolute URL.
        :param relative_url: The relative URL to be appended to the base URL.
        :return: The absolute URL obtained by combining the base URL and the relative URL.

        """
        return base_url + relative_url if not relative_url.startswith('http') else relative_url

    def extract_new_download_links_from_html_content(self, html_content: Optional[BeautifulSoup]) -> None:
        """
        :param html_content: The HTML content from which to extract the download links.
        :return: A list of valid download links found in the HTML content.

        """
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
                    F.print_und_log("Link in Excluded_paths! Link:" + link["href"])

        self.urls_to_download.push_all(valid_urls, self.config["page_base"])

        if len(valid_urls) > 0:
            print("Number of links: " + str(self.urls_to_download.count()))

        if DownloadManager.debug_enabled:
            self.print_todo_list()

    def download_the_page_data(self, url: str) -> Dict[str, Any]:
        """
        Download the page data from the given URL.

        :param url: The URL of the page to download.
        :return: A dictionary containing the following information:
                 - "url": The URL of the downloaded page.
                 - "encoding": The encoding of the content.
                 - "content-type": The content type of the page.
                 - "headers": The headers of the response.
                 - "page_title": The title of the page.
                 - "data": The content of the page.
                 - "images": The URLs of the images in the page.
        :raises requests.exceptions.RequestException: If there is an error during the request.
        """
        try:
            response = requests.get(url)
            if response.status_code == 404:
                F.logError('Page Not Found:' + url)
                F.logError('Ignoring this download')
                page_data_content_type = IGNORE_DOWNLOAD
                if self.maximum_downloads > 0:
                    self.maximum_downloads += 1
            else:
                response.raise_for_status()
                page_data_content_type = response.headers['content-type']

            if "text/html" in page_data_content_type:
                # F.print_und_log("A html/text to download ->",page_data_content_type)

                soup = BeautifulSoup(response.text, 'html.parser')
                page_title = soup.title.string
                body = soup.find('body')
                self.extract_new_download_links_from_html_content(body)
                col3_content = soup.find('div', id='col3_content')

                if not col3_content:
                    F.logError("Kein konkreten Inhalt gefunden:" + url)
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

                    # if get_content_as_html:
                    content = str(col3_content)
                    # maybe helpfull later
                    # elif get_content_as_markdown:
                    #    markdown_converter = html2text.HTML2Text()
                    #    markdown_converter.ignore_links = False
                    #    content = markdown_converter.handle(str(col3_content))
                    # else:
                    #    content = col3_content.get_text()
            else:
                # F.print_und_log("A Picture or binary to download ->",page_data_content_type)
                page_title = 'FileDownload'
                content = response.content
                images = []

            return {"url": url,
                    "encoding": response.encoding,
                    "content-type": page_data_content_type,
                    "headers": response.headers,
                    "page_title": page_title,
                    "data": content,
                    "images": images}

        except requests.exceptions.RequestException as e:
            F.logException(f"Fehler beim Abrufen der Seite {url}: {e}")
            raise e

    def url_is_valid(self, url: str) -> bool:
        """
        Validates if the given URL is valid.

        :param url: The URL to validate.
        :return: True if the URL is valid, False otherwise.
        """
        file_path = self.__get_download_dir_structure_from(url) + "/" + self.__get_file_name_from(url)
        if ":" in file_path \
                or file_path.startswith("/" + NO_FILE_NAME):
            F.logError("URL is not valid: " + url)
            return False
        return True

    def save_filelist_to_pickle(self, pickle_filename: str) -> None:
        """
        :param pickle_filename: The name of the pickle file to save the file list to.
        :return: None
        """
        with open(pickle_filename, 'wb') as f_output:
            pickle.dump(self.files_processed, f_output)

    def load_filelist_from(self, filename: str) -> None:
        """
        Load a filelist from a given file.

        :param filename: The name of the file to load the filelist from.
        :return: None

        """
        with open(filename, 'rb') as f_input:
            self.files_processed = pickle.load(f_input)

    def get_files_to_prepare_for_upload(self) -> list[Any]:
        """
        Get the list of files to prepare for upload.

        :return: The list of files processed.
        """
        return self.files_processed

    def some_files_have_been_downloaded(self) -> bool:
        """
        Check if any files have been downloaded.

        :return: True if at least one file has been downloaded, False otherwise.
        :rtype: bool
        """
        return len(self.files_processed) > 0

    @classmethod
    def downloaded_pickle_suffix(cls):
        return '_files_after_download.pkl'

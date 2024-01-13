import os.path

import requests
from bs4 import BeautifulSoup
import html2text
import re


def get_absolute_url(base_url, relative_url):
    return base_url + relative_url if not relative_url.startswith('http') else relative_url


def get_all_urls_from_sitemap(base_url, sitemap_path, excluded_paths):
    try:
        response = requests.get(base_url+sitemap_path)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Abrufen der Sitemap: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    col3_content = soup.find('div', id='col3_content')
    links = col3_content.find_all('a') if col3_content else []

    urls = [get_absolute_url(base_url, link['href']) for link in links if
            'href' in link.attrs and not any(excluded_path in link['href'] for excluded_path in excluded_paths)]
    return urls


def scrape_page(url, get_content_as_html=True, get_content_as_markdown=False):
    try:
        response = requests.get(url)
        response.raise_for_status()
        # Fügen Sie hier Ihre Logik zum Extrahieren von Texten und Bildern ein
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Abrufen der Seite {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    col3_content = soup.find('div', id='col3_content')

    if not col3_content:
        return {"url": url, "data": "Kein Inhalt gefunden"}

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

    return {"url": url, "data": content, "images": images}


def download_all_pictures(base_url, pic_list, main_file_name, download_folder_name):
    for i, pic_url in enumerate(pic_list, start=1):
        # Bestimmen des Dateinamens für jedes Bild
        file_extension = pic_url.split('.')[-1]
        if len(file_extension) > 4:
            print("Unbekannte File Extension bei",main_file_name, "Bild nr.", i, "EXT:",file_extension)
            file_extension = "_original_file_.jpg"
            # TODO: Bilder die das enthalten, sind tatsächlich HTML-Daten => diese beinhalten eine URL mit einem Bild
            #       in einem weiteren IMG-Tag:
            #   <!DOCTYPE html>
            #   <html>
            #   <head>
            #   	<title>Image</title>
            #   	<meta name="robots" content="noindex,follow" />
            #   </head>
            #   <body style="margin:0; background:#fff;">
            #   	<img src="fileadmin/_processed_/csm_Neues_Titelbild_8451cc5bf5.jpg" alt="Image" title="Image" />
            #   </body>
            #   </html>

        image_filename = os.path.join(download_folder_name,f"{main_file_name}.{str(i).zfill(3)}.{file_extension}")

        # Herunterladen und Speichern des Bildes
        try:
            response = requests.get(base_url+pic_url)
            response.raise_for_status()
            with open(image_filename, 'wb') as file:
                file.write(response.content)
        except requests.exceptions.RequestException as e:
            print(f"Fehler beim Herunterladen des Bildes {pic_url}: {e}")


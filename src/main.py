import time
from datetime import datetime
import os.path
from common import F
import transferFuncs

test_me = False
#test_me = True

if __name__ == "__main__":
    config = {}

    if not os.path.exists(F.get_config_file_name()):
        # Create a Default setup on current project -> only once before first run!

        config['page_base'] = "http://ovetze.drkcms.de/"
        config['page_sitemap'] = "sonderseiten/sitemap.html"
        config['get_text'] = True
        config['get_pictures'] = True
        config['sleep_between_pages'] = 1
        config['excluded_paths'] = ["termine"]  # "news", "aktuelles"
        # TODO: feature: follow links on same base page?
        # TODO: feature: "pictures" found intern may contain html -> do not solve it at picture-download-function
        # TODO: feature: get also other high res pictures, not mentioned in text (hint is always "_processed_" dir name
        F.save_a_config(config)

    # load the latest config
    config = F.get_a_config_loaded()

    data_base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloaded")
    download_folder_name = os.path.join(data_base, "ovetze.drkcms.de-" + datetime.now().strftime("%Y-%m-%d--%H-%M"))
    os.makedirs(download_folder_name, exist_ok=True)

    urls = transferFuncs.get_all_urls_from_sitemap(config['page_base'],
                                                   config['page_sitemap'],
                                                   config["excluded_paths"])

    for url in urls:
        print("Bearbeite",url)
        page_data = transferFuncs.scrape_page(url)
        if page_data:
            file_path = os.path.join(download_folder_name, url.split('/')[-1] + ".txt")
            if test_me:
                print("\n\nNew File:", file_path)
                print("-" * 50, "\n\n")
                print(page_data)
                print("")
                for img in page_data["images"]:
                    print(img)
                print(os.path.basename(file_path))
                print("-" * 50, "\n\n")
            else:
                with open(file_path, 'w') as file:
                    file.write(str(page_data))
                transferFuncs.download_all_pictures(config['page_base'], page_data["images"], os.path.basename(file_path), download_folder_name)
        time.sleep(1)  # Verzögerung von 1 Sekunde zwischen den Anfragen

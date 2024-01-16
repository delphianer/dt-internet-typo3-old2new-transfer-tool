import time
from datetime import datetime
import os.path
from common import F
import transferFuncs
from UniqueStack import UniqueStack

test_me = False
#test_me = True

def get_and_prepare_config():
    cfg = {}
    if not os.path.exists(F.get_config_file_name()):
        # Create a Default setup on current project -> only once before first run!

        cfg['download_dir_prefix'] = "ovetze.drkcms.de-"
        cfg['page_base'] = "http://ovetze.drkcms.de/"
        cfg['page_sitemap'] = "sonderseiten/sitemap.html"
        cfg['get_text'] = True
        cfg['get_pictures'] = True
        cfg['sleep_between_pages'] = 1
        cfg['excluded_paths'] = ["termine", "news", "aktuelles"]
        cfg['extra_paths'] = ["sonderseiten/impressum.html",
                                 "sonderseiten/datenschutz.html"
                              # other excluded things...
                              ,"javascript:"
                              ]
        cfg['follow_links_on_same_page'] = True
        # TODO: feature: check encoding! all german special chars are wrong...
        # TODO: feature: "pictures" found intern may contain html -> do not solve it at picture-download-function
        # TODO: feature: get also other high res pictures, not mentioned in text (hint is always "_processed_" dir name
        F.save_a_config(cfg)
        print(f"New config saved to {F.get_config_file_name()}")
    # load the latest config
    cfg = F.get_a_config_loaded()
    data_base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloaded")
    dl_folder_name = os.path.join(data_base,
                                  cfg['download_dir_prefix'] + datetime.now().strftime("%Y-%m-%d--%H-%M"))
    F.initLogging("logs",cfg['download_dir_prefix'],True)
    if not test_me:
        os.makedirs(dl_folder_name, exist_ok=True)
    return cfg, dl_folder_name


# # # # # # #
# Main Part #
# # # # # # #
if __name__ == "__main__":
    config, download_folder_name = get_and_prepare_config()

    # get all urls from sitemap
    urls = transferFuncs.get_all_urls_from_sitemap(config['page_base'],
                                                   config['page_sitemap'],
                                                   config["excluded_paths"])

    urls_todo = UniqueStack()
    urls_todo.push_all(urls)
    urls_todo.push_all(config["extra_paths"], config["page_base"])

    if test_me:
        print("TODO:")
        print("-"*50)
        urls_todo.print_stack()
        print("-"*50,"\n\n")

    while not urls_todo.is_empty():

        url = urls_todo.pop()
        print("Bearbeite",url)

        page_data, new_urls = transferFuncs.scrape_page(url, config)

        urls_todo.push_all(new_urls)

        if test_me:
            if len(new_urls) > 0:
                print("\n\nNEW TODO:")
                print("-"*50)
                urls_todo.print_stack()
                print("-"*50,"\n\n")

        if page_data:
            directory, file_name = F.get_download_dir_structure_and_file_name_from(url)
            full_download_path = os.path.join(download_folder_name, directory)

            if not test_me:
                os.makedirs(full_download_path, exist_ok=True)

            file_path_page = os.path.join(full_download_path, url.split('/')[-1])
            file_path_json = os.path.join(full_download_path, url.split('/')[-1]+".json")

            if test_me:
                print("\n\nNew File:", file_path_page)
                print("JSON File:", file_path_json)
                print("Directory",directory)
                print("Name",file_name)
                print("-" * 50, "\n\n")
                print(page_data)
                print("")
                for img in page_data["images"]:
                    print(img)
                print(os.path.basename(file_path_page))
                print("-" * 50, "\n\n")
                new_urls = transferFuncs.download_all_pictures(page_data["images"],
                                                               os.path.basename(file_path_page),
                                                               full_download_path,
                                                               config,
                                                               test_me)

                urls_todo.push_all(new_urls)

                if len(new_urls) > 0:
                    print("\n\nNEW TODOs at PICTURE DOWNLOADS!:")
                    print("-" * 50)
                    urls_todo.print_stack()
                    print("-" * 50, "\n\n")
            else:
                with open(file_path_page, 'w') as file:
                    file.write(page_data["data"])
                with open(file_path_json, 'w') as file:
                    file.write(str(page_data))
                new_urls = transferFuncs.download_all_pictures(page_data["images"],
                                                               os.path.basename(file_path_page),
                                                               full_download_path,
                                                               config,
                                                               test_me)
                urls_todo.push_all(new_urls)

        time.sleep(1)  # Verzögerung von 1 Sekunde zwischen den Anfragen
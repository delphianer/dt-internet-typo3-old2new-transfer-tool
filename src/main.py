import glob
import pickle
from datetime import datetime
import os.path
from common import F
from DownloadManager import DownloadManager
from src.PreparationManager import PreparationManager


def get_and_prepare_config():
    cfg = {}
    if not os.path.exists(F.get_config_file_name()):
        # Create a Default setup on current project -> only once before first run!

        # todo: Typo3-Version für die Config festsetzen => neue Version braucht ggf. Anpassung
        cfg['download_dir_prefix'] = "ovetze.drkcms.de-"
        cfg['page_base'] = "http://ovetze.drkcms.de/"
        cfg['page_sitemap'] = "sonderseiten/sitemap.html"
        cfg['get_text'] = True
        cfg['get_pictures'] = True
        cfg['sleep_between_pages'] = 1
        cfg['excluded_paths'] = ["javascript:", "suche.html", "sonderseiten/drkde.html"] # "termine", "news", "aktuelles", -> auch News sind Seiten...
        cfg['extra_paths'] = ["sonderseiten/impressum.html",
                              "sonderseiten/datenschutz.html"]
        F.save_a_config(cfg)
        print(f"New config saved to {F.get_config_file_name()}")
    # load the latest config
    cfg = F.get_a_config_loaded()
    data_base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloaded")
    dl_folder_name = os.path.join(data_base,
                                  cfg['download_dir_prefix'] + datetime.now().strftime("%Y-%m-%d--%H-%M"))
    F.initLogging("logs",cfg['download_dir_prefix'],True)
    #if not DownloadManager.debug_enabled:
        #os.makedirs(dl_folder_name, exist_ok=True)
    return cfg, dl_folder_name


# # # # # # #
# Main Part #
# # # # # # #
if __name__ == "__main__":
    config, download_folder_name = get_and_prepare_config()

    # todo: change if other imports
    default_load = True
    default_load_number = 3

    files_processed = []
    DownloadManager.debug_enabled = input("Enter 'D' for enabling debug-mode: ").lower() == 'd'
    if default_load:
        download_or_load = "l"
    else:
        download_or_load = input("Enter 'L' for load old case or leave blank for download: ")
    pickle_file_to_load = ""
    dlMan = DownloadManager(config, download_folder_name)

    # 1. Step: Download files and gather web-data
    if download_or_load.lower() != 'l':
        if not DownloadManager.debug_enabled:
            num_downloads = input("Enter the number of maximum downloads or leave blank: ")
            if len(num_downloads) > 0:
                DownloadManager.maximum_downloads = int(num_downloads)
        dlMan.download_files()
        dlMan.save_filelist_to_pickle(download_folder_name+'_files_after_download.pkl')
    else:
        path = os.path.join(os.path.dirname(download_folder_name), '*.pkl')
        print("Suche im Pfad:",path)
        pkl_files = glob.glob(path)

        if len(pkl_files) > 0:
            for i, file in enumerate(pkl_files):
                print(f"{i}: {file}")

            if default_load:
                file_index = default_load_number
            else:
                file_index = int(input("Enter the index number of the file you want to load: "))
            if len(pkl_files) > file_index:
                pickle_file_to_load = pkl_files[file_index]
            else:
                print("Index not in Range")
        else:
            print("No file found")

    # 2. Step: Prepare Data to Upload
    # if pickle to load - print the stats first
    if len(pickle_file_to_load) > 0:
        dlMan.load_filelist_from(pickle_file_to_load)

    pagePrepMan = PreparationManager()

    if dlMan.has_files_downloaded():
        pagePrepMan.set_files_processed(dlMan.get_files_to_prepare_for_upload())
        pagePrepMan.print_download_stats()
        pagePrepMan.prepare_pages()

    # 3. Step: Use Typo3-API https://docs.typo3.org/m/typo3/reference-coreapi/main/en-us/Introduction/Index.html
    # TODO: read and use documentation
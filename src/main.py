from datetime import datetime
import os.path
from common import F
from DownloadManager import DownloadManager


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
    if not DownloadManager.debug_enabled:
        os.makedirs(dl_folder_name, exist_ok=True)
    return cfg, dl_folder_name


# # # # # # #
# Main Part #
# # # # # # #
if __name__ == "__main__":
    config, download_folder_name = get_and_prepare_config()

    # 1. Step: Download files and gather web-data
    dlMan = DownloadManager(config, download_folder_name)
    files_to_prepare_for_upload = dlMan.download_files()

    # 2. Step: Prepare Data to Upload


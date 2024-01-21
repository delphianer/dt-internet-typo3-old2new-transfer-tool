import logging
import os
import time
import platform
import hashlib
import json


# V13.01.2024

class F:
    error_count = 0
    exception_count = 0
    bad_error_count = 0
    importantMsgs = []
    do_print = False
    log_file_name = ""
    config_file_basepath = None
    config_file_name = "conf_main.json"
    __config_file = None

    @classmethod
    def isOs(cls, what):

        """Gibt das Betriebssystem zurück."""
        os = platform.system()

        if os == "Windows" and what == os:
            return True
        elif os == "Linux" and what == os:
            return True
        elif os == "Darwin" and what == os:
            return True
        else:
            return False

    @classmethod
    def isWindows(cls):
        return F.isOs("Windows")

    @classmethod
    def isMac(cls):
        return F.isOs("Darwin")

    @classmethod
    def initLogging(cls, logfile_dir_name, logfile_name, do_activate_print):

        # logging-setup
        datetime = time.strftime("%Y-%m-%d")
        logging_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), logfile_dir_name)
        if not os.path.exists(logging_directory):
            os.makedirs(logging_directory)

        logging_filename = f"{logfile_name}{datetime}_{platform.system()}.log"
        F.log_file_name = os.path.join(logging_directory, logging_filename)
        logging.basicConfig(filename=F.log_file_name,
                            filemode='a',
                            format='%(asctime)s : %(name)s - %(levelname)s - %(message)s',
                            level=logging.DEBUG)
        F.do_print = do_activate_print
        F.print_und_log("Logging initialisiert")
        F.print_und_log("Logfile = " + F.log_file_name)

    @classmethod
    def print_und_log(cls, msg, msg_part2 = "", msg_part3 = ""):
        if F.do_print:
            print(msg,msg_part2,msg_part3)
        logging.debug(msg)
        if msg_part2 is not None and len(msg_part2)>0:
            logging.debug(msg_part2)
        if msg_part3 is not None and len(msg_part3)>0:
            logging.debug(msg_part3)

    @classmethod
    def i(cls, *msg):
        if F.do_print:
            try:
                msg_out = ""
                for m in msg:
                    msg_out += str(m)
                print(msg_out)
            except Exception as ex:
                print(ex)
                for m in msg:
                    print(m)
        logging.info(msg)

    @classmethod
    def print_and_save(cls, msg):
        F.importantMsgs.append(msg)
        if F.do_print:
            print(msg)

    @classmethod
    def logWarning(cls, msg):
        logging.warning(msg)
        if F.do_print:
            print("Warn:" + msg)
        F.error_count += 1

    @classmethod
    def logError(cls, msg):
        F.print_and_save("-" * 50)
        F.print_and_save("----  ERROR: ---- " + msg)
        F.print_and_save("-" * 50)
        logging.error(msg)
        if F.do_print:
            print(msg)
        F.error_count += 1

    @classmethod
    def logException(cls, msg):
        F.print_and_save("##" * 50)
        if type(msg) == "str":
            F.print_and_save("#######  EXCEPTION WAS CALLED " + msg)
        F.print_and_save("##" * 50)
        logging.exception(msg)
        if F.do_print:
            print(msg)
        F.exception_count += 1

    @classmethod
    def print_important(cls):
        if F.do_print:
            for msg in F.importantMsgs:
                print(msg)

    @classmethod
    def get_any_error_count(cls):
        return F.error_count + F.exception_count + F.bad_error_count

    @classmethod
    def md5sum(cls, filename):
        """Calculates the MD5 checksum of a file.

        Args:
            filename: The path to the file.

        Returns:
            The MD5 checksum of the file.
        """
        hash_md5 = hashlib.md5()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @classmethod
    def __base_config_preparation(cls):
        if F.config_file_basepath == None:
            F.config_file_basepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
            if not os.path.exists(F.config_file_basepath):
                os.makedirs(F.config_file_basepath)
        F.__config_file = os.path.join(F.config_file_basepath, F.config_file_name)

    @classmethod
    def get_config_file_name(cls):
        F.__base_config_preparation()
        return F.__config_file


    @classmethod
    def save_a_config(cls, configObj):
        F.__base_config_preparation()
        with open(file=F.__config_file, encoding="UTF-8", mode="w") as file:
            json.dump(configObj, file)

    @classmethod
    def get_a_config_loaded(cls):
        F.__base_config_preparation()
        with open(file=F.__config_file, encoding="UTF-8", mode="r") as file:
            configObj = json.load(file)
            return configObj

    @classmethod
    def logInfo(cls, msg):
        logging.debug(msg)


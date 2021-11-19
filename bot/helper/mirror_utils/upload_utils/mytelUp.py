# Implement By SK
# All rights reserved

import os
import logging
import time
import requests
import subprocess
import glob

from pyrogram.errors import FloodWait

from bot import app, DOWNLOAD_DIR, AS_DOCUMENT, AS_DOC_USERS, AS_MEDIA_USERS
from bot.helper.ext_utils import fs_utils

LOGGER = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


class MytelUploader:

    def __init__(self, name=None, listener=None):
        self.__listener = listener
        self.name = name
        self.__app = app
        self.total_bytes = 0
        self.uploaded_bytes = 0
        self.last_uploaded = 0
        self.start_time = time.time()
        self.is_cancelled = False
        self.chat_id = listener.message.chat.id
        self.message_id = listener.uid
        self.user_id = listener.message.from_user.id
        self.sent_msg = self.__app.get_messages(self.chat_id, self.message_id)

    def upload(self):
        msgs_dict = {}
        path = f"{DOWNLOAD_DIR}{self.message_id}"
        for dirpath, subdir, files in sorted(os.walk(path)):
            for file in sorted(files):
                if self.is_cancelled:
                    return
                up_path = os.path.join(dirpath, file)
                f_size = os.path.getsize(up_path)
                if (int(f_size) >> 20) > 140:
                    # Greater than 140MB
                    LOGGER.info(f"File size: {int(f_size) >> 20} MB")
                    LOGGER.info(f"Splitting: {up_path}")
                    file_parts = self.split(up_path)
                else:
                    file_parts = [up_path]
                msgs_dict[file] = ""
                for file_part in sorted(file_parts):
                    self.upload_file(file_part)
                    msgs_dict[file] += self.single_msg
        LOGGER.info(f"MytelUpload Done: {self.name}")
        self.__listener.onUploadComplete(self.name, f_size, msgs_dict, None, None)

    def upload_file(self, up_path):
        burp0_headers = {"Sec-Ch-Ua": "\"Google Chrome\";v=\"95\", \"Chromium\";v=\"95\", \";Not A Brand\";v=\"99\"", "Sec-Ch-Ua-Mobile": "?0", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36", "Origin": "https://mycc.mytel.com.mm:9090", "Sec-Fetch-Site": "same-site", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Referer": "https://mycc.mytel.com.mm:9090/", "Accept-Encoding": "gzip, deflate", "Accept-Language": "en-US,en;q=0.9", "Connection": "close"}
        try:
            if self.is_cancelled:
                return
            # start upload
            url = "https://mycc.mytel.com.mm:9082/u"
            LOGGER.info("Uploading File: " + up_path)
            file_name = os.path.basename(up_path)
            LOGGER.info(file_name)
            files = {'fileUp': (file_name+".doc", open(up_path,'rb'), 'image/jpeg')}

            resp = requests.post(url, headers=burp0_headers, files=files,)
            if resp:
                resp = resp.json()
            LOGGER.info(resp['fileName'])
            LOGGER.info(resp['url'])
            self.single_msg = f"{resp['fileName']}\n{resp['url']}\n\n"

            if not self.is_cancelled:
                os.remove(up_path)
        except FloodWait as f:
            LOGGER.info(f)
            time.sleep(f.x)
    def split(self, up_path):
        out_path = up_path + "-part."
        subprocess.run(["split", "--numeric-suffixes=1", "--suffix-length=3", "-b 100M", up_path, out_path])
        os.remove(up_path)
        file_partlist = glob.glob(f'{out_path}*')
        LOGGER.info(file_partlist)
        return file_partlist

    def upload_progress(self, current, total):
        if self.is_cancelled:
            self.__app.stop_transmission()
            return
        chunk_size = current - self.last_uploaded
        self.last_uploaded = current
        self.uploaded_bytes += chunk_size

    def speed(self):
        try:
            return self.uploaded_bytes / (time.time() - self.start_time)
        except ZeroDivisionError:
            return 0

    def cancel_download(self):
        self.is_cancelled = True
        LOGGER.info(f"Cancelling Upload: {self.name}")
        self.__listener.onUploadError('your upload has been stopped!')

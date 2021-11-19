# Implement By SK
# All rights reserved

import os
import logging
import time
import requests

from pyrogram.errors import FloodWait
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

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
        self.user_settings()
        for dirpath, subdir, files in sorted(os.walk(path)):
            for file in sorted(files):
                if self.is_cancelled:
                    return
                up_path = os.path.join(dirpath, file)
                self.upload_file(up_path, file, dirpath)
                if self.is_cancelled:
                    return
                msgs_dict[file] = self.sent_msg.message_id
                self.last_uploaded = 0
        LOGGER.info(f"MytelUpload Done: {self.name}")
        self.__listener.onUploadComplete(self.name, None, msgs_dict, None, None)

    def upload_file(self, up_path, file, dirpath):
        burp0_headers = {"Sec-Ch-Ua": "\"Google Chrome\";v=\"95\", \"Chromium\";v=\"95\", \";Not A Brand\";v=\"99\"", "Sec-Ch-Ua-Mobile": "?0", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36", "Sec-Ch-Ua-Platform": "\"Windows\"", "Content-Type": "multipart/form-data", "Accept": "*/*", "Origin": "https://mycc.mytel.com.mm:9090", "Sec-Fetch-Site": "same-site", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Referer": "https://mycc.mytel.com.mm:9090/", "Accept-Encoding": "gzip, deflate", "Accept-Language": "en-US,en;q=0.9", "Connection": "close"}
        try:
            if self.is_cancelled:
                return
            # start upload
            url = "https://mycc.mytel.com.mm:9082/u"
            files = {'fileUp': (file+".doc", open(up_path,'rb'), 'image/jpeg')}

            resp = requests.post(url, headers=burp0_headers, files=files,).json()
            LOGGER.info(resp['fileName'])
            LOGGER.info(resp['url'])
            self.sent_msg = f"{resp['fileName']}\n{resp['url']}"
            sendMessage(self.sent_msg)

            if not self.is_cancelled:
                os.remove(up_path)
        except FloodWait as f:
            LOGGER.info(f)
            time.sleep(f.x)

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

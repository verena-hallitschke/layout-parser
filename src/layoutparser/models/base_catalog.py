# Copyright 2021 The Layout Parser team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import uuid
from typing import Any, Optional
from urllib.parse import urlparse

from iopath.common.download import download
from iopath.common.file_io import HTTPURLHandler, get_cache_dir, file_lock
from iopath.common.file_io import PathManager as PathManagerBase

# A trick learned from https://github.com/facebookresearch/detectron2/blob/65faeb4779e4c142484deeece18dc958c5c9ad18/detectron2/utils/file_io.py#L3


class DropboxHandler(HTTPURLHandler):
    """
    Supports download and file check for dropbox links
    """

    def _get_supported_prefixes(self):
        return ["https://www.dropbox.com"]

    def _isfile(self, path):
        return path.removesuffix("?dl=1") in self.cache_map
    
    def _get_local_path(
        self,
        path: str,
        force: bool = False,
        cache_dir: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        # Copy from iopath.common.file_io.HTTPURLHandler._get_local_path 
        # with small change to support ?dl=1 in dropbox links
        self._check_kwargs(kwargs)
        if (
            force
            or path not in self.cache_map
            or not os.path.exists(self.cache_map[path])
        ):
            logger = logging.getLogger(__name__)
            parsed_url = urlparse(path)
            dirname = os.path.join(
                get_cache_dir(cache_dir), os.path.dirname(parsed_url.path.lstrip("/"))
            )
            filename = path.split("/")[-1].removesuffix("?dl=1")
            if len(filename) > self.MAX_FILENAME_LEN:
                filename = filename[:100] + "_" + uuid.uuid4().hex

            cached = os.path.join(dirname, filename)
            with file_lock(cached):
                if not os.path.isfile(cached):
                    logger.info("Downloading {} ...".format(path))
                    cached = download(path, dirname, filename=filename)
            logger.info("URL {} cached in {}".format(path, cached))
            self.cache_map[path] = cached
        return self.cache_map[path]


PathManager = PathManagerBase()
PathManager.register_handler(DropboxHandler())

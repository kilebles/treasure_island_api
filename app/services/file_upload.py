import os
from typing import Callable, List, Optional
from uuid import uuid4

import aiofiles
from starlette.datastructures import UploadFile

from app.config import config


class FileExtNotAllowed(Exception):
    pass


class FileMaxSizeLimit(Exception):
    pass


class FileUpload:
    def __init__(
            self,
            uploads_dir: str = 'app/static/',
            allow_extensions: Optional[List[str]] = None,
            max_size: int = 1024 ** 3,
            filename_generator: Optional[Callable] = None,
            prefix: str = f'{config.APP_URL}/api/uploads/',
    ):
        self.max_size = max_size
        self.allow_extensions = allow_extensions
        self.uploads_dir = uploads_dir
        self.filename_generator = filename_generator
        self.prefix = prefix

    async def save_file(self, filename: str, content: bytes):
        file = os.path.join(self.uploads_dir, filename)
        async with aiofiles.open(file, "wb") as f:
            await f.write(content)
        return os.path.join(self.prefix, filename)

    async def upload(self, file: UploadFile):
        if self.filename_generator:
            filename = self.filename_generator(file)
        else:
            filename = f'{uuid4()}.{file.filename.split(".")[-1]}'

        content = await file.read()
        file_size = len(content)
        if file_size > self.max_size:
            raise FileMaxSizeLimit(f"File size {file_size} exceeds max size {self.max_size}")
        if self.allow_extensions:
            for ext in self.allow_extensions:
                if filename.endswith(ext):
                    raise FileExtNotAllowed(
                        f"File ext {ext} is not allowed of {self.allow_extensions}"
                    )
        return await self.save_file(filename, content)

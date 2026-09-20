import io
import random
import zipfile
from collections.abc import Callable
from typing import ClassVar, Literal

from PIL.Image import Image
from PIL.Image import new as newImage
from pydantic import BaseModel, ConfigDict, Field
from requests import Response

from lanraragi_api import LANraragiAPI
from lanraragi_api.base import MinionJobResponse
from tests.integration.util.minion_util import wait_minion_job_util


def gen_rand_image(width: int, height: int) -> Image:
    img = newImage(mode="RGB", size=(width, height))

    for x in range(width):
        for y in range(height):
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            img.putpixel((x, y), value=(r, g, b))
    return img


def img_to_bytes(img: Image, ext: str):
    img_buffer = io.BytesIO()
    img.save(img_buffer, format=ext)
    return img_buffer.getvalue()


def zip_images(img_dict: dict[str, Image], ext: Literal["PNG", "JPEG"]) -> bytes:
    """
    Args:
        img_dict: filename to Image mapping. Filenames should have no
            extension.
        ext: file format the images will be saved as. Currently only
            supports PNG and JPEG

    Returns:
        bytes: zipped file in bytes
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename, img in img_dict.items():
            filename = f"{filename}.{ext.lower()}"
            data = img_to_bytes(img, ext)
            zip_file.writestr(filename, data)

    _ = zip_buffer.seek(0)
    return zip_buffer.getvalue()


class ArchiveRawContent(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    img_dict: dict[str, Image] = Field(...)
    zip: bytes = Field(...)


def gen_test_archive(
    width: int = 170,
    height: int = 240,
    img_count: int = 10,
    ext: Literal["PNG", "JPEG"] = "PNG",
) -> ArchiveRawContent:
    imgs = [gen_rand_image(width, height) for _ in range(img_count)]
    digit_len = len(str(img_count))
    img_dict: dict[str, Image] = {}
    for i, img in enumerate(imgs):
        img_dict[f"{i:0{digit_len}}"] = img

    zip = zip_images(img_dict, ext)
    return ArchiveRawContent(img_dict=img_dict, zip=zip)


def get_thumbnail(api: LANraragiAPI, task: Callable[[], Response]):
    """The "Get thumbnail" APIs all require waiting for a minion job. So this
    function calls the task which encapsulates calling a "Get thumbnail" API,
    wait for the minion job to be done, and return the thumbnail in bytes.
    """
    while True:
        resp = task()
        if resp.status_code == 200:
            break
        assert resp.status_code == 202
        job_resp = api.archives.parse_model(MinionJobResponse, resp.json(), "")
        assert job_resp.success == 1
        job = job_resp.job
        assert job is not None
        wait_minion_job_util(api.minion, job, "finished")
    return resp.content

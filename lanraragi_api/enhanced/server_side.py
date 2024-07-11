# the same to server side's code
import hashlib
import re

from script_house.utils.FileSystemUtils import assert_is_file


def compute_id(file_path: str) -> str:
    """
    The archive id is determined only by the archive itself. So we can
    compute it on client side as well.

    see LANraragi/lib/LANraragi/Utils/Database.pm
    :param file_path: the file to the archive
    :return:
    """
    assert_is_file(file_path)
    try:
        # Read the first 512 KB of the file
        with open(file_path, 'rb') as file:
            data = file.read(512000)
    except IOError as e:
        raise Exception(f"Couldn't open {file_path}: {e}")

    # Compute the SHA-1 hash of the data
    sha1 = hashlib.sha1()
    sha1.update(data)
    digest = sha1.hexdigest()

    return digest


def is_archive(file_name):
    """

    see LANraragi/lib/LANraragi/Utils/Generic.pm
    :param file_name:
    :return:
    """
    return re.match(r'^.+\.(zip|rar|7z|tar|tar\.gz|lzma|xz|cbz|cbr|cb7|cbt|pdf|epub)$', file_name,
                    re.IGNORECASE) is not None

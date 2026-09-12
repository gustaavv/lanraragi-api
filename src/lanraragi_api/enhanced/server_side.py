# the same to server side's code
import hashlib
import os
import re


class ArchiveFileError(Exception):
    """Raised when an archive file cannot be accessed on disk."""


def compute_id(file_path: str) -> str:
    """Compute the archive ID of a file the same way the server does.

    The ID of an archive is determined only by the archive itself, so it can be
    computed on the client side as well.

    Args:
        file_path: Path of the archive file.

    Returns:
        str: Hexadecimal SHA-1 digest of the first 512 KB of the file.

    Raises:
        ArchiveFileError: If ``file_path`` is not a file, or if the file cannot
            be opened or read.

    Note:
        The algorithm matches the server side implementation in
        ``LANraragi/lib/LANraragi/Utils/Database.pm``.
    """
    if not os.path.isfile(file_path):
        raise ArchiveFileError(f"not a valid file path: {file_path}")
    try:
        # Read the first 512 KB of the file
        with open(file_path, "rb") as file:
            data = file.read(512000)
    except OSError as e:
        raise ArchiveFileError(f"Couldn't open {file_path}: {e}") from e

    # Compute the SHA-1 hash of the data
    sha1 = hashlib.sha1()
    sha1.update(data)
    digest = sha1.hexdigest()

    return digest


def is_archive(file_name):
    """Check whether a file name has a supported archive extension.

    Args:
        file_name: File name to test.

    Returns:
        bool: True if the name ends with ``zip``, ``rar``, ``7z``, ``tar``,
            ``tar.gz``, ``lzma``, ``xz``, ``cbz``, ``cbr``, ``cb7``, ``cbt``,
            ``pdf`` or ``epub``, compared case-insensitively. False otherwise.

    Note:
        The list of extensions matches the server side implementation in
        ``LANraragi/lib/LANraragi/Utils/Generic.pm``.
    """
    return (
        re.match(
            r"^.+\.(zip|rar|7z|tar|tar\.gz|lzma|xz|cbz|cbr|cb7|cbt|pdf|epub)$",
            file_name,
            re.IGNORECASE,
        )
        is not None
    )

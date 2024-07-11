import os
from os.path import join

import unicodedata

from lanraragi_api import LANrargiAPI
from lanraragi_api.Config import assert_use_untested_functions
from lanraragi_api.base.archive import Archive
from lanraragi_api.enhanced.server_side import is_archive, compute_id


def subfolders_to_artists(api: LANrargiAPI, dirname: str):
    """
    Walk through dirname, and set artist tag for those archives without artist tag.
    For every archive, the artist will be the name of its parent folder.

    This function is similar to Subfolders to Categories, but has better performance.

    :param api: LANrargiAPI instance
    :param dirname: content folder
    :return:
    """
    archives = api.archive.get_all_archives()
    map: dict[str, list[Archive]] = {}
    # possibly duplicate archive names
    for a in archives:
        k = unicodedata.normalize('NFC', a.title)
        if k not in map:
            map[k] = list()
        map[k].append(a)
    skip_count = 0
    update_count = 0
    for root, dirs, files in os.walk(dirname):
        for f in files:
            if not is_archive(f):
                continue
            f = unicodedata.normalize('NFC', f)
            f2 = f[:f.rfind('.')].strip()  # remove file extension
            if f2 not in map:
                continue
            if len(map[f2]) > 1:
                # only call compute_id if there are duplicates to improve performance
                id = compute_id(join(root, f))
                a = [a for a in map[f2] if a.arcid == id]
                if len(a) == 0:
                    continue
                a = a[0]
            else:
                a = map[f2][0]

            if a.has_artists():
                skip_count += 1
                continue
            _, subfolder = os.path.split(root)
            update_count += 1
            assert_use_untested_functions()
            continue  # TODO: untested
            a.set_artists([subfolder])
            api.archive.update_archive_metadata(a)
    print(f'archives skipped count: {skip_count} , updated count:  {update_count}')

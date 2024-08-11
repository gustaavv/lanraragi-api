import os
from os.path import join

import unicodedata

from lanraragi_api import LANraragiAPI
from lanraragi_api.base.archive import Archive
from lanraragi_api.enhanced.server_side import is_archive, compute_id


def subfolders_to_artists(api: LANraragiAPI, dirname: str):
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
            a.set_artists([subfolder])
            api.archive.update_archive_metadata(a.arcid, a)
    print(f'archives skipped count: {skip_count} , updated count:  {update_count}')


def remove_all_categories(api: LANraragiAPI):
    """
    For every category, remove all the archives it contains. After that, all the
    categories are removed.
    :param api:
    :return:
    """
    cs = api.category.get_all_categories()
    for c in cs:
        for aid in c.archives:
            result = api.category.remove_archive_from_category(c.id, aid)
        print(f'remove {len(c.archives)} from category {c.id}:{c.name}')
    for c in cs:
        result = api.category.delete_category(c.id)
    print(f'remove {len(cs)} categories')

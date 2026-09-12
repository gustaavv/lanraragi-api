import os
import unicodedata
from os.path import join

from lanraragi_api import LANraragiAPI
from lanraragi_api.base.archive import ArchiveMetadata
from lanraragi_api.enhanced.server_side import compute_id, is_archive


def subfolders_to_artists(api: LANraragiAPI, dirname: str):
    """Set the artist tag of archives to the name of their parent folder.

    Walks through ``dirname`` and, for every archive that has no artist tag
    yet, sets its artist tag to the name of the subfolder holding it. Archives
    that already have an artist tag are skipped.

    This function is similar to Subfolders to Categories, but has better
    performance.

    Args:
        api: LANraragiAPI instance used to read and update the archives.
        dirname: Content folder whose subfolders give the artist tags.

    Note:
        This function modifies archive metadata on the server. Archives are
        looked up by title, and the archive ID is computed from the file only
        when several archives share the same title. A summary of the skipped
        and updated archives is printed.
    """
    archives = api.archives.get_all_archives()
    map: dict[str, list[ArchiveMetadata]] = {}
    # possibly duplicate archive names
    for a in archives:
        k = unicodedata.normalize("NFC", a.title)
        if k not in map:
            map[k] = []
        map[k].append(a)
    skip_count = 0
    update_count = 0
    for root, dirs, files in os.walk(dirname):
        for f in files:
            if not is_archive(f):
                continue
            f = unicodedata.normalize("NFC", f)
            f2 = f[: f.rfind(".")].strip()  # remove file extension
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
            api.archives.update_archive_metadata(a.arcid, a)
    print(f"archives skipped count: {skip_count} , updated count:  {update_count}")


def remove_all_categories(api: LANraragiAPI):
    """Remove every archive from every category, then delete the categories.

    For every category, all the archives it contains are removed from it. After
    that, all the categories are removed.

    Args:
        api: LANraragiAPI instance used to read and modify the categories.

    Note:
        Every category of the server is deleted. Removing the archives from a
        category does not delete the archives themselves. The number of removed
        archives and categories is printed.
    """
    cs = api.categories.get_all_categories()
    for c in cs:
        for aid in c.archives:
            api.categories.remove_archive_from_category(c.id, aid)
        print(f"remove {len(c.archives)} from category {c.id}:{c.name}")
    for c in cs:
        api.categories.delete_category(c.id)
    print(f"remove {len(cs)} categories")

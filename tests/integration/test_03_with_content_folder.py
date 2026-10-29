from os.path import join
from pathlib import Path
from typing import cast

import pytest
from pydantic import BaseModel, Field

from lanraragi_api import LANraragiAPI
from lanraragi_api.enhanced.script import remove_all_categories, subfolders_to_artists
from lanraragi_api.enhanced.server_side import compute_id
from lanraragi_api.entity.archive import ArchiveMetadata, ArchiveTags
from tests.integration.conftest import integration_test_setup, integration_test_teardown
from tests.integration.util.archive_util import gen_test_archive

pytestmark = pytest.mark.order(3)


@pytest.fixture(scope="module", autouse=True)
def module_setup_and_cleanup(tmp_path_factory: pytest.TempPathFactory):
    content_dir = tmp_path_factory.mktemp("test_03") / "content"
    content_dir.mkdir()
    content_dir = str(content_dir)

    gen_archives_in_content_folder(content_dir)

    integration_test_teardown(content_dir)
    integration_test_setup(content_dir)

    yield content_dir

    integration_test_teardown(content_dir)


def gen_archives_in_content_folder(content_dir: str):
    a1 = Path(content_dir) / "a1"
    a1.mkdir()
    z1 = gen_test_archive(img_count=10)
    _ = (a1 / "z1.zip").write_bytes(z1.zip)

    a2 = Path(content_dir) / "a2_intermediate" / "a2"
    a2.mkdir(parents=True)
    z2 = gen_test_archive(img_count=9)
    z3 = gen_test_archive(img_count=7)
    _ = (a2 / "z2.zip").write_bytes(z2.zip)
    _ = (a2 / "z3.zip").write_bytes(z3.zip)


class SharedState(BaseModel):
    content_dir: str = Field(...)


@pytest.fixture(scope="module")
def shared_state(module_setup_and_cleanup: str):
    return SharedState(content_dir=module_setup_and_cleanup)


def sort_fn_archive_by_tile(a: ArchiveMetadata):
    return a.title


class TestEnhancedServerSide:
    def test_compute_id(self, api: LANraragiAPI, shared_state: SharedState):
        archiveApi = api.archives
        content_dir = shared_state.content_dir

        archives = archiveApi.get_all_archives()
        assert len(archives) == 3

        archives.sort(key=sort_fn_archive_by_tile)
        assert [a.title for a in archives] == ["z1", "z2", "z3"]
        z1p = str(join(content_dir, "a1", "z1.zip"))
        assert archives[0].arcid == compute_id(z1p)
        z2p = str(join(content_dir, "a2_intermediate", "a2", "z2.zip"))
        assert archives[1].arcid == compute_id(z2p)
        z3p = str(join(content_dir, "a2_intermediate", "a2", "z3.zip"))
        assert archives[2].arcid == compute_id(z3p)


class TestEnhancedScript:
    def test_remove_all_categories(self, api: LANraragiAPI):
        archiveApi = api.archives
        categoryApi = api.categories

        # add an archive to a category first
        archives = archiveApi.get_all_archives()
        assert len(archives) == 3
        a1 = next(a for a in archives if a.title == "z1")

        resp = categoryApi.create_category("c1")
        assert resp.success == 1
        cid = cast(str, resp.category_id)  # pyright: ignore[reportAttributeAccessIssue]
        cat = categoryApi.get_category(cid)
        assert cat is not None
        assert cat.name == "c1"

        resp = categoryApi.add_archive_to_category(cid, a1.arcid)
        assert resp.success == 1

        cat = categoryApi.get_category(cid)
        assert cat is not None
        assert cat.archives == [a1.arcid]

        remove_all_categories(api)

        categoryApi = api.categories
        cats = categoryApi.get_all_categories()
        assert len(cats) == 0

        # no archive will be removed
        archives = archiveApi.get_all_archives()
        assert len(archives) == 3

    def test_subfolders_to_artists(self, api: LANraragiAPI, shared_state: SharedState):
        archiveApi = api.archives

        archives = archiveApi.get_all_archives()
        assert len(archives) == 3
        a = next(a for a in archives if a.title == "z3")
        new_tags = ArchiveTags(a.tags)
        new_tags.set_artists(["ac1", "ac2"])
        resp = archiveApi.update_archive_metadata(
            id=a.arcid, title="z3", tags=new_tags.tags
        )
        assert resp.success == 1

        subfolders_to_artists(api, shared_state.content_dir)

        archives = archiveApi.get_all_archives()
        assert len(archives) == 3

        archives.sort(key=sort_fn_archive_by_tile)
        assert [a.title for a in archives] == ["z1", "z2", "z3"]
        assert ArchiveTags(archives[0].tags).get_artists() == ["a1"]
        assert ArchiveTags(archives[1].tags).get_artists() == ["a2"]
        # subfolders_to_artists only updates archives without artist tag
        assert ArchiveTags(archives[2].tags).get_artists() == ["ac1", "ac2"]

import hashlib
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import cast
from urllib.parse import parse_qs, urlparse

import pytest
from pydantic import BaseModel, Field

from lanraragi_api import LANraragiAPI
from lanraragi_api.base import (
    APIHttpError,
    APIResponseDecodeError,
    DatabaseBackup,
    StampsData,
)
from tests.integration.util.archive_util import (
    ArchiveRawContent,
    gen_test_archive,
    get_thumbnail,
    img_to_bytes,
)
from tests.integration.util.minion_util import wait_minion_job_util

pytestmark = pytest.mark.order(2)


class SharedState(BaseModel):
    archives: dict[str, ArchiveRawContent] = Field(default={})
    cids: set[str] = Field(default=set())
    tids: set[str] = Field(default=set())

    def get_archive_id(self):
        """Get an archive id for testing in a deterministic way."""
        assert len(self.archives) > 0
        aid = min(self.archives.keys())
        return aid

    def get_category_id(self):
        """Get a category id for testing in a deterministic way."""
        assert len(self.cids) > 0
        cid = min(self.cids)
        return cid

    def get_tankoubon_id(self):
        """Get a tankoubon id for testing in a deterministic way."""
        assert len(self.tids) > 0
        tid = min(self.tids)
        return tid


@pytest.fixture(scope="module")
def shared_state():
    return SharedState()


class TestArchives:
    def test_upload_archive_1(self, api: LANraragiAPI, shared_state: SharedState):
        archiveApi = api.archives
        z = gen_test_archive(img_count=10)
        # upload with zip file in memory
        resp = archiveApi.upload_archive(("z1.zip", z.zip))
        assert resp.success == 1
        assert resp.operation == "upload"

        archives = archiveApi.get_all_archives()
        assert len(archives) == 1
        archive = archives[0]
        assert archive.arcid == resp.id  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        shared_state.archives[archive.arcid] = z

        assert archive.extension == "zip"
        assert archive.filename == "z1"
        assert archive.isnew == True
        assert archive.pagecount == 10
        assert archive.size == len(z.zip)
        assert "date_added:" in archive.tags
        assert archive.title == "z1"
        assert archive.summary == ""

        # duplicate archive
        resp = archiveApi.upload_archive(("z2.zip", z.zip))
        assert resp.success == 0
        assert resp.error is not None
        assert "This file already exists in the Library" in resp.error
        assert resp.id == archive.arcid  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

        archives = archiveApi.get_all_archives()
        assert len(archives) == 1
        assert archives[0].arcid == archive.arcid

    def test_upload_archive_2(
        self, api: LANraragiAPI, tmp_path: Path, shared_state: SharedState
    ):
        archiveApi = api.archives
        z = gen_test_archive(img_count=15)
        # upload with zip file on disk

        d = tmp_path / "zip_folder"
        d.mkdir()
        zf = d / "z.zip"
        _ = zf.write_bytes(z.zip)

        # checksum mismatch
        wrong_sha1 = "0" * 40
        resp = archiveApi.upload_archive(str(zf), file_checksum=wrong_sha1)

        assert resp.success == 0
        assert resp.error is not None
        assert "Checksum mismatch" in resp.error

        archives = archiveApi.get_all_archives()
        assert len(archives) == 1
        assert archives[0].title == "z1"

        # upload with zip file on disk
        # use all the parameters when uploading the archive
        sha1 = hashlib.sha1()
        sha1.update(z.zip)
        correct_sha1 = sha1.hexdigest()
        resp = archiveApi.upload_archive(
            str(zf),
            title="z3",
            tags="k1:v1, k2:v21, k2:v22, v3, v4",
            summary="a randomly generated file",
            file_checksum=correct_sha1,
        )

        new_uploaded_id = cast(str, resp.id)  # pyright: ignore[reportAttributeAccessIssue]
        shared_state.archives[new_uploaded_id] = z
        assert resp.success == 1
        assert resp.operation == "upload"

        archives = archiveApi.get_all_archives()
        assert len(archives) == 2
        assert sorted([a.arcid for a in archives]) == sorted(
            shared_state.archives.keys()
        )
        assert sorted([a.title for a in archives]) == sorted(["z1", "z3"])
        assert sorted([a.filename for a in archives]) == sorted(["z", "z1"])

        archive = archiveApi.get_archive(new_uploaded_id)
        assert archive is not None
        assert archive.extension == "zip"
        assert archive.isnew == True
        assert archive.pagecount == 15
        assert archive.size == len(z.zip)
        # lrr will format tags in the request to remove the spaces
        assert "k1:v1,k2:v21,k2:v22,v3,v4" in archive.tags
        # date_added will also be added to the tag although we set it manually
        assert "date_added" in archive.tags
        assert archive.title == "z3"
        assert archive.summary == "a randomly generated file"

    def test_update_archive_metadata(
        self, api: LANraragiAPI, shared_state: SharedState
    ):
        archiveApi = api.archives

        # update an existing archive

        aid = shared_state.get_archive_id()
        oldArchive = archiveApi.get_archive(aid)
        assert oldArchive is not None

        resp = archiveApi.update_archive_metadata(
            aid, title=oldArchive.title, summary="test update archive metadata"
        )
        assert resp.success == 1
        assert resp.operation == "update_metadata"

        newArchive = archiveApi.get_archive(aid)
        assert newArchive is not None
        assert newArchive.title == oldArchive.title
        assert newArchive.summary == "test update archive metadata"
        # tags is not set when calling the api, so the request field is None,
        # and lrr converts it to an empty string
        assert newArchive.tags == ""

    def test_archive_new_flag(self, api: LANraragiAPI, shared_state: SharedState):
        archiveApi = api.archives
        aid = shared_state.get_archive_id()

        def set_and_check():
            resp = archiveApi.set_archive_new_flag(aid)
            assert resp.success == 1
            assert resp.operation == "add_new"

            archive = archiveApi.get_archive_metadata(aid)
            assert archive is not None
            assert archive.isnew

        def clear_and_check():
            resp = archiveApi.clear_archive_new_flag(aid)
            assert resp.success == 1
            assert resp.operation == "clear_new"

            archive = archiveApi.get_archive_metadata(aid)
            assert archive is not None
            assert not archive.isnew

        for _ in range(2):
            archive = archiveApi.get_archive_metadata(aid)
            assert archive is not None
            if archive.isnew:
                # run twice for idempotency check
                for _ in range(2):
                    clear_and_check()
            else:
                # run twice for idempotency check
                for _ in range(2):
                    set_and_check()

    def test_archive_toc(self, api: LANraragiAPI, shared_state: SharedState):
        archiveApi = api.archives
        aid = shared_state.get_archive_id()

        archive = archiveApi.get_archive(aid)
        assert archive is not None
        assert archive.pagecount > 5

        def add_tocs(tocs: dict[int, str]):
            for p, title in tocs.items():
                resp = archiveApi.add_archive_toc(aid, p, title)
                assert resp.success == 1
                assert resp.operation == "add_toc"
                assert resp.successMessage == f"Added ToC entry for page {p}."

            archive = archiveApi.get_archive(aid)
            assert archive is not None
            assert archive.toc is not None
            assert sorted({t["page"]: t["name"] for t in archive.toc}) == sorted(tocs)

        tocs1 = {1: "p1", 3: "p3"}
        # add tocs
        add_tocs(tocs1)
        tocs2 = {1: "p1_1", 2: "p2", 3: "p3_1"}
        # put tocs
        add_tocs(tocs2)

        # delete_tocs, also check idempotency by deleting twice
        for p in list(tocs2) * 2:
            resp = archiveApi.delete_archive_toc(aid, p)
            assert resp.success == 1
            assert resp.operation == "remove_toc"
            assert resp.successMessage == f"Removed ToC entry for page {p}."

        archive = archiveApi.get_archive(aid)
        assert archive is not None
        assert archive.toc == []

    def test_archive_thumbnail(self, api: LANraragiAPI, shared_state: SharedState):
        archiveApi = api.archives
        minionApi = api.minion
        aid = shared_state.get_archive_id()

        archive = archiveApi.get_archive(aid)
        assert archive is not None
        assert archive.pagecount > 5

        page_thumbnail_map: dict[int, bytes] = {}

        # get thumbnails
        for p in range(1, 4):

            def task(p: int = p):
                return archiveApi.get_archive_thumbnail(aid, page=p, no_fallback=True)

            thumbnail = get_thumbnail(api, task)
            page_thumbnail_map[p] = thumbnail

        # update thumbnail
        new_thumb_page = 2
        resp = archiveApi.update_thumbnail(aid, page=new_thumb_page)
        assert resp.success == 1
        assert resp.operation == "update_thumbnail"

        resp = archiveApi.get_archive_thumbnail(aid, page=new_thumb_page)
        assert resp.status_code == 200
        assert page_thumbnail_map[new_thumb_page] == resp.content

        # create thumbnails for every page
        while True:
            resp = archiveApi.queue_extraction_of_page_thumbnails(aid)
            assert resp.success == 1
            job = resp.job
            if job is None:
                assert resp.message == "No job queued, all thumbnails already exist."  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                break

            _ = minionApi.get_basic_status(job)
            _ = minionApi.get_full_status(job)
            time.sleep(1)

    def test_download_archive(self, api: LANraragiAPI, shared_state: SharedState):
        archiveApi = api.archives
        aid = shared_state.get_archive_id()

        archive = archiveApi.get_archive(aid)
        assert archive is not None

        resp = archiveApi.download_archive(aid)
        assert resp.status_code == 200
        assert resp.content == shared_state.archives[aid].zip

    def test_extract_archive(self, api: LANraragiAPI, shared_state: SharedState):
        archiveApi = api.archives
        aid = shared_state.get_archive_id()
        raw_data = shared_state.archives[aid]

        archive = archiveApi.get_archive(aid)
        assert archive is not None

        resp = archiveApi.extract_archive(aid)
        # job: int = resp["job"]

        pages: list[str] = resp["pages"]
        assert len(pages) == archive.pagecount

        for p in pages:
            url = urlparse(p)
            assert url.path == f"/api/archives/{aid}/page"

            query_dict = parse_qs(url.query)
            assert "path" in query_dict

            path = query_dict["path"]
            assert len(path) == 1
            path = path[0]

            basename = os.path.basename(path)
            name, ext = basename.split(".")
            assert name in raw_data.img_dict
            page_data = img_to_bytes(raw_data.img_dict[name], ext)

            resp = archiveApi.get_archive_page(aid, path)
            assert resp.status_code == 200
            assert resp.content == page_data

    def test_reading_progress(self, api: LANraragiAPI, shared_state: SharedState):
        archiveApi = api.archives
        miscApi = api.misc

        aid = shared_state.get_archive_id()
        archive = archiveApi.get_archive(aid)
        assert archive is not None
        assert archive.pagecount > 5

        si = miscApi.get_server_information()

        for p in [1, 3]:
            resp = archiveApi.update_reading_progression(aid, page=p)
            assert resp.operation == "update_progress"

            if resp.success == 1:
                archive = archiveApi.get_archive(aid)
                assert archive is not None
                assert archive.progress == p
                assert archive.lastreadtime == cast(int, resp.lastreadtime)  # pyright: ignore[reportAttributeAccessIssue]
                assert si.server_tracks_progress
            else:
                assert (
                    resp.error
                    == "Server-side Progress Tracking is disabled on this instance."
                )
                assert not si.server_tracks_progress

    def test_delete_archive(self, api: LANraragiAPI, shared_state: SharedState):
        archiveApi = api.archives
        aid = shared_state.get_archive_id()

        archive = archiveApi.get_archive(aid)
        assert archive is not None

        old_num = len(shared_state.archives)
        archives = archiveApi.get_all_archives()
        assert old_num == len(archives)

        resp = archiveApi.delete_archive(aid)
        assert resp.success == 1
        assert resp.operation == "delete_archive"
        assert cast(str, resp.id) == aid  # pyright: ignore[reportAttributeAccessIssue]
        # resp.filename is the full path, not aligned with the doc
        assert cast(str, resp.filename).endswith(  # pyright: ignore[reportAttributeAccessIssue]
            f"{archive.filename}.{archive.extension}"
        )

        new_num = old_num - 1
        del shared_state.archives[aid]

        archive = archiveApi.get_archive(aid)
        assert archive is None

        archives = archiveApi.get_all_archives()
        assert new_num == len(archives)
        assert sorted([a.arcid for a in archives]) == sorted(
            shared_state.archives.keys()
        )


class TestSearch:
    def test_search_archives(self, api: LANraragiAPI, shared_state: SharedState):
        searchApi = api.search
        result = searchApi.search_archives()
        assert result.recordsTotal == len(shared_state.archives)
        assert all((a.arcid in shared_state.archives) for a in result.data)

    def test_search_archive_ids(self, api: LANraragiAPI, shared_state: SharedState):
        searchApi = api.search
        result = searchApi.search_archive_ids()
        assert result.recordsTotal == len(shared_state.archives)
        assert all((aid in shared_state.archives) for aid in result.data)

    def test_search_random_archive(self, api: LANraragiAPI, shared_state: SharedState):
        searchApi = api.search

        for i in range(1, 5):
            archives = searchApi.get_random_archives(count=i)
            assert len(archives) == min(i, len(shared_state.archives))
            assert all((a.arcid in shared_state.archives) for a in archives)


class TestCategories:
    def test_create_categories(self, api: LANraragiAPI, shared_state: SharedState):
        # this test case is mainly for creating 2 categories for later use
        # since we have test crud operation for categories in
        # test_01_new_instance.py#test_basic_crud_categories

        categoryApi = api.categories

        cats = categoryApi.get_all_categories()
        assert len(cats) == 0

        def create_and_assert(name: str) -> str:
            resp = categoryApi.create_category(name)
            assert resp.success == 1
            assert resp.operation == "create_category"
            new_cid = cast(str, resp.category_id)  # pyright: ignore[reportAttributeAccessIssue]

            cat = categoryApi.get_category(new_cid)
            assert cat is not None
            assert cat.name == name
            assert not cat.pinned
            assert cat.search == ""

            return new_cid

        cid1 = create_and_assert("c1")
        cats = categoryApi.get_all_categories()
        assert len(cats) == 1
        assert sorted([c.id for c in cats]) == [cid1]
        assert sorted([c.name for c in cats]) == ["c1"]

        cid2 = create_and_assert("c2")
        cats = categoryApi.get_all_categories()
        assert len(cats) == 2
        assert sorted([c.id for c in cats]) == sorted([cid1, cid2])
        assert sorted([c.name for c in cats]) == ["c1", "c2"]

        shared_state.cids.add(cid1)
        shared_state.cids.add(cid2)

    def test_bookmark_link(self, api: LANraragiAPI, shared_state: SharedState):
        categoryApi = api.categories
        cid = shared_state.get_category_id()

        def get_bookmark_link_category() -> str:
            resp = categoryApi.get_bookmark_link()
            assert resp["operation"] == "get_bookmark_link"
            assert resp["success"] == 1
            assert "category_id" in resp

            return resp["category_id"]

        def disable_bookmark_link() -> str:
            resp = categoryApi.disable_bookmark_feature()
            assert resp.success == 1
            assert resp.operation == "remove_bookmark_link"

            last_cid = cast(str, resp.category_id)  # pyright: ignore[reportAttributeAccessIssue]
            return last_cid

        def update_bookmark_link(cid: str):
            resp = categoryApi.update_bookmark_link(cid)
            assert resp.success == 1
            assert resp.operation == "update_bookmark_link"

        for _ in range(2):
            link_cid = get_bookmark_link_category()
            if link_cid == "":
                # run twice for idempotency check
                update_bookmark_link(cid)
                assert cid == get_bookmark_link_category()
                update_bookmark_link(cid)
                assert cid == get_bookmark_link_category()
            else:
                # run twice for idempotency check
                assert cid == disable_bookmark_link()
                assert "" == get_bookmark_link_category()
                assert "" == disable_bookmark_link()
                assert "" == get_bookmark_link_category()

    def test_with_archive(self, api: LANraragiAPI, shared_state: SharedState):
        categoryApi = api.categories
        archiveApi = api.archives

        aid = shared_state.get_archive_id()
        cid = shared_state.get_category_id()

        cat = categoryApi.get_category(cid)
        assert cat is not None
        assert len(cat.archives) == 0

        # run twice for idempotency check
        for _ in range(2):
            resp = categoryApi.add_archive_to_category(cid, aid)
            assert resp.success == 1

            cat = categoryApi.get_category(cid)
            assert cat is not None
            assert len(cat.archives) == 1
            assert cat.archives == [aid]

            cats = archiveApi.get_archive_categories(aid)
            assert len(cats) == 1
            assert cats == [cat]

        # run twice for idempotency check
        for _ in range(2):
            resp = categoryApi.remove_archive_from_category(cid, aid)
            assert resp.success == 1

            cat = categoryApi.get_category(cid)
            assert cat is not None
            assert len(cat.archives) == 0

            cats = archiveApi.get_archive_categories(aid)
            assert len(cats) == 0


class TestTankoubons:
    def test_crud_tankoubons(self, api: LANraragiAPI, shared_state: SharedState):
        tankoubonApi = api.tankoubons

        tanks = tankoubonApi.get_all_tankoubons()
        assert len(tanks) == 0

        # create tank
        resp = tankoubonApi.create_tankoubon("t1")
        assert resp.success == 1
        assert resp.operation == "create_tankoubon"

        tid = cast(str, resp.tankoubon_id)  # pyright: ignore[reportAttributeAccessIssue]

        tank = tankoubonApi.get_tankoubon(tid)
        assert tank.name == "t1"

        tanks = tankoubonApi.get_all_tankoubons()
        assert len(tanks) == 1
        assert tanks == [tank]

        shared_state.tids.add(tid)

        # update tank name
        resp = tankoubonApi.create_tankoubon("t2", tankid=tid)
        assert resp.success == 1
        assert resp.operation == "create_tankoubon"

        tank = tankoubonApi.get_tankoubon(tid)
        assert tank.name == "t2"

        tanks = tankoubonApi.get_all_tankoubons()
        assert len(tanks) == 1
        assert tanks == [tank]

        # delete tank
        resp = tankoubonApi.create_tankoubon("t3")
        assert resp.success == 1
        assert resp.operation == "create_tankoubon"

        tid2 = cast(str, resp.tankoubon_id)  # pyright: ignore[reportAttributeAccessIssue]
        tanks = tankoubonApi.get_all_tankoubons()
        assert len(tanks) == 2
        assert sorted([t.tankid for t in tanks]) == sorted([tid, tid2])

        # run twice for idempotency check
        for _ in range(2):
            resp = tankoubonApi.delete_tankoubon(tid2)
            assert resp.success == 1
            tanks = tankoubonApi.get_all_tankoubons()
            assert len(tanks) == 1
            assert tanks == [tank]

        # update tank
        resp = tankoubonApi.update_tankoubon(
            tid,
            name="t2",
            tags="k1:v1, k2:v21, k2:v22, v3, v4",
            summary="a test tankoubon",
        )
        assert resp.success == 1
        tank = tankoubonApi.get_tankoubon(tid)
        assert tank.name == "t2"
        # lrr will format tags in the request to remove the spaces
        assert tank.tags == "k1:v1,k2:v21,k2:v22,v3,v4"
        assert tank.summary == "a test tankoubon"

        tank_full = tankoubonApi.get_tankoubon_full(tid).result
        assert tank_full.full_data == []  # since the tank contains no archives
        # other than this field, the tanks return by the 2 get apis are the same
        tank_full.full_data = None
        assert tank_full == tank

    def test_with_archive(self, api: LANraragiAPI, shared_state: SharedState):
        tankoubonApi = api.tankoubons
        archiveApi = api.archives

        tid = shared_state.get_tankoubon_id()
        aid = shared_state.get_archive_id()

        archive = archiveApi.get_archive(aid)
        assert archive is not None
        tank = tankoubonApi.get_tankoubon(tid)
        assert tank.archives == []

        # run twice for idempotency check
        for _ in range(2):
            resp = tankoubonApi.add_archive_to_tankoubon(tid, aid)
            assert resp.success == 1

            tank_full = tankoubonApi.get_tankoubon_full(tid).result
            assert tank_full.full_data == [archive]
            assert tank_full.archives == [aid]

            tank = tankoubonApi.get_tankoubon(tid)
            assert tank.archives == [aid]

            tids = archiveApi.get_archive_tankoubons(aid)
            assert tids == [tid]

        # test remove
        resp = tankoubonApi.remove_archive_from_tankoubon(tid, aid)
        assert resp.success == 1
        assert resp.operation == "remove_from_tankoubon"

        tank_full = tankoubonApi.get_tankoubon_full(tid).result
        assert tank_full.full_data == []
        assert tank_full.archives == []

        tank = tankoubonApi.get_tankoubon(tid)
        assert tank.archives == []

        tids = archiveApi.get_archive_tankoubons(aid)
        assert tids == []

        # remove operation is not idempotent
        resp = tankoubonApi.remove_archive_from_tankoubon(tid, aid)
        assert resp.success == 0
        assert resp.operation == "remove_from_tankoubon"
        assert resp.error == f"{aid} not in tankoubon {tid}, doing nothing."

    def test_tankoubon_thumbnail(self, api: LANraragiAPI, shared_state: SharedState):
        tankoubonApi = api.tankoubons
        archiveApi = api.archives

        tid = shared_state.get_tankoubon_id()
        aid = shared_state.get_archive_id()

        archive = archiveApi.get_archive(aid)
        assert archive is not None
        assert archive.pagecount > 5

        resp = tankoubonApi.add_archive_to_tankoubon(tid, aid)
        assert resp.success == 1

        for p in [1, 2, 3]:
            resp = tankoubonApi.update_tankoubon_thumbnail(tid, p)
            assert resp.success == 1
            assert resp.operation == "update_tankoubon_thumbnail"

            def archive_task(p: int = p):
                return archiveApi.get_archive_thumbnail(aid, page=p, no_fallback=True)

            def tank_task():
                return tankoubonApi.get_tankoubon_thumbnail(tid, no_fallback=True)

            archive_thumbnail = get_thumbnail(api, archive_task)
            tank_thumb = get_thumbnail(api, tank_task)
            assert archive_thumbnail == tank_thumb

        resp = tankoubonApi.remove_archive_from_tankoubon(tid, aid)
        assert resp.success == 1
        assert resp.operation == "remove_from_tankoubon"


class TestOPDS:
    def test_get_opds_catalog(self, api: LANraragiAPI, shared_state: SharedState):
        opdsApi = api.opds
        archiveApi = api.archives
        categoryApi = api.categories

        aid = shared_state.get_archive_id()
        archive = archiveApi.get_archive(aid)
        assert archive is not None

        cid = shared_state.get_category_id()
        cat = categoryApi.get_category(cid)
        assert cat is not None

        for aid2, cid2 in [(None, None), (aid, None), (None, cid), (aid, cid)]:
            resp = opdsApi.get_opds_catalog(archive_id=aid2, category_id=cid2)
            assert len(resp) > 0

    def test_get_archive_opds(self, api: LANraragiAPI, shared_state: SharedState):
        opdsApi = api.opds
        archiveApi = api.archives

        aid = shared_state.get_archive_id()
        archive = archiveApi.get_archive(aid)
        assert archive is not None

        data = opdsApi.get_opds_item(aid)
        assert len(data) > 0
        assert archive.title in data

    def test_get_opds_page(self, api: LANraragiAPI, shared_state: SharedState):
        opdsApi = api.opds
        archiveApi = api.archives

        aid = shared_state.get_archive_id()
        archive = archiveApi.get_archive(aid)
        assert archive is not None

        for p in [1, 2, None]:
            data = opdsApi.get_opds_page(aid, page=p).content
            assert len(data) > 0


class TestStamps:
    def test_crud_stamps(self, api: LANraragiAPI, shared_state: SharedState):
        stampApi = api.stamps
        archiveApi = api.archives
        aid = shared_state.get_archive_id()

        archive = archiveApi.get_archive(aid)
        assert archive is not None
        assert archive.pagecount > 5

        # get all pages containing stamps
        pages = stampApi.get_stamped_pages(aid).result
        assert pages == []

        page2stamp_maps: dict[int, list[StampsData]] = {
            1: [
                StampsData(position="5,10", content="p1s1"),
                StampsData(position="12,16", content="p1s2"),
            ],
            2: [StampsData(position="31,17", content="p2s1")],
            4: [
                StampsData(position="15,10", content="p3s1"),
                StampsData(position="7,16", content="p3s2"),
                StampsData(position="51,10", content="p3s3"),
            ],
        }

        # add stamps
        for p, ss in page2stamp_maps.items():
            for s in ss:
                resp = stampApi.add_stamp(aid, p, s.content, s.position)
                assert resp.success == 1
                assert resp.operation == "add_stamp"
                assert resp.stamp_id is not None
                s.id = resp.stamp_id

                # s2 = stampApi.get_stamp(s.id)
                # assert s == s2

        pages = stampApi.get_stamped_pages(aid).result
        pages = [int(p) for p in pages]
        assert sorted(pages) == sorted(page2stamp_maps.keys())

        # get stamps by page
        sort_by_id_key: Callable[[StampsData], str | None] = lambda s: cast(str, s.id)
        for p in pages:
            ss1 = stampApi.get_stamps_by_page(aid, p)
            ss2 = page2stamp_maps[p]
            assert sorted(ss1, key=sort_by_id_key) == sorted(ss2, key=sort_by_id_key)

        stamp = page2stamp_maps[1][0]
        sid = stamp.id
        assert sid is not None

        # get a stamp by its id will lead to 500
        # it seems the web ui does not use this api
        with pytest.raises(APIHttpError) as e:
            _ = stampApi.get_stamp(sid)

        assert e.type is APIHttpError
        assert e.value.status_code == 500

        # update a stamp
        resp = stampApi.update_stamp(
            sid, position="1,1", content="updated stamp content"
        )
        assert resp.success == 1
        # stamp = stampApi.get_stamp(sid)
        # assert stamp.content == "updated stamp content"
        # assert stamp.position == "1,1"

        # delete stamps
        for p, ss in page2stamp_maps.items():
            for s in ss:
                assert s.id is not None
                resp = stampApi.delete_stamp(s.id)
            ss2 = stampApi.get_stamps_by_page(aid, p)
            assert ss2 == []

        pages = stampApi.get_stamped_pages(aid).result
        assert pages == []


class TestPlugins:
    def test_use_plugin(self, api: LANraragiAPI):
        pluginApi = api.plugins

        plugin = "fldr2cat"

        resp = pluginApi.use_plugin(plugin=plugin)
        assert resp.success == 1
        assert resp.operation == "use_plugin"
        assert resp.type == "script"

    def test_use_plugin_async(self, api: LANraragiAPI):
        pluginApi = api.plugins
        minionApi = api.minion

        plugin = "fldr2cat"

        resp = pluginApi.use_plugin_async(plugin=plugin)
        assert resp.success == 1
        assert resp.operation == "queue_plugin_exec"

        job = resp.job
        assert job is not None

        wait_minion_job_util(minionApi, job, "finished")


class TestShinobu:
    pass


class TestMinion:
    def test_queue_job(self):
        pass


class TestMisc:
    def test_queue_url_to_download(self):
        pass


class TestDatabase:
    def test_clear_all_new(self, api: LANraragiAPI):
        dbApi = api.database

        resp = dbApi.clear_all_new_flags()
        assert resp.success == 1
        assert resp.operation == "clear_new_all"

    def test_clean_db(self, api: LANraragiAPI):
        dbApi = api.database

        resp = dbApi.clean_database()
        assert resp.success == 1
        assert resp.operation == "clean_database"

    def test_drop_db(self, api: LANraragiAPI):
        dbApi = api.database

        resp = dbApi.drop_database()
        assert resp.success == 1
        assert resp.operation == "drop_database"

    def test_restore(self, api: LANraragiAPI, tmp_path: Path):
        dbApi = api.database
        _minionApi = api.minion

        d = tmp_path / "bkp_folder"
        d.mkdir()
        bf = d / "bkp.json"
        _ = bf.write_text(DatabaseBackup().model_dump_json())

        # don't know why the body is
        # {'error': 'This API is protected and requires login or an API Key.'}
        # all other apis can be authed
        with pytest.raises(APIResponseDecodeError) as e:
            _resp = dbApi.queue_restore(str(bf))

        assert e.type is APIResponseDecodeError

        # assert resp.success == 1
        # assert resp.operation == "queue_restore"

        # job = resp.job
        # assert job is not None

        # wait_minion_job_util(minionApi, job, "finished")

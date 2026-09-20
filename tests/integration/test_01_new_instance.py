import pytest

from lanraragi_api import LANraragiAPI
from lanraragi_api.base import APIHttpError, APIResponseDecodeError, DatabaseBackup
from tests.integration.util.minion_util import wait_minion_job_util

pytestmark = pytest.mark.order(1)


class TestSearch:
    def test_search_archives(self, api: LANraragiAPI):
        searchApi = api.search
        # empty db will always lead to 204
        with pytest.raises(APIResponseDecodeError):
            _ = searchApi.search_archives()

    def test_search_archive_ids(self, api: LANraragiAPI):
        searchApi = api.search
        # empty db will always lead to 204
        with pytest.raises(APIResponseDecodeError):
            _ = searchApi.search_archive_ids()

    def test_search_random_archive(self, api: LANraragiAPI):
        searchApi = api.search
        archives = searchApi.get_random_archives()
        assert len(archives) == 0

    def test_discard_cache(self, api: LANraragiAPI):
        searchApi = api.search
        resp = searchApi.discard_search_cache()
        assert resp.success == 1


class TestArchives:
    def test_get_all_archives(self, api: LANraragiAPI):
        archiveApi = api.archives

        archives = archiveApi.get_all_archives()
        assert len(archives) == 0

    def test_get_all_untagged_archives(self, api: LANraragiAPI):
        archiveApi = api.archives

        archives = archiveApi.get_untagged_archives()
        assert len(archives) == 0


class TestCategories:
    def test_basic_crud_categories(self, api: LANraragiAPI):
        categoryApi = api.categories

        cats = categoryApi.get_all_categories()
        assert len(cats) == 1

        cid = cats[0].id

        cat = categoryApi.get_category(cid)
        assert cat is not None
        assert cat == cats[0]
        assert cat.name == "🔖 Favorites"
        assert cat.archives == []
        assert cat.pinned == 0
        assert cat.search == ""

        resp = categoryApi.update_category(
            cid,
            name="My Favorites",
        )
        assert resp.success == 1

        cat = categoryApi.get_category(cid)
        assert cat is not None
        assert cat.name == "My Favorites"
        assert cat.archives == []
        assert cat.pinned == 0
        assert cat.search == ""

        resp = categoryApi.delete_category(cid)
        assert resp.success == 1

        cats = categoryApi.get_all_categories()
        assert len(cats) == 0


class TestTankoubons:
    pass


class TestPlugins:
    def test_list_plugins(self, api: LANraragiAPI):
        pluginApi = api.plugins

        plugins = pluginApi.get_available_plugins("download")
        assert len(plugins) == 3

        plugins = pluginApi.get_available_plugins("login")
        assert len(plugins) == 4

        plugins = pluginApi.get_available_plugins("metadata")
        assert len(plugins) == 21

        plugins = pluginApi.get_available_plugins("script")
        assert len(plugins) == 3

        plugins = pluginApi.get_available_plugins("all")
        assert len(plugins) == 31

        with pytest.raises(APIHttpError) as e:
            _ = pluginApi.get_available_plugins("invalid_type")
        assert e.type is APIHttpError
        assert e.value.status_code == 400


class TestShinobu:
    def test_shinobu(self, api: LANraragiAPI):
        shinobuApi = api.shinobu

        def assert_shinobu_status(is_alive: int):
            status = shinobuApi.get_shinobu_status()
            assert status["success"] == 1
            assert status["is_alive"] == is_alive
            assert status["operation"] == "shinobu_status"

        assert_shinobu_status(1)

        resp = shinobuApi.stop_shinobu()
        assert resp.success == 1
        assert resp.operation == "shinobu_stop"

        resp = shinobuApi.restart_shinobu()
        assert resp.success == 1
        assert resp.operation == "shinobu_restart"

        assert_shinobu_status(1)

        resp = shinobuApi.rescan_shinobu()
        assert resp.success == 1
        assert resp.operation == "shinobu_rescan"

        assert_shinobu_status(1)


class TestMinion:
    pass


class TestOPDS:
    pass


class TestStamps:
    pass


class TestDatabase:
    def test_get_stat(self, api: LANraragiAPI):
        dbApi = api.database

        stat = dbApi.get_tag_statistics()
        assert len(stat) == 0

    def test_get_backup(self, api: LANraragiAPI):
        dbApi = api.database

        bkp = dbApi.get_backup()
        assert bkp == DatabaseBackup()

    def test_get_backup_async(self, api: LANraragiAPI):
        dbApi = api.database

        resp = dbApi.queue_backup()
        assert resp.success == 1
        assert resp.operation == "queue_backup"

        job_id = resp.job
        assert job_id is not None

        # TODO: make the state enum
        wait_minion_job_util(api.minion, job_id, "finished")

        bkp = dbApi.download_backup(job_id, "json").json()
        # this bkp json does not have `tankoubons` fields as the one from sync backup endpoint
        assert bkp == {"archives": [], "categories": []}


class TestMisc:
    def test_get_server_info(self, api: LANraragiAPI):
        miscApi = api.misc

        si = miscApi.get_server_information()
        assert si.version == "0.9.81"
        assert si.nofun_mode

    def test_clean_temp_folder(self, api: LANraragiAPI):
        miscApi = api.misc

        resp = miscApi.clean_temporary_folder()
        assert resp.success == 1
        assert resp.operation == "cleantemp"

    def test_regen_thumbs(self, api: LANraragiAPI):
        miscApi = api.misc
        minionApi = api.minion

        resp = miscApi.regenerate_thumbnails()
        assert resp.success == 1
        assert resp.operation == "regen_thumbnails"
        job1 = resp.job
        assert job1 is not None
        _ = minionApi.get_basic_status(job1)
        _ = minionApi.get_full_status(job1)

        resp = miscApi.regenerate_thumbnails(force=True)
        assert resp.success == 1
        assert resp.operation == "regen_thumbnails"
        job2 = resp.job
        assert job2 is not None
        assert job1 != job2
        _ = minionApi.get_basic_status(job2)
        _ = minionApi.get_full_status(job2)

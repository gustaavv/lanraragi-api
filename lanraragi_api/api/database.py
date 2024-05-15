from ..common.base import BaseAPICall


class DatabaseAPI(BaseAPICall):
    """
    Query and modify the database.
    """
    def get_statistics(self):
        pass

    def clean_database(self):
        pass

    def drop_database(self):
        raise NotImplementedError

    def get_backup(self):
        pass

    def clear_all_new_flags(self):
        pass

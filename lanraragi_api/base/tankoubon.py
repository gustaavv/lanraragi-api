from typing import Optional

import requests
from pydantic import BaseModel
from script_house.utils import JsonUtils

from lanraragi_api.base.archive import Archive
from lanraragi_api.base.base import BaseAPICall


class Tankoubon(BaseModel):
    archives: list[str]
    full_data: Optional[list[Archive]] = None
    id: str
    name: str
    summary: str
    tags: str


class TankoubonAPI(BaseAPICall):
    """
    Tankoubon API.
    """

    def get_all_tankoubons(self, page: str = None) -> list[Tankoubon]:
        """
        Get list of Tankoubons paginated.
        :param page: Page of the list of Tankoubons.
        :return: list of Tankoubons
        """
        resp = requests.get(f"{self.server}/api/tankoubons", params=self.build_params({'page': page}),
                            headers=self.build_headers())
        list = JsonUtils.to_obj(resp.text)['result']
        return [JsonUtils.to_obj(JsonUtils.to_str(o), Tankoubon) for o in list]

    def get_tankoubon(self, id: str, include_full_data: str = None, page: str = None) -> dict:
        """
        Get the details of the specified tankoubon ID, with the archives list
        paginated.
        :param id: ID of the Tankoubon desired.
        :param include_full_data: If set in 1, it appends a full_data array
        with Archive objects.
        :param page: Page of the Archives list.
        :return: Tankoubon
        """
        resp = requests.get(f"{self.server}/api/tankoubons/{id}",
                            params=self.build_params({
                                'page': page,
                                'include_full_data': include_full_data if include_full_data else None}),
                            headers=self.build_headers())
        return JsonUtils.to_obj(JsonUtils.to_str(JsonUtils.to_obj(resp.text)['result']), Tankoubon)

    def create_tankoubon(self, name: str):
        """
        Create a new Tankoubon or updated the name of an existing one.
        :param name: Name of the Tankoubon.
        :return: operation result
        """
        resp = requests.put(f"{self.server}/api/tankoubons", params=self.build_params({'name': name}),
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def update_tankoubon(self, id: str):
        raise NotImplementedError()

    def add_archive_to_tankoubon(self, tankoubon_id: str, archive_id: str):
        """
        Append an archive at the final position of a Tankoubon.
        :param tankoubon_id: ID of the Tankoubon to update.
        :param archive_id: ID of the Archive to append.
        :return: operation result
        """
        resp = requests.put(f"{self.server}/api/tankoubons/{tankoubon_id}/{archive_id}", params=self.build_params(),
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def remove_archive_from_tankoubon(self, tankoubon_id: str, archive_id: str):
        """
        Remove an archive from a Tankoubon.
        :param tankoubon_id: ID of the Tankoubon to update.
        :param archive_id: ID of the archive to remove.
        :return: operation result
        """
        resp = requests.delete(f"{self.server}/api/tankoubons/{tankoubon_id}/{archive_id}", params=self.build_params(),
                               headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def delete_tankoubon(self, id: str) -> dict:
        """
        Remove a Tankoubon.
        :param id: ID of the Tankoubon to delete.
        :return: operation result
        """
        resp = requests.delete(f"{self.server}/api/tankoubons/{id}", params=self.build_params(),
                               headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

import requests
from script_house.utils import JsonUtils

from lanraragi_api.Config import assert_use_untested_functions
from lanraragi_api.base.base import BaseAPICall


class ShinobuAPI(BaseAPICall):
    """
    Control the built-in Background Worker.
    """

    def get_shinobu_status(self) -> dict:
        """
        Get the current status of the Worker.
        :return: json
        """
        resp = requests.get(f"{self.server}/api/shinobu", params={'key': self.key},
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def stop_shinobu(self) -> dict:
        """
        Stop the Worker.
        :return: operation result
        """
        # TODO: untested
        assert_use_untested_functions()
        resp = requests.post(f"{self.server}/api/shinobu/stop", params={'key': self.key},
                             headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def restart_shinobu(self) -> dict:
        """
        (Re)-start the Worker.
        :return: operation result
        """
        resp = requests.post(f"{self.server}/api/shinobu/restart", params={'key': self.key},
                             headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

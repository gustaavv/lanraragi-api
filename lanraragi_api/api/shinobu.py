from ..common.base import BaseAPICall
from script_house.utils import JsonUtils
import requests


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

    def stop_shinobu(self) -> bool:
        """
        Stop the Worker.
        :return: stopped or not
        """
        # TODO: untested
        resp = requests.post(f"{self.server}/api/shinobu/stop", params={'key': self.key},
                             headers=self.build_headers())
        return resp.status_code == 200

    def restart_shinobu(self) -> int:
        """
        (Re)-start the Worker.
        :return: pid of the new worker
        """
        resp = requests.post(f"{self.server}/api/shinobu/restart", params={'key': self.key},
                             headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)['new_pid']

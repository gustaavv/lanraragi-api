from lanraragi_api.base.base import BaseAPICall, OperationResponse


class ShinobuAPI(BaseAPICall):
    """
    Control the built-in Background Worker.
    """

    def get_shinobu_status(self) -> dict:
        """
        Get the current status of the Worker.
        :return: operation result
        """
        return self.request_json("GET", "/api/shinobu")

    def stop_shinobu(self) -> OperationResponse:
        """
        Stop the Worker.
        :return: operation result
        """
        return self.request_operation("POST", "/api/shinobu/stop")

    def restart_shinobu(self) -> OperationResponse:
        """
        (Re)-start the Worker.
        :return: operation result
        """
        return self.request_operation("POST", "/api/shinobu/restart")

    def rescan_shinobu(self) -> OperationResponse:
        """
        Rescan filemap and restart the Worker.
        :return: operation result
        """
        return self.request_operation("POST", "/api/shinobu/rescan")

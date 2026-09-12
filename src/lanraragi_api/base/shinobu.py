from lanraragi_api.base.base import BaseAPICall, OperationResponse


class ShinobuAPI(BaseAPICall):
    """Shinobu Filewatcher APIs.

    Shared request and error behavior is documented on ``BaseAPICall``.
    """

    def get_shinobu_status(self) -> dict:
        """Get the current status of the filewatcher.

        Returns:
            dict: Decoded status payload, holding the ``is_alive`` flag and the
                ``pid`` of the watcher process.

        Raises:
            APIHttpError: Any status code other than 200.
            APIResponseDecodeError: If the body is not valid JSON.
        """
        return self.request_json("GET", "/api/shinobu")

    def stop_shinobu(self) -> OperationResponse:
        """Stop the filewatcher.

        Use ``/api/shinobu/restart`` to start it again.

        Returns:
            OperationResponse: Result of the operation.

        Raises:
            APIResponseDecodeError: If the body is not valid JSON, or does not
                match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.
        """
        return self.request_operation("POST", "/api/shinobu/stop")

    def restart_shinobu(self) -> OperationResponse:
        """Restart the Shinobu filewatcher.

        This also starts the filewatcher again when it was stopped.

        Returns:
            OperationResponse: Result of the operation, with the new process
                PID as an extra field.

        Raises:
            APIResponseDecodeError: If the body is not valid JSON, or does not
                match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.
        """
        return self.request_operation("POST", "/api/shinobu/restart")

    def rescan_shinobu(self) -> OperationResponse:
        """Rescan the filemap and restart Shinobu.

        This deletes the internal map of scanned files on your system (the
        "filemap") and restarts Shinobu, effectively prompting a full rescan
        of your FS.

        Returns:
            OperationResponse: Result of the operation, with the new process
                PID as an extra field.

        Raises:
            APIResponseDecodeError: If the body is not valid JSON, or does not
                match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.
        """
        return self.request_operation("POST", "/api/shinobu/rescan")

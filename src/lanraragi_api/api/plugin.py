from lanraragi_api.api.base import (
    BaseAPICall,
)
from lanraragi_api.entity.minion import MinionJobResponse
from lanraragi_api.entity.plugin import PluginInfo, PluginUseResponse


class PluginAPI(BaseAPICall):
    """APIs to list and execute Plugins.

    Shared request and error behavior is documented on ``BaseAPICall``.
    """

    def get_available_plugins(self, type: str) -> list[PluginInfo]:
        """List all plugins of the given type.

        Args:
            type: Type of plugins you want to list, one of ``download``,
                ``login``, ``metadata`` or ``script``. Use ``all`` to get
                every type at once.

        Returns:
            list[PluginInfo]: One entry per plugin of the given type.

        Raises:
            APIHttpError: Any status code other than 200.
            APIResponseDecodeError: If the body is not a list of objects
                matching ``PluginInfo``.
        """
        return self.request_model_list("GET", f"/api/plugins/{type}", PluginInfo)

    def use_plugin(
        self, plugin: str, id: str | None = None, arg: str | None = None
    ) -> PluginUseResponse:
        """Use a Plugin and return the result.

        If using a metadata plugin, the matching archive will not be modified
        in the database. See more info on Plugins in the matching section of
        the Docs.

        Args:
            plugin: Namespace of the plugin to use.
            id: ID of the archive to use the plugin on. Only mandatory for
                metadata plugins. Defaults to None.
            arg: One-shot argument to use when executing this plugin. Defaults
                to None.

        Returns:
            PluginUseResponse: Result of the plugin run, with the type of the
                plugin and any data it returned.

        Raises:
            APIResponseDecodeError: If the body is not valid JSON, or does not
                match ``PluginUseResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            A failed plugin run is reported inside the body, through ``success``
            set to 0, and does not raise unless raising is enabled.
        """
        return self.request_operation(
            "POST",
            "/api/plugins/use",
            model=PluginUseResponse,
            params={"plugin": plugin, "id": id, "arg": arg},
        )

    def use_plugin_async(
        self,
        plugin: str,
        id: str | None = None,
        arg: str | None = None,
        priority: int = 0,
    ) -> MinionJobResponse:
        """Use a Plugin and return the Minion job ID matching the run.

        This endpoint is useful if you want to run longer-lived plugins which
        might timeout if ran with the standard endpoint.

        Args:
            plugin: Namespace of the plugin to use.
            id: ID of the archive to use the plugin on. Only mandatory for
                metadata plugins. Defaults to None.
            arg: One-shot argument to use when executing this plugin. Defaults
                to None.
            priority: Priority of the Minion job. The higher the number, the
                more important the job is. Defaults to 0.

        Returns:
            MinionJobResponse: Result of the call, with the ID of the queued
                job.

        Raises:
            APIResponseDecodeError: If the body is not valid JSON, or does not
                match ``MinionJobResponse``.
            APIOperationError: If the operation failed and raising is enabled.
        """
        return self.request_operation(
            "POST",
            "/api/plugins/queue",
            model=MinionJobResponse,
            params={"plugin": plugin, "id": id, "arg": arg, "priority": priority},
        )

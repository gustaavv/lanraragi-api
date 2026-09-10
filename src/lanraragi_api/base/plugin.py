from typing import Any

from pydantic import Field

from lanraragi_api.base.base import (
    BaseAPICall,
    DictLikeModel,
    MinionJobResponse,
    OperationResponse,
)


class PluginParameter(DictLikeModel):
    name: str | None = Field(default=None)
    desc: str | None = Field(default=None)
    type: str | None = Field(default=None)
    default_value: str | None = Field(default=None)


class PluginInfo(DictLikeModel):
    author: str | None = Field(default=None)
    description: str | None = Field(default=None)
    name: str | None = Field(default=None)
    icon: str | None = Field(default=None)
    type: str | None = Field(default=None)
    namespace: str | None = Field(default=None)
    parameters: list[PluginParameter] = Field(default_factory=list)
    version: str | None = Field(default=None)
    oneshot_arg: str | None = Field(default=None)
    url_regex: str | None = Field(default=None)
    login_from: str | None = Field(default=None)


class PluginUseResponse(OperationResponse):
    type: str | None = Field(default=None)
    data: dict[str, Any] | None = Field(default=None)


class PluginAPI(BaseAPICall):
    """
    APIs to list and execute Plugins.
    """

    def get_available_plugins(self, type: str) -> list[PluginInfo]:
        """
        Get a list of the available plugins on the server, filtered by type.
        :param type: Type of plugins you want to list.
                You can either use 'login', 'metadata', 'script',
                 or 'all' to get all previous types at once.
        :return: list of plugins
        """
        return self.request_model_list("GET", f"/api/plugins/{type}", PluginInfo)

    def use_plugin(
        self, plugin: str, id: str | None = None, arg: str | None = None
    ) -> PluginUseResponse:
        """
        Uses a Plugin and returns the result.

        If using a metadata plugin, the matching archive will not be modified
        in the database.

        See more info on Plugins in the matching section of the Docs.
        :param plugin: Namespace of the plugin to use.
        :param id: ID of the archive to use the Plugin on. This is only
        mandatory for metadata plugins.
        :param arg: Optional One-Shot argument to use when executing this
        Plugin.
        :return: operation result
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
        """
        Uses a Plugin and returns a Minion Job ID matching the Plugin run.

        This endpoint is useful if you want to run longer-lived plugins which
        might timeout if ran with the standard endpoint.

        :param plugin: Namespace of the plugin to use.
        :param id: ID of the archive to use the Plugin on. This is only
        mandatory for metadata plugins.
        :param arg: Optional One-Shot argument to use when executing this
        Plugin.
        :param priority: Minion job priority. Higher values are processed first.
        Defaults to 0.
        :return: operation result
        """
        return self.request_operation(
            "POST",
            "/api/plugins/queue",
            model=MinionJobResponse,
            params={"plugin": plugin, "id": id, "arg": arg, "priority": priority},
        )

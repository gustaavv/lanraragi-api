from typing import Any

from pydantic import Field

from lanraragi_api.entity.base import DictLikeModel, OperationResponse


class PluginParameter(DictLikeModel):
    """Parameter for a LRR Plugin.

    Attributes:
        name: Name of the parameter.
        desc: Description of the parameter.
        type: Type of the parameter, one of ``bool``, ``int`` or ``string``.
            Not checked server-side; used to inform the plugin config page.
        default_value: Default value of the parameter.
    """

    name: str | None = Field(default=None)
    desc: str | None = Field(default=None)
    type: str | None = Field(default=None)
    default_value: str | None = Field(default=None)


class PluginInfo(DictLikeModel):
    """Metadata payload for a LRR Plugin.

    Attributes:
        author: Author of the plugin.
        description: Description of the plugin.
        name: Name of the plugin.
        icon: Base64 image of the plugin icon.
        type: Type of the plugin, one of ``download``, ``login``,
            ``metadata`` or ``script``.
        namespace: Unique namespace for the plugin.
        parameters: Parameters the plugin accepts.
        version: Version of the plugin.
        oneshot_arg: Description of the manual one-shot argument users can
            fill in for manual plugin calls.
        url_regex: For downloader plugins, regex where it should be used.
        login_from: Namespace of the login plugin this plugin depends on.
    """

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
    """Result of a Plugin run.

    Attributes:
        type: Type of the plugin that ran, one of ``download``, ``login``,
            ``metadata`` or ``script``. Omitted when the plugin is not found.
        data: Arbitrary data returned by the plugin.
    """

    type: str | None = Field(default=None)
    data: dict[str, Any] | None = Field(default=None)

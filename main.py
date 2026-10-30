import asyncio
from packaging.version import parse as parse_version
from astrbot.api import star
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.core.utils.version_comparator import VersionComparator


@star.register("advanced_plugin_manager", "user", "智能插件管理系统", "1.0.0")
class AdvancedPluginManager(star.Star):
    def __init__(self, context: star.Context) -> None:
        super().__init__(context)
        self.context = context
        self.star_manager = context._star_manager
        # 默认使用官方推荐的 GitHub 镜像加速源，保持与 Web 前端一致
        self.github_proxy = "https://edgeone.gh-proxy.com"
        self.interval_seconds = 86400  # 定时轮询插件地址检测升级周期: 24小时
        self._update_task = asyncio.create_task(self._scheduled_update_loop())

    async def _get_outdated_plugins(self) -> list[tuple[star.StarMetadata, str]]:
        outdated = []
        for plugin in self.context.get_all_stars():
            if plugin.reserved or not plugin.repo:
                continue
            # 不通过市场索引，透传 github_proxy 直接轮询插件地址的元数据版本号
            remote_info = await self.star_manager.inspect_plugin_repository(
                plugin.repo, proxy=self.github_proxy
            )
            remote_ver = str(remote_info["version"]).strip()
            local_ver = str(plugin.version).strip()
            # 只要插件地址的元数据版本号增加，即判定为有更新
            if VersionComparator.compare_version(local_ver, remote_ver) < 0:
                outdated.append((plugin, remote_ver))
        return outdated

    @filter.llm_tool(name="set_github_proxy")
    async def set_github_proxy(self, event: AstrMessageEvent, proxy_url: str) -> str:
        """设置或切换 GitHub 镜像加速源。

        Args:
            proxy_url(string): 镜像加速地址，如 'https://edgeone.gh-proxy.com'、'https://gh-proxy.com'，传入 'none' 或空则直连
        """
        self.github_proxy = "" if proxy_url.lower() in ("none", "off", "direct") else proxy_url.rstrip("/")
        mode = self.github_proxy if self.github_proxy else "直连/无镜像"
        return f"GitHub 镜像源已设置为: {mode}"

    @filter.llm_tool(name="update_plugin")
    async def update_plugin(self, event: AstrMessageEvent, plugin_name: str) -> str:
        """更新指定的插件。

        Args:
            plugin_name(string): 要更新的插件名称
        """
        await self.star_manager.update_plugin(plugin_name, proxy=self.github_proxy)
        await self.star_manager.reload(plugin_name)
        return f"插件 {plugin_name} 已成功更新并重载。"

    @filter.llm_tool(name="reload_plugin")
    async def reload_plugin(self, event: AstrMessageEvent, plugin_name: str) -> str:
        """重新加载指定的插件或全部插件。

        Args:
            plugin_name(string): 插件名称，若为 'all' 则重载所有插件
        """
        if plugin_name.lower() == "all":
            await self.star_manager.reload()
            return "所有插件已成功重新加载。"
        await self.star_manager.reload(plugin_name)
        return f"插件 {plugin_name} 已成功重新加载。"

    @filter.llm_tool(name="reinstall_plugin")
    async def reinstall_plugin(self, event: AstrMessageEvent, plugin_name: str) -> str:
        """重新安装指定的插件（无需卸载，调用原生 install_plugin 直接覆盖安装）。

        Args:
            plugin_name(string): 要重新安装的插件名称
        """
        plugin = self.context.get_registered_star(plugin_name)
        await self.star_manager.install_plugin(plugin.repo, proxy=self.github_proxy)
        return f"插件 {plugin_name} 已成功重新安装。"

    @filter.llm_tool(name="check_plugin_updates")
    async def check_plugin_updates(self, event: AstrMessageEvent) -> str:
        """不通过市场索引，调用原生接口直接轮询各插件地址的 metadata 版本号检查更新。"""
        outdated = await self._get_outdated_plugins()
        if not outdated:
            return "所有插件均已是最新版本，无需更新。"
        details = [f"- {p.name}: 当前 {p.version} -> 仓库最新 {remote_v}" for p, remote_v in outdated]
        return "检测到以下插件存在新版本：\n" + "\n".join(details)

    @filter.llm_tool(name="update_all_plugins")
    async def update_all_plugins(self, event: AstrMessageEvent = None) -> str:
        """升级所有检测到仓库元数据版本号增加的插件并自动重载。"""
        outdated = await self._get_outdated_plugins()
        if not outdated:
            return "当前没有检测到需要升级的插件。"
        updated_names = []
        for plugin, _ in outdated:
            await self.star_manager.update_plugin(plugin.name, proxy=self.github_proxy)
            await self.star_manager.reload(plugin.name)
            updated_names.append(plugin.name)
        return f"已完成所有插件升级并重载：{', '.join(updated_names)}"

    async def _scheduled_update_loop(self) -> None:
        while True:
            await asyncio.sleep(self.interval_seconds)
            await self.update_all_plugins()

    async def terminate(self) -> None:
        self._update_task.cancel()

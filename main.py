import time
import asyncio
import aiohttp
from astrbot.api import star
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.core.utils.version_comparator import VersionComparator

OFFICIAL_PROXIES = [
    "https://edgeone.gh-proxy.com",
    "https://hk.gh-proxy.com",
    "https://gh-proxy.com",
    "https://gh.dpik.top",
]
TEST_TARGET = "https://github.com/AstrBotDevs/AstrBot/raw/refs/heads/master/.python-version"


@star.register("advanced_plugin_manager", "user", "智能插件管理系统", "1.0.0")
class AdvancedPluginManager(star.Star):
    def __init__(self, context: star.Context) -> None:
        super().__init__(context)
        self.context = context
        self.star_manager = context._star_manager
        self.interval_seconds = 86400
        self._update_task = asyncio.create_task(self._scheduled_update_loop())

    async def _test_latency(self, session: aiohttp.ClientSession, proxy: str) -> tuple[str, float]:
        start = time.time()
        async with session.get(f"{proxy.rstrip('/')}/{TEST_TARGET}", timeout=aiohttp.ClientTimeout(total=5)) as resp:
            assert resp.status == 200
            return proxy, (time.time() - start) * 1000

    async def _get_fastest_proxy(self) -> str:
        async with aiohttp.ClientSession() as session:
            tasks = [self._test_latency(session, p) for p in OFFICIAL_PROXIES]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            valid = [r for r in results if isinstance(r, tuple)]
            return min(valid, key=lambda x: x[1])[0]

    async def _get_outdated_plugins(self, proxy: str) -> list[tuple[star.StarMetadata, str]]:
        outdated = []
        for plugin in self.context.get_all_stars():
            if plugin.reserved or not plugin.repo:
                continue
            remote_info = await self.star_manager.inspect_plugin_repository(plugin.repo, proxy=proxy)
            remote_ver = str(remote_info["version"]).strip()
            local_ver = str(plugin.version).strip()
            if VersionComparator.compare_version(local_ver, remote_ver) < 0:
                outdated.append((plugin, remote_ver))
        return outdated

    @filter.llm_tool(name="test_fastest_proxy")
    async def test_fastest_proxy(self, event: AstrMessageEvent) -> str:
        """测试所有官方 GitHub 镜像站延迟并返回当前最优镜像。"""
        fastest = await self._get_fastest_proxy()
        return f"当前测速最优 GitHub 镜像为: {fastest}"

    @filter.llm_tool(name="update_plugin")
    async def update_plugin(self, event: AstrMessageEvent, plugin_name: str) -> str:
        """更新指定的插件，自动选择延迟最低的镜像站加速。

        Args:
            plugin_name(string): 要更新的插件名称
        """
        proxy = await self._get_fastest_proxy()
        await self.star_manager.update_plugin(plugin_name, proxy=proxy)
        await self.star_manager.reload(plugin_name)
        return f"插件 {plugin_name} 已使用最优镜像 {proxy} 成功更新并重载。"

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
        """重新安装指定的插件，自动选择延迟最低的镜像站覆盖安装。

        Args:
            plugin_name(string): 要重新安装的插件名称
        """
        proxy = await self._get_fastest_proxy()
        plugin = self.context.get_registered_star(plugin_name)
        await self.star_manager.install_plugin(plugin.repo, proxy=proxy)
        return f"插件 {plugin_name} 已使用最优镜像 {proxy} 成功重新安装。"

    @filter.llm_tool(name="check_plugin_updates")
    async def check_plugin_updates(self, event: AstrMessageEvent) -> str:
        """自动测速并选最优镜像，轮询各插件地址的 metadata 版本号检查更新。"""
        proxy = await self._get_fastest_proxy()
        outdated = await self._get_outdated_plugins(proxy)
        if not outdated:
            return f"所有插件均已是最新版本 (使用镜像: {proxy})。"
        details = [f"- {p.name}: 当前 {p.version} -> 仓库最新 {remote_v}" for p, remote_v in outdated]
        return f"检测到以下插件存在新版本 (使用镜像: {proxy})：\n" + "\n".join(details)

    @filter.llm_tool(name="update_all_plugins")
    async def update_all_plugins(self, event: AstrMessageEvent = None) -> str:
        """选择延迟最低的镜像，升级所有版本增加的插件并重载。"""
        proxy = await self._get_fastest_proxy()
        outdated = await self._get_outdated_plugins(proxy)
        if not outdated:
            return "当前没有检测到需要升级的插件。"
        updated_names = []
        for plugin, _ in outdated:
            await self.star_manager.update_plugin(plugin.name, proxy=proxy)
            await self.star_manager.reload(plugin.name)
            updated_names.append(plugin.name)
        return f"已使用最优镜像 {proxy} 完成插件升级并重载：{', '.join(updated_names)}"

    async def _scheduled_update_loop(self) -> None:
        while True:
            await asyncio.sleep(self.interval_seconds)
            await self.update_all_plugins()

    async def terminate(self) -> None:
        self._update_task.cancel()

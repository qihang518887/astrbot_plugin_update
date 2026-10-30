# 高级插件管理系统 (advanced_plugin_manager)

基于 AstrBot 核心架构深度定制的插件管理系统。

## 核心设计与特性

1. **脱离市场索引，直接轮询插件地址的元数据版本号**
   - 不依赖任何第三方或官方市场索引/索引变更判定。
   - 直接读取插件仓库地址中的 `metadata.yaml`，仅以云端元数据版本号增加（`VersionComparator.compare_version < 0`）作为唯一判定依据。

2. **原生覆盖式重新安装（无需卸载）**
   - 遵照官方重装机制，通过 `install_plugin(repo_url, proxy)` 直接拉取代码并覆盖安装并重新加载依赖，不会删除数据与配置，避免先卸载带来的中间态丢失风险。

3. **完美兼容 GitHub 镜像加速**
   - 默认集成 AstrBot 官方同款 GitHub 镜像加速源（如 `https://edgeone.gh-proxy.com`），同时支持通过自然语言工具随时切换指定镜像或切回直连。
   - 在轮询元数据检测版本、执行更新、重新安装时全程透传镜像参数。

4. **自然语言 LLM Tool 支持**
   - `set_github_proxy(proxy_url)`: 设置或切换 GitHub 镜像加速源。
   - `update_plugin(plugin_name)`: 更新并重载指定插件。
   - `reload_plugin(plugin_name)`: 重新加载指定插件或所有插件（`all`）。
   - `reinstall_plugin(plugin_name)`: 直接重新安装覆盖插件。
   - `check_plugin_updates()`: 轮询插件源地址的 metadata 检查更新。
   - `update_all_plugins()`: 批量升级所有新版本插件。

5. **后台定时轮询自动升级**
   - 挂载后台异步轮询协程，定时直连各插件地址检测元数据版本号，自动执行全量平滑更新与热重载。

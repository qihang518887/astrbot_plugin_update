# 高级插件管理系统 (advanced_plugin_manager)

基于 AstrBot 核心架构深度定制的插件管理系统。

## 核心设计与特性

1. **脱离市场索引，直接轮询插件地址的元数据版本号**
   - 不依赖任何第三方或官方市场索引/索引变更判定。
   - 直接读取插件仓库地址中的 `metadata.yaml`，仅以云端元数据版本号增加（`parse_version(remote) > parse_version(local)`）作为唯一判定依据。

2. **原生覆盖式重新安装（无需卸载）**
   - 遵照官方重装机制，通过 `install_plugin(repo_url)` 直接拉取代码并覆盖安装并重新加载依赖，不会删除数据与配置，避免先卸载带来的中间态丢失风险。

3. **自然语言 LLM Tool 支持**
   - `update_plugin(plugin_name)`: 更新并重载指定插件。
   - `reload_plugin(plugin_name)`: 重新加载指定插件或所有插件（`all`）。
   - `reinstall_plugin(plugin_name)`: 直接重新安装覆盖插件。
   - `check_plugin_updates()`: 轮询插件源地址的 metadata 检查更新。
   - `update_all_plugins()`: 批量升级所有新版本插件。

4. **后台定时轮询自动升级**
   - 挂载后台异步轮询协程，定时直连各插件地址检测元数据版本号，自动执行全量平滑更新与热重载。

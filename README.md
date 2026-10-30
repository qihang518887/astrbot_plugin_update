# 高级插件管理系统 (advanced_plugin_manager)

基于 AstrBot 核心架构深度定制的插件管理系统。

## 核心设计与特性

1. **自然语言 LLM Tools 支持**
   - `configure_auto_update(enabled, interval_hours)`: 开启/关闭定时自动升级，设置周期（小时）。
   - `get_auto_update_status()`: 获取当前自动升级开关与周期。
   - `test_fastest_proxy()`: 测速并查看延迟最低的官方镜像站。
   - `update_plugin(plugin_name)`: 使用最低延迟镜像更新并热重载指定插件。
   - `reload_plugin(plugin_name)`: 热重载指定插件或所有插件（`all`）。
   - `reinstall_plugin(plugin_name)`: 覆盖重装插件。
   - `check_plugin_updates()`: 自动选优镜像检查更新。
   - `update_all_plugins()`: 批量升级新版本插件。

2. **动态并发测速选优**
   - 每次执行检查、安装、更新与定时任务前，并发测试官方候选镜像站延迟并使用最优节点。

3. **纯元数据版本判定**
   - 抛弃市场索引依赖，直连插件源地址读取 `metadata.yaml`，仅在云端版本增加时判定更新。

4. **原生覆盖重装**
   - 遵照官方重装机制保留数据和配置，无需卸载。

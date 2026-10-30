# 高级插件管理系统 (advanced_plugin_manager)

基于 AstrBot 核心架构深度定制的插件管理系统。

## 核心设计与特性

1. **动态并发测速选优**
   - 复用官方测速目标（`.python-version`）与官方镜像候选池。
   - 每次执行检查、安装、更新时并发测速，自动选取当前延迟最低的可用镜像透传。

2. **脱离市场索引，纯元数据版本判定**
   - 直连插件源地址读取 `metadata.yaml`，仅在云端版本递增时判定更新。

3. **原生覆盖重装**
   - 覆盖安装保留插件数据，无需卸载。

4. **自然语言 LLM Tools**
   - `test_fastest_proxy()`: 手动触发测速并查看最优节点。
   - `update_plugin(plugin_name)`: 使用最低延迟镜像更新并重载。
   - `reload_plugin(plugin_name)`: 热重载指定或全部插件。
   - `reinstall_plugin(plugin_name)`: 覆盖重装插件。
   - `check_plugin_updates()`: 自动选优镜像检查更新。
   - `update_all_plugins()`: 批量升级新版本插件。

5. **后台定时轮询自动升级**

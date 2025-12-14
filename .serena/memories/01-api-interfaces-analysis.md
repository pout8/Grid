# Grid 项目 - API 接口分析

## 接口分组概览

### 1. 认证模块 (Auth - FastAPI)
**位置**: `src/fastapi_app/routers/auth.py`

#### POST /api/auth/login
- **源码**: `src/fastapi_app/routers/auth.py:27`
- **功能**: 用户名+密码换取 JWT
- **请求体**:
  ```yaml
  username: str
  password: str
  ```
- **响应**: `TokenResponse {access_token, token_type, expires_in, user}`
- **错误**: `401 无效凭据`
- **使用场景**: 前端登录、CLI 自动化脚本登录

#### POST /api/auth/logout
- **源码**: `src/fastapi_app/routers/auth.py:53`
- **功能**: 逻辑注销（审计记录）
- **请求头**: `Authorization: Bearer <token>`
- **响应**: `{message}`
- **使用场景**: 清理 token、本地存储

#### POST /api/auth/change-password
- **源码**: `src/fastapi_app/routers/auth.py:68`
- **功能**: 校验旧密码、更新 hash、发行新 JWT
- **请求体**:
  ```yaml
  old_password: str (>=6 chars)
  new_password: str (>=6 chars)
  ```
- **响应**: `{message, access_token,...}`
- **错误**: `400 旧密码错误/弱密码`
- **使用场景**: 安全审计要求的定期换密

#### GET /api/auth/me
- **源码**: `src/fastapi_app/routers/auth.py:105`
- **功能**: 返回当前用户资料
- **请求头**: `Authorization`
- **响应**: `UserInfo`
- **使用场景**: 前端展示头像/角色

#### GET /api/auth/verify
- **源码**: `src/fastapi_app/routers/auth.py:115`
- **功能**: 轻量校验 token 有效性
- **请求头**: `Authorization`
- **响应**: `{valid, user_id, username}`
- **使用场景**: SSE 等长连接在建立前探测 token

---

### 2. 配置管理模块 (Config Management - FastAPI)
**位置**: `src/fastapi_app/routers/config.py`

#### GET /api/configs
- **源码**: `src/fastapi_app/routers/config.py:41`
- **功能**: 带分页/过滤的配置查询
- **查询参数**:
  ```yaml
  page: int>=1
  page_size: 1..100
  search: 可选模糊字段
  type: ConfigTypeEnum
  status: ConfigStatusEnum
  requires_restart: bool
  ```
- **响应**: `{total, page, items:[Configuration]}`
- **使用场景**: 前端配置表格、API 集成

#### GET /api/configs/{config_id}
- **源码**: `src/fastapi_app/routers/config.py:123`
- **功能**: 按 ID 获取配置详情
- **路径参数**: `config_id: int`
- **响应**: `Configuration`
- **错误**: `404`
- **使用场景**: 加载编辑表单

#### POST /api/configs
- **源码**: `src/fastapi_app/routers/config.py:143`
- **功能**: 创建新配置并写入历史记录
- **请求体**: `ConfigCreate (key/type/value/metadata)`
- **响应**: `新 Configuration`
- **错误**: `400 重复 key/非法枚举`
- **使用场景**: 扩展交易参数或添加 API 密钥引用

#### PUT /api/configs/{config_id}
- **源码**: `src/fastapi_app/routers/config.py:222`
- **功能**: 更新配置、追加版本历史
- **请求体**: `ConfigUpdate (config_value + 可选元数据)`
- **响应**: `更新后的 Configuration`
- **错误**: `404 未找到`
- **使用场景**: 策略参数热调优

#### DELETE /api/configs/{config_id}
- **源码**: `src/fastapi_app/routers/config.py:285`
- **功能**: 删除非必需配置，级联历史
- **使用场景**: 废弃配置、防止冲突

#### POST /api/configs/batch-update
- **源码**: `src/fastapi_app/routers/config.py:323`
- **功能**: 批量更新并返回 require_restart 聚合
- **请求体**:
  ```yaml
  updates: [{id, config_value}, ...]
  change_reason: str
  ```
- **响应**: `{updated, failed, requires_restart, details[]}`
- **使用场景**: 一次性切换多交易对参数

#### POST /api/configs/reload
- **源码**: `src/fastapi_app/routers/config.py:433`
- **功能**: 触发 `config_loader.reload()` 并调用各 GridTrader.update_config
- **响应**: `{cache_size, warning, traders_updated}`
- **使用场景**: 配置热生效

#### GET /api/configs/export
- **源码**: `src/fastapi_app/routers/config.py:471`
- **功能**: 导出 JSON，支持类型筛选与敏感字段过滤
- **查询参数**:
  ```yaml
  config_type: optional enum
  include_sensitive: bool (默认 false)
  ```
- **响应**: `下载 JSON (StreamingResponse)`
- **使用场景**: 备份/发版审查

#### POST /api/configs/import
- **源码**: `src/fastapi_app/routers/config.py:557`
- **功能**: 导入 JSON，支持覆盖/备份
- **表单参数**:
  ```yaml
  file: application/json
  overwrite: bool
  create_backup: bool
  ```
- **响应**: `{message, imported/skipped/failed,...}`
- **使用场景**: 迁移配置、灾备恢复

---

### 3. 配置历史模块 (Config History - FastAPI)
**位置**: `src/fastapi_app/routers/history.py`

#### GET /api/configs/{config_id}/history
- **源码**: `src/fastapi_app/routers/history.py:23`
- **功能**: 返回最近 N 条版本记录
- **查询参数**: `limit: 1..200`
- **响应**: `[ConfigHistoryResponse]`
- **使用场景**: 审计、比较差异

#### POST /api/configs/{config_id}/rollback
- **源码**: `src/fastapi_app/routers/history.py:50`
- **功能**: 将配置回滚到指定版本、生成新版本
- **请求体**:
  ```yaml
  version: int
  reason: optional str
  ```
- **响应**: `{message, from_version, new_version, requires_restart}`
- **使用场景**: 快速恢复稳定版本

---

### 4. 配置模板模块 (Config Templates)
**位置**: `src/fastapi_app/routers/template.py`

#### GET /api/templates
- **源码**: `src/fastapi_app/routers/template.py:23`
- **功能**: 按类型/系统模板筛选模板列表
- **响应**: `{total, items:[Template]}`

#### GET /api/templates/{template_id}
- **源码**: `src/fastapi_app/routers/template.py:51`
- **功能**: 查看模板 JSON 内容

#### POST /api/templates/{template_id}/apply
- **源码**: `src/fastapi_app/routers/template.py:73`
- **功能**: 批量应用模板项，写历史并累加 usage_count
- **响应**: `{applied, message}`

---

### 5. 实时通信模块 (Realtime - SSE)
**位置**: `src/fastapi_app/routers/sse.py`, `src/api/routes/sse_routes.py`

> **注意**: FastAPI 版本使用 query token，aiohttp 版本使用 Header

#### GET /api/sse/events (FastAPI)
- **源码**: `src/fastapi_app/routers/sse.py:88`
- **功能**: 基于 StreamingResponse 的 SSE Feed
- **查询参数**: `token: JWT (url encoded)`
- **响应**: `event-stream (connected + push events)`
- **使用场景**: 前端配置变更提醒

#### GET /api/sse/status (FastAPI)
- **源码**: `src/fastapi_app/routers/sse.py:116`
- **功能**: 返回当前队列数量

#### GET /api/sse/events (aiohttp)
- **源码**: `src/api/routes/sse_routes.py:47`
- **功能**: 旧版 SSE，使用 Authorization 头

#### POST /api/sse/broadcast
- **源码**: `src/api/routes/sse_routes.py:110`
- **功能**: 手动推送事件给所有 SSE 客户端
- **使用场景**: 测试

#### GET /api/sse/status (aiohttp)
- **源码**: `src/api/routes/sse_routes.py:141`
- **功能**: legacy 连接统计

---

### 6. 仪表盘与监控模块 (Dashboard & Monitoring)

#### GET /api/dashboard/status
- **源码**: `src/fastapi_app/routers/dashboard.py:202`
- **功能**: 聚合 trader 状态、资产、最近交易、性能占位
- **请求头**: `Authorization`
- **响应**: `{success, data:{dashboard/system/symbols/...}}`

#### GET /api/dashboard/quick-stats
- **源码**: `src/fastapi_app/routers/dashboard.py:296`
- **功能**: 轻量状态，仅返回核心统计

#### GET /api/logs/list
- **源码**: `src/fastapi_app/routers/logs.py:154`
- **功能**: 分页读取日志文件，支持级别+关键词

#### GET /api/logs/files
- **源码**: `src/fastapi_app/routers/logs.py:203`
- **功能**: 列举 log 目录下 *.log 文件

#### GET /api/logs/stream
- **源码**: `src/fastapi_app/routers/logs.py:299`
- **功能**: SSE 实时日志推送，附心跳

#### GET /api/trades/list
- **源码**: `src/fastapi_app/routers/trades.py:159`
- **功能**: 基于内存 trade_history 的分页查询+summary

#### GET /api/trades/symbols
- **源码**: `src/fastapi_app/routers/trades.py:219`
- **功能**: 列举有交易记录的 symbol

#### GET /api/trades/statistics
- **源码**: `src/fastapi_app/routers/trades.py:252`
- **功能**: 按周期/交易对输出绩效统计+每日图

#### GET /api/metrics
- **源码**: `src/fastapi_app/routers/metrics.py:44`
- **功能**: 需要认证的 Prometheus payload

#### GET /metrics
- **源码**: `src/fastapi_app/main.py:93`
- **功能**: 公开 Prometheus 端点，供 Prom 抓取

#### GET /api/health
- **源码**: `src/fastapi_app/main.py:58`
- **功能**: 无认证健康检查

---

### 7. 网格策略服务模块 (Grid Strategy Service)
**位置**: `src/api/routes/grid_strategy_routes.py`

> **注意**: 使用本地 JSON 文件模拟策略存储

#### POST /api/grid-strategies
- **源码**: `src/api/routes/grid_strategy_routes.py:131`
- **功能**: 依据 `GridStrategyConfig` 创建策略，序列化到 /src/api/data/strategies

#### GET /api/grid-strategies
- **源码**: `src/api/routes/grid_strategy_routes.py:163`
- **功能**: 列出所有策略文件

#### GET /api/grid-strategies/{strategy_id}
- **源码**: `src/api/routes/grid_strategy_routes.py:186`
- **功能**: 读取指定策略 JSON

#### PUT /api/grid-strategies/{strategy_id}
- **源码**: `src/api/routes/grid_strategy_routes.py:206`
- **功能**: 覆盖式更新策略

#### DELETE /api/grid-strategies/{strategy_id}
- **源码**: `src/api/routes/grid_strategy_routes.py:245`
- **功能**: 删除对应文件

#### GET /api/grid-strategies/templates/list
- **源码**: `src/api/routes/grid_strategy_routes.py:265`
- **功能**: 返回内置 conservative/aggressive 模板说明

#### POST /api/grid-strategies/templates/{template_name}
- **源码**: `src/api/routes/grid_strategy_routes.py:288`
- **功能**: 用模板生成策略 (默认 symbol=BNB/USDT)

#### POST /api/grid-strategies/{strategy_id}/start
- **源码**: `src/api/routes/grid_strategy_routes.py:332`
- **功能**: 占位：未来对接 GridTrader 启动

#### POST /api/grid-strategies/{strategy_id}/stop
- **源码**: `src/api/routes/grid_strategy_routes.py:360`
- **功能**: 占位：未来停止策略

---

### 8. 遗留配置扩展 (Legacy Config Extras)

#### GET /api/config-definitions
- **源码**: `src/api/routes/config_routes.py:857`
- **功能**: 透出 `config_definitions.ALL_CONFIGS` (按 key 或 type)
- **使用场景**: 前端动态表单/CLI 生成器

---

## 核心特点总结

1. **双框架支持**: FastAPI 为主入口，部分 aiohttp 兼容层
2. **配置中心化**: 所有配置通过数据库+缓存+热重载机制管理
3. **实时通信**: SSE 支持配置变更推送和日志流式传输
4. **监控完整**: Prometheus 指标 + 仪表盘 API + 交易统计
5. **安全认证**: JWT 统一认证，SSE 兼容 query token
6. **版本控制**: 配置历史追踪与回滚机制
7. **模板系统**: 配置模板批量应用

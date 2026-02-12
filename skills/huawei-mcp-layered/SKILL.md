---
name: huawei-mcp-layered
description: Use this skill when users need a layered Huawei MCP discovery flow: first locate Group Name, then Product Name, and finally fetch MCP API schemas via mcp_collect.py.
---

# Huawei MCP Layered Discovery

## 适用场景
当用户要按“**Group Name -> Product Name -> MCP API**”分层定位华为云 MCP 能力时，使用此技能。

## 工作流
1. 先列出 Group Name。
2. 在目标 Group 内列出 Product Name。
3. 选定 Product 后，调用项目根目录 `mcp_collect.py` 收集 API schema。

## 执行命令
优先使用脚本：`scripts/hierarchy_query.py`。

```bash
# 1) 查看所有 Group
python skills/huawei-mcp-layered/scripts/hierarchy_query.py --list-groups

# 2) 查看某个 Group 下的 Product
python skills/huawei-mcp-layered/scripts/hierarchy_query.py --group "管理与监管"

# 3) 锁定 Product 并输出元信息
python skills/huawei-mcp-layered/scripts/hierarchy_query.py --group "管理与监管" --product "云监控服务"

# 4) 锁定 Product 后收集 MCP API schema（调用 mcp_collect.py）
python skills/huawei-mcp-layered/scripts/hierarchy_query.py \
  --group "管理与监管" \
  --product "云监控服务" \
  --collect-api \
  --output ces_schema.json
```

## 实现说明
- Group/Product 来源：根目录 `README_zh.md` 中工具表格。
- API 采集来源：根目录 `mcp_collect.py`。
- 若某 Product 无法推断启动命令（`mcp-server-xxx`），先提示用户手动提供命令，再用 `mcp_collect.py` 采集。

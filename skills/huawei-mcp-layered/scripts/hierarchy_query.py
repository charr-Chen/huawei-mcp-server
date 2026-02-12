#!/usr/bin/env python3
"""分层查询华为云 MCP Server：Group -> Product -> API Schema。"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[3]
README_ZH = PROJECT_ROOT / "README_zh.md"
MCP_COLLECT = PROJECT_ROOT / "mcp_collect.py"


@dataclass
class ProductRecord:
    group: str
    product_name: str
    product_short: str
    repo_path: Optional[str]


def _extract_rows(table_html: str) -> List[ProductRecord]:
    rows = re.findall(r"<tr>(.*?)</tr>", table_html, flags=re.S)
    products: List[ProductRecord] = []
    current_group: Optional[str] = None

    for row in rows:
        tds = re.findall(r"<td(?:\s+rowspan=\"\d+\")?>(.*?)</td>", row, flags=re.S)
        if not tds:
            continue

        cleaned = [re.sub(r"<.*?>", "", col).strip() for col in tds]
        href_match = re.search(r'href="([^"]+)"', row)
        repo_path = None
        if href_match:
            href = href_match.group(1)
            marker = "mcp-server/tree/master-dev/"
            if marker in href:
                repo_path = href.split(marker, 1)[1]

        if len(cleaned) == 3:
            current_group = cleaned[0]
            product_name = cleaned[1]
            product_short = cleaned[2]
        elif len(cleaned) == 2 and current_group:
            product_name = cleaned[0]
            product_short = cleaned[1]
        else:
            continue

        products.append(
            ProductRecord(
                group=current_group or "未分组",
                product_name=product_name,
                product_short=product_short,
                repo_path=repo_path,
            )
        )

    return products


def load_hierarchy() -> Dict[str, List[ProductRecord]]:
    content = README_ZH.read_text(encoding="utf-8")
    match = re.search(r"<table.*?</table>", content, flags=re.S)
    if not match:
        raise RuntimeError("在 README_zh.md 中没有找到产品表格。")

    products = _extract_rows(match.group(0))
    hierarchy: Dict[str, List[ProductRecord]] = {}
    for item in products:
        hierarchy.setdefault(item.group, []).append(item)
    return hierarchy


def infer_server_command(record: ProductRecord) -> Optional[str]:
    if not record.repo_path:
        return None
    repo_name = Path(record.repo_path).name
    if repo_name.startswith("mcp_server_"):
        return f"mcp-server-{repo_name.replace('mcp_server_', '')}"
    return None


def list_groups(hierarchy: Dict[str, List[ProductRecord]]) -> None:
    print("可用 Group Name:")
    for group in sorted(hierarchy):
        print(f"- {group} ({len(hierarchy[group])})")


def list_products(hierarchy: Dict[str, List[ProductRecord]], group_name: str) -> List[ProductRecord]:
    items = hierarchy.get(group_name, [])
    if not items:
        raise ValueError(f"未找到分组: {group_name}")

    print(f"Group: {group_name}")
    for idx, item in enumerate(items, start=1):
        command = infer_server_command(item) or "N/A"
        print(f"{idx:02d}. {item.product_name} | short={item.product_short} | command={command}")
    return items


def find_product(hierarchy: Dict[str, List[ProductRecord]], group_name: str, product: str) -> ProductRecord:
    for item in hierarchy.get(group_name, []):
        if item.product_name == product or item.product_short.lower() == product.lower():
            return item
    raise ValueError(f"在分组 {group_name} 中未找到产品: {product}")


def collect_api(record: ProductRecord, output: str) -> None:
    command = infer_server_command(record)
    if not command:
        raise RuntimeError(f"产品 {record.product_name} 缺少可推断的启动命令。")

    cmd = [
        sys.executable,
        str(MCP_COLLECT),
        "--command",
        command,
        "--output",
        output,
    ]
    print("执行:", " ".join(cmd))
    subprocess.run(cmd, cwd=str(PROJECT_ROOT), check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="分层查询 Huawei MCP 服务")
    parser.add_argument("--list-groups", action="store_true", help="查看所有分组")
    parser.add_argument("--group", help="指定 Group Name")
    parser.add_argument("--product", help="指定 Product Name 或 Product Short")
    parser.add_argument("--collect-api", action="store_true", help="调用 mcp_collect.py 收集 API")
    parser.add_argument("--output", default="mcp_schemas.json", help="API 输出文件")
    parser.add_argument("--json", action="store_true", help="用 JSON 输出查询结果")

    args = parser.parse_args()
    hierarchy = load_hierarchy()

    if args.list_groups:
        list_groups(hierarchy)
        return

    if args.group and not args.product:
        items = list_products(hierarchy, args.group)
        if args.json:
            payload = [item.__dict__ for item in items]
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    if args.group and args.product:
        record = find_product(hierarchy, args.group, args.product)
        if args.json:
            print(json.dumps(record.__dict__, indent=2, ensure_ascii=False))
        else:
            command = infer_server_command(record)
            print(f"Group: {record.group}")
            print(f"Product: {record.product_name}")
            print(f"Short: {record.product_short}")
            print(f"Repo: {record.repo_path or 'N/A'}")
            print(f"Command: {command or 'N/A'}")

        if args.collect_api:
            collect_api(record, args.output)
        return

    parser.error("请使用 --list-groups，或组合 --group/--product 参数。")


if __name__ == "__main__":
    main()

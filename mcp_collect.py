#!/usr/bin/env python3
"""
MCP服务器API Schema获取脚本
需要安装：pip install mcp
"""

import asyncio
import json
import sys
from typing import Dict, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def get_server_schemas(server_command: str, args: list = None) -> Dict[str, Any]:
    """
    连接到MCP服务器并获取所有API的Input Schema
    
    Args:
        server_command: 启动MCP服务器的命令
        args: 服务器命令行参数
    
    Returns:
        包含所有工具schema的字典
    """
    if args is None:
        args = []
    
    schemas = {}
    
    try:
        # 创建服务器参数
        server_params = StdioServerParameters(
            command=server_command,
            args=args
        )
        
        # 创建stdio客户端连接
        async with stdio_client(server_params) as (read_stream, write_stream):
            # 创建客户端会话
            async with ClientSession(read_stream, write_stream) as session:
                # 初始化会话
                await session.initialize()
                
                # 列出所有可用工具
                tools_response = await session.list_tools()
                
                print(f"发现 {len(tools_response.tools)} 个工具:")
                print("-" * 50)
                
                # 获取每个工具的详细信息
                for tool in tools_response.tools:
                    print(f"工具名称: {tool.name}")
                    print(f"描述: {tool.description}")
                    
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        print("Input Schema:")
                        print(json.dumps(tool.inputSchema, indent=2, ensure_ascii=False))
                        schemas[tool.name] = {
                            "description": tool.description,
                            "inputSchema": tool.inputSchema,
                            "parameters": getattr(tool, 'parameters', {})
                        }
                    else:
                        print("无Input Schema定义")
                        schemas[tool.name] = {
                            "description": tool.description,
                            "inputSchema": None
                        }
                    
                    print("-" * 50)
                
                return schemas
                
    except Exception as e:
        print(f"连接服务器时出错: {e}", file=sys.stderr)
        return {}

def save_schemas_to_file(schemas: Dict[str, Any], filename: str = "mcp_schemas.json"):
    """将schema保存到JSON文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(schemas, f, indent=2, ensure_ascii=False)
    print(f"\nSchema已保存到 {filename}")

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='获取MCP服务器的API Input Schema')
    parser.add_argument('--command', '-c', required=True,
                       help='MCP服务器启动命令')
    parser.add_argument('--args', '-a', nargs='*', default=[],
                       help='MCP服务器参数')
    parser.add_argument('--output', '-o', default='mcp_schemas.json',
                       help='输出文件名（默认：mcp_schemas.json）')
    
    args = parser.parse_args()
    
    print("正在连接到MCP服务器...")
    schemas = await get_server_schemas(args.command, args.args)
    
    if schemas:
        save_schemas_to_file(schemas, args.output)
        
        # 生成简要报告
        print("\n=== Schema统计 ===")
        print(f"总工具数: {len(schemas)}")
        with_schema = sum(1 for s in schemas.values() if s['inputSchema'])
        print(f"包含Schema的工具: {with_schema}")
        print(f"无Schema的工具: {len(schemas) - with_schema}")
    else:
        print("未获取到任何schema信息")

if __name__ == "__main__":
    asyncio.run(main())
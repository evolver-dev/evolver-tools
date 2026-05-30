#!/usr/bin/env python3
"""portcheck — 端口检查与查找工具。零外部依赖。"""
import socket
import sys

def check_port(port, host="127.0.0.1"):
    """检查端口是否被占用"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect((host, port))
        s.close()
        return True
    except (ConnectionRefusedError, OSError):
        return False

def find_free_port(start, end=None):
    """查找空闲端口"""
    end = end or start + 100
    for port in range(start, end + 1):
        if not check_port(port):
            return port
    return None

def format_output(port, in_use):
    status = "🔴 已占用" if in_use else "🟢 空闲"
    return f"Port {port:<5} {status}"

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("用法:")
        print("  portcheck <port>            — 检查指定端口")
        print("  portcheck --free [start] [end] — 查找空闲端口")
        print("  portcheck --list <start>-<end>   — 列出端口状态范围")
        print("示例:")
        print("  portcheck 3000")
        print("  portcheck --free 3000 3100")
        print("  portcheck --list 3000-3010")
        return

    if args[0] == "--free":
        start = int(args[1]) if len(args) > 1 else 3000
        end = int(args[2]) if len(args) > 2 else start + 100
        port = find_free_port(start, end)
        if port:
            print(f"✅ 空闲端口: {port}")
        else:
            print(f"❌ 在 {start}-{end} 范围内未找到空闲端口")
    elif args[0] == "--list":
        parts = args[1].split("-") if len(args) > 1 else []
        start = int(parts[0]) if parts else 3000
        end = int(parts[1]) if len(parts) > 1 else start + 10
        for port in range(start, end + 1):
            print(format_output(port, check_port(port)))
    else:
        port = int(args[0])
        if port < 1 or port > 65535:
            print(f"❌ 端口号必须在 1-65535 范围内: {port}", file=sys.stderr)
            sys.exit(1)
        in_use = check_port(port)
        print(format_output(port, in_use))
        sys.exit(0 if not in_use else 1)

if __name__ == "__main__":
    main()

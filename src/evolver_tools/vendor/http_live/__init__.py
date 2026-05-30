"""
http-live — 零依赖热重载 HTTP 服务器

一个纯 Python 的静态文件服务器，当文件变化时自动刷新浏览器。
零外部依赖，仅使用 Python 标准库。

Usage:
    http-live                    # 当前目录，端口 8000
    http-live --port 3000        # 自定义端口
    http-live --dir ./dist       # 自定义目录
    http-live --poll 1.0         # 轮询间隔(秒)
    http-live --no-browser       # 不自动打开浏览器
"""

import argparse
import http.server
import json
import os
import queue
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path


REFRESH_SCRIPT = """
<script>
(function() {
    var es = new EventSource('/__http_live/reload');
    es.onmessage = function(e) {
        if (e.data === 'refresh') {
            location.reload();
        }
    };
    es.onerror = function() {
        // 如果 SSE 连接断开，静默重连
        es.close();
        setTimeout(function() {
            location.reload();
        }, 2000);
    };
})();
</script>
"""


class LiveHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """在 HTML 响应中注入热重载脚本的请求处理器"""

    def __init__(self, *args, **kwargs):
        self._directory = kwargs.pop("live_dir", None) or os.getcwd()
        self._event_queue = kwargs.pop("event_queue")
        super().__init__(*args, directory=self._directory, **kwargs)

    def send_head(self):
        path = self.translate_path(self.path)
        if self.path.endswith("/__http_live/reload"):
            return self._handle_sse()
        return super().send_head()

    def _handle_sse(self):
        """处理 SSE 连接"""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        def stream():
            try:
                while True:
                    try:
                        msg = self._event_queue.get(timeout=30)
                        self.wfile.write(f"data: {msg}\n\n".encode())
                        self.wfile.flush()
                    except queue.Empty:
                        # 发送心跳保持连接
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass

        threading.Thread(target=stream, daemon=True).start()
        return None  # 阻止默认响应

    def copyfile(self, source, outputfile):
        content = source.read()
        source.seek(0)
        path = self.translate_path(self.path)

        if self.path.endswith(".html"):
            modified = source.read().decode("utf-8", errors="replace")
            # 在 </body> 前注入刷新脚本
            if "</body>" in modified:
                modified = modified.replace("</body>", REFRESH_SCRIPT + "\n</body>")
            else:
                modified += REFRESH_SCRIPT
            outputfile.write(modified.encode("utf-8"))
        else:
            super().copyfile(source, outputfile)


class FileWatcher(threading.Thread):
    """基于轮询的文件变化检测器"""

    def __init__(self, watch_dir, poll_interval=0.5, event_queue=None):
        super().__init__(daemon=True)
        self.watch_dir = Path(watch_dir).resolve()
        self.poll_interval = poll_interval
        self.event_queue = event_queue
        self._mtime_cache = {}
        self._running = True
        self.name = "FileWatcher"

    def run(self):
        self._scan_initial()
        while self._running:
            time.sleep(self.poll_interval)
            self._check_changes()

    def stop(self):
        self._running = False

    def _scan_initial(self):
        for path in self._walk():
            try:
                self._mtime_cache[str(path)] = path.stat().st_mtime
            except OSError:
                pass

    def _walk(self):
        for root, dirs, files in os.walk(self.watch_dir):
            # 跳过隐藏目录和 __pycache__
            dirs[:] = [d for d in dirs
                       if not d.startswith(".")
                       and d != "__pycache__"
                       and d != "node_modules"
                       and d != ".git"]
            for f in files:
                if f.startswith("."):
                    continue
                yield Path(root) / f

    def _check_changes(self):
        current = {}
        changed = False
        for path in self._walk():
            try:
                mtime = path.stat().st_mtime
                current[str(path)] = mtime
                cached = self._mtime_cache.get(str(path))
                if cached is None or abs(mtime - cached) > 0.01:
                    changed = True
                    # 打印日志到 stderr（不干扰 SSE 流）
                    relative = path.relative_to(self.watch_dir)
                    print(f"  \u2728 Changed: {relative}", file=sys.stderr)
            except OSError:
                continue

        # 检测文件删除
        for path_str in list(self._mtime_cache.keys()):
            if path_str not in current:
                changed = True
                try:
                    rel = Path(path_str).relative_to(self.watch_dir)
                    print(f"  \u274c Removed: {rel}", file=sys.stderr)
                except ValueError:
                    pass

        if changed:
            self._mtime_cache = current
            if self.event_queue:
                self.event_queue.put("refresh")


def _find_open_port(start=8000, end=9999):
    """找到可用端口"""
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="http-live — 零依赖热重载 HTTP 服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  http-live                    # 当前目录，端口 8000
  http-live --port 3000        # 自定义端口
  http-live --dir ./dist       # 自定义目录
  http-live --poll 1.0         # 轮询间隔 1 秒
        """,
    )
    parser.add_argument("--port", "-p", type=int, default=8000, help="端口号 (默认: 8000)")
    parser.add_argument("--dir", "-d", type=str, default=".", help="服务目录 (默认: 当前目录)")
    parser.add_argument("--poll", type=float, default=0.5, help="文件轮询间隔秒数 (默认: 0.5)")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    parser.add_argument("--version", "-v", action="version", version="http-live 1.0.0")

    args = parser.parse_args()

    serve_dir = os.path.abspath(args.dir)
    if not os.path.isdir(serve_dir):
        print(f"错误: 目录不存在: {serve_dir}", file=sys.stderr)
        sys.exit(1)

    port = _find_open_port(args.port)
    if port == 0:
        print("错误: 找不到可用端口", file=sys.stderr)
        sys.exit(1)

    event_queue = queue.Queue()

    # 启动文件监控
    watcher = FileWatcher(
        watch_dir=serve_dir,
        poll_interval=args.poll,
        event_queue=event_queue,
    )
    watcher.start()

    # 创建服务器
    handler = lambda *h_args, **h_kwargs: LiveHTTPRequestHandler(
        *h_args, live_dir=serve_dir, event_queue=event_queue, **h_kwargs
    )

    server = http.server.HTTPServer(("127.0.0.1", port), handler)

    url = f"http://127.0.0.1:{port}"

    print(f"")
    print(f"  \U0001f525 http-live started")
    print(f"  \ud83d\udcc1 Serving: {serve_dir}")
    print(f"  \ud83c\udf10 URL:      {url}")
    print(f"  \u23f3 Watching:  every {args.poll}s")
    print(f"  \u241b Quit:      Ctrl+C")
    print(f"")

    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  \ud83d\udc4b Shutting down...")
        watcher.stop()
        server.shutdown()
        print("  Done.")
        sys.exit(0)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "http-live",
    "func": "main",
    "desc": 'HTTP Live Server',
}

if __name__ == "__main__":
    main()

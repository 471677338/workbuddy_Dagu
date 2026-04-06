"""
Claude Code TUI 中间件 v3 - T8 版本
支持 OpenAI 兼容 API (ai.t8star.cn)

配置:
    MODEL_PROVIDER=openai
    OPENAI_BASE_URL=https://ai.t8star.cn/v1
    OPENAI_API_KEY=sk-xxx
    OPENAI_MODEL=claude-opus-4-6
    DISABLE_TELEMETRY=1
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1

运行:
    python claw_tui_bridge.py              # 启动 HTTP API 服务
    python claw_tui_bridge.py --test       # 测试模式
    python claw_tui_bridge.py --task "..." # 直接运行任务
    python claw_tui_bridge.py --tui        # 启动交互式 TUI
"""

# Windows 下强制 UTF-8 输出，避免 GBK 无法编码 emoji 等字符
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import os
import sys
import json
import time
import asyncio
import ctypes
import struct
import subprocess
import threading
import re
from typing import Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from io import StringIO


def _safe_print(msg: str):
    """打印时忽略 Windows GBK 无法编码的字符（如 emoji）"""
    try:
        print(msg)
    except (UnicodeEncodeError, OSError):
        try:
            print(msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
        except Exception:
            pass

# ============================================================
# Windows ConPTY 支持
# ============================================================

@dataclass
class ConsoleScreenInfo:
    width: int = 120
    height: int = 40
    cursor_x: int = 0
    cursor_y: int = 0


class ConPTYProcess:
    """
    Windows ConPTY 子进程管理器
    使用 Windows Pseudo Console API 创建可控的终端
    """

    def __init__(self, rows: int = 40, cols: int = 120):
        self.rows = rows
        self.cols = cols
        self.process: Optional[subprocess.Popen] = None
        self.started = False
        self.output_buffer = ""
        self._reader_thread: Optional[threading.Thread] = None
        self._running = False
        self._callbacks: list[Callable[[str], None]] = []

        # ANSI 转义序列清除
        self.ansi_re = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

    def _init_pty_windows(self) -> bool:
        """Windows ConPTY 初始化"""
        try:
            # 获取 Windows 版本
            class OSVERSIONINFOW(ctypes.Structure):
                _fields_ = [
                    ("dwOSVersionInfoSize", ctypes.c_ulong),
                    ("dwMajorVersion", ctypes.c_ulong),
                    ("dwMinorVersion", ctypes.c_ulong),
                    ("dwBuildNumber", ctypes.c_ulong),
                    ("dwPlatformId", ctypes.c_ulong),
                    ("szCSDVersion", ctypes.c_wchar * 128)
                ]

            ver = OSVERSIONINFOW()
            ver.dwOSVersionInfoSize = ctypes.sizeof(ver)
            ctypes.windll.kernel32.GetVersionExW(ctypes.byref(ver))

            # Windows 10 1903+ 才支持 ConPTY
            if ver.dwMajorVersion < 10 or ver.dwBuildNumber < 18362:
                print("[ConPTY] Windows version too old (need 1903+)")
                return False

            print(f"[ConPTY] Windows {ver.dwMajorVersion}.{ver.dwMinorVersion} Build {ver.dwBuildNumber}")
            return True
        except Exception as e:
            print(f"[ConPTY] Init error: {e}")
            return False

    def start(self, command: list[str], cwd: Optional[str] = None) -> bool:
        """启动子进程"""
        if self._init_pty_windows():
            return self._start_with_pty(command, cwd)
        else:
            return self._start_fallback(command, cwd)

    def _start_with_pty(self, command: list[str], cwd: Optional[str] = None) -> bool:
        """使用 ConPTY 启动"""
        try:
            from ctypes import wintypes, POINTER, Structure, byref, create_string_buffer
            kernel32 = ctypes.windll.kernel32

            # 创建 ConPTY
            class COORD(ctypes.Structure):
                _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

            size = COORD(self.cols, self.rows)

            # 调用 CreatePseudoConsole
            CreatePseudoConsole = kernel32.CreatePseudoConsole
            CreatePseudoConsole.argtypes = [COORD, wintypes.HANDLE, wintypes.HANDLE, DWORD]
            CreatePseudoConsole.restype = wintypes.HANDLE

            # 创建管道
            class SECURITY_ATTRIBUTES(ctypes.Structure):
                _fields_ = [
                    ("nLength", ctypes.c_ulong),
                    ("lpSecurityDescriptor", ctypes.c_void_p),
                    ("bInheritHandle", ctypes.c_bool)
                ]

            sa = SECURITY_ATTRIBUTES()
            sa.nLength = ctypes.sizeof(sa)
            sa.bInheritHandle = True
            sa.lpSecurityDescriptor = 0

            # 创建 ConPTY（同步 API 不可用，需要异步）
            pty_handle = wintypes.HANDLE()
            hr = CreatePseudoConsole(size, None, None, byref(pty_handle))

            if hr != 0:
                print(f"[ConPTY] CreatePseudoConsole failed: {hr}")
                return self._start_fallback(command, cwd)

            print(f"[ConPTY] Created pseudo console: {pty_handle.value}")

            # 使用 STARTUPINFOEXW 和 ConPTY
            class STARTUPINFOEXW(ctypes.Structure):
                _fields_ = [("StartupInfo", wintypes.STARTUPINFOW), ("lpAttributeList", ctypes.c_void_p)]

            startupinfo = STARTUPINFOEXW()
            startupinfo.StartupInfo.cb = ctypes.sizeof(STARTUPINFOEXW)

            class PROCESS_INFORMATION(ctypes.Structure):
                _fields_ = [
                    ("hProcess", wintypes.HANDLE),
                    ("hThread", wintypes.HANDLE),
                    ("dwProcessId", wintypes.DWORD),
                    ("dwThreadId", wintypes.DWORD)
                ]

            process_info = PROCESS_INFORMATION()

            # 启动进程
            cmd_str = " ".join(f'"{c}"' for c in command)
            CreateProcessAsUserW = kernel32.CreateProcessAsUserW
            CreateProcessAsUserW.argtypes = [
                wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.LPVOID,
                ctypes.c_void_p, ctypes.c_void_p, wintypes.BOOL,
                wintypes.DWORD, wintypes.LPCVOID, wintypes.LPCWSTR,
                ctypes.POINTER(wintypes.STARTUPINFOW), ctypes.POINTER(PROCESS_INFORMATION)
            ]

            result = CreateProcessAsUserW(
                None, cmd_str, None, None, True,
                0x00000010,  # CREATE_NEW_CONSOLE
                None, cwd or os.getcwd(),
                byref(startupinfo.StartupInfo),
                byref(process_info)
            )

            if result:
                print(f"[ConPTY] Process started: PID={process_info.dwProcessId}")
                self.started = True
                self._running = True
                return True

            return self._start_fallback(command, cwd)

        except Exception as e:
            print(f"[ConPTY] Error: {e}")
            return self._start_fallback(command, cwd)

    def _start_fallback(self, command: list[str], cwd: Optional[str] = None) -> bool:
        """降级方案：使用 Popen + 管道"""
        try:
            print("[Fallback] Using subprocess.Popen with pipes")
            self.process = subprocess.Popen(
                command,
                cwd=cwd or os.getcwd(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=False,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )
            self.started = True
            self._running = True

            # 启动输出读取线程
            self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._reader_thread.start()

            print(f"[Fallback] Process started: PID={self.process.pid}")
            return True
        except Exception as e:
            print(f"[Fallback] Error: {e}")
            return False

    def _read_loop(self):
        """后台读取子进程输出"""
        if not self.process or not self.process.stdout:
            return
        try:
            while self._running:
                try:
                    chunk = self.process.stdout.read(4096)
                    if not chunk:
                        break
                    self.output_buffer += chunk
                    for cb in self._callbacks:
                        try:
                            cb(chunk)
                        except:
                            pass
                except Exception:
                    break
        except Exception as e:
            print(f"[Reader] Error: {e}")

    def write(self, text: str) -> int:
        """发送输入到子进程"""
        if not self.process or not self.process.stdin:
            return 0
        try:
            self.process.stdin.write(text)
            self.process.stdin.write('\n')
            self.process.stdin.flush()
            return len(text)
        except Exception as e:
            print(f"[Write] Error: {e}")
            return 0

    def send_command(self, command: str) -> bool:
        """发送命令（带回车）"""
        return self.write(command) > 0

    def get_output(self) -> str:
        """获取所有输出"""
        return self.output_buffer

    def get_new_output(self, since: int = 0) -> str:
        """获取新增输出"""
        return self.output_buffer[since:]

    def on_output(self, callback: Callable[[str], None]):
        """注册输出回调"""
        self._callbacks.append(callback)

    def resize(self, rows: int, cols: int):
        """调整大小"""
        self.rows = rows
        self.cols = cols
        # ConPTY resize 需要重新创建

    def close(self):
        """关闭进程"""
        self._running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except:
                self.process.kill()
        self.started = False

    def is_alive(self) -> bool:
        """检查进程是否存活"""
        if not self.process:
            return False
        return self.process.poll() is None


# ============================================================
# CLI 包装器（Claude Code T8 - OpenAI 兼容 API）
# ============================================================

# T8 OpenAI 兼容配置（默认）
T8_DEFAULT_CONFIG = {
    "MODEL_PROVIDER": "openai",
    "OPENAI_BASE_URL": "https://ai.t8star.cn/v1",
    "OPENAI_MODEL": "claude-opus-4-6",
    "API_TIMEOUT_MS": "3000000",
    "DISABLE_TELEMETRY": "1",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
}


class ClawCLIBridge:
    """
    Claude Code T8 包装器
    支持 OpenAI 兼容 API (ai.t8star.cn)

    用法示例:
        bridge = ClawCLIBridge(
            t8_dir="G:\\work_software\\claw\\.workbuddy\\AI工具\\claude-code-t8-main",
            api_key="sk-xxx"
        )
        result = bridge.run_task("写一个Arduino舵机代码")
    """

    def __init__(
        self,
        t8_dir: str,
        api_key: str = None,
        model: str = None,
        base_url: str = None,
    ):
        self.t8_dir = t8_dir
        self.node_exe = self._find_node()
        self.bun_exe = self._find_bun()
        self.last_output = ""

        # API 配置（优先级：构造参数 > 环境变量 > T8 默认）
        self.config = dict(T8_DEFAULT_CONFIG)
        self._apply_env_overrides()
        if base_url:
            self.config["OPENAI_BASE_URL"] = base_url
        if model:
            self.config["OPENAI_MODEL"] = model
        self.config["OPENAI_API_KEY"] = api_key or self._load_api_key()

    def _find_node(self) -> str:
        """查找 Node.js 可执行文件（仅备用）"""
        import shutil
        node = shutil.which("node") or shutil.which("node.exe")
        if node:
            return node
        for path in [
            r"C:\Program Files\nodejs\node.exe",
            os.path.expanduser(r"~\AppData\Roaming\nvm\current\node.exe"),
        ]:
            if os.path.exists(path):
                return path
        return "node"

    def _find_bun(self) -> str:
        """查找 bun 可执行文件"""
        import shutil
        # 先找 PATH
        bun = shutil.which("bun") or shutil.which("bun.exe")
        if bun:
            return bun
        # 常见安装位置
        candidates = [
            os.path.join(os.environ.get("USERPROFILE", ""), ".bun", "bin", "bun.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "bun", "bun.exe"),
            r"C:\Users\guwenjin\.bun\bin\bun.exe",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return "bun"

    def _apply_env_overrides(self):
        """从环境变量覆盖默认配置"""
        for key in ["OPENAI_BASE_URL", "OPENAI_MODEL", "OPENAI_API_KEY",
                    "MODEL_PROVIDER", "API_TIMEOUT_MS"]:
            val = os.environ.get(key)
            if val:
                self.config[key] = val

    def _load_api_key(self) -> str:
        """从环境变量或配置文件加载 API key"""
        for key_name in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY",
                         "anthropic_api_key", "CLAUDE_API_KEY"]:
            key = os.environ.get(key_name)
            if key:
                return key

        # 尝试从 .env 文件读取
        for env_path in [
            Path(self.t8_dir) / ".env",
            Path.home() / ".workbuddy" / ".env",
            Path(os.environ.get("USERPROFILE", "~")) / ".env",
        ]:
            if env_path.exists():
                try:
                    content = env_path.read_text(encoding='utf-8')
                    for line in content.splitlines():
                        if '=' in line and 'API_KEY' in line.upper():
                            k, v = line.split('=', 1)
                            if v.strip():
                                return v.strip()
                except Exception:
                    pass
        return ""

    def _build_env(self) -> dict:
        """构建传递给子进程的环境变量"""
        _env = dict(os.environ)
        if not _env.get("HOME"):
            _env["HOME"] = _env.get("USERPROFILE") or os.path.expanduser("~")

        # 注入 T8 OpenAI 配置
        for key, val in self.config.items():
            _env[key] = val

        # 确保 bun 在 PATH 里（常见安装位置）
        bun_dirs = [
            os.path.join(_env.get("USERPROFILE", ""), ".bun", "bin"),
            os.path.join(_env.get("LOCALAPPDATA", ""), "bun"),
            r"C:\Users\guwenjin\.bun\bin",
        ]
        current_path = _env.get("PATH", "")
        for d in bun_dirs:
            if os.path.isdir(d) and d not in current_path:
                _env["PATH"] = d + os.pathsep + current_path
                current_path = _env["PATH"]

        return _env

    def _get_cmd(self, extra_args: list = None) -> list:
        """
        构建启动命令
        直接用 bun 调用 cli.tsx，绕过 claude-code-tudou 的 shell=true 包装
        （Windows 下 shell=true 会导致参数被 cmd.exe 重新解析，多词参数被拆散）
        """
        entrypoint = os.path.join(self.t8_dir, "src", "entrypoints", "cli.tsx")
        env_file = os.path.join(self.t8_dir, ".env")
        cmd = [self.bun_exe, f"--env-file={env_file}", entrypoint]
        if extra_args:
            cmd.extend(extra_args)
        return cmd

    def run_task(self, task: str, timeout: int = 300) -> dict:
        """
        运行任务，实时打印所有输出到控制台，并返回最终结果
        使用 --print 模式（非 json），可以看到 T8 的完整交互过程
        """
        import json as _json

        _env = self._build_env()
        # 用 --print 而非 -p --output-format json，这样能看到完整的交互过程
        cmd = self._get_cmd(["-p", task])

        self.last_output = ""

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=self.t8_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 合并 stderr 到 stdout
                env=_env,
                shell=False,
            )

            # 实时读取并打印所有输出
            while True:
                chunk = proc.stdout.read(4096)
                if not chunk:
                    break
                text = chunk.decode('utf-8', errors='replace')
                self.last_output += text
                # 实时打印到控制台，让用户看到所有进度
                _safe_print(text)

            proc.wait(timeout=10)
            returncode = proc.returncode

            # 尝试从输出末尾提取 JSON 结果
            output_text = self.last_output
            try:
                # 找最后一个 JSON 对象
                json_match = re.search(r'\{[^{}]*"result"[^{}]*\}', self.last_output, re.DOTALL)
                if json_match:
                    json_resp = _json.loads(json_match.group())
                    if isinstance(json_resp, dict) and "result" in json_resp:
                        output_text = json_resp["result"]
            except Exception:
                pass

            return {
                "success": returncode == 0,
                "output": output_text,
                "error": "",
                "returncode": returncode,
            }
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except Exception:
                pass
            _safe_print(f"\n[TIMEOUT] 任务超过 {timeout}s，已终止\n")
            return {
                "success": False,
                "output": self.last_output,
                "error": f"Task timeout ({timeout}s)",
                "returncode": -1,
            }
        except Exception as e:
            return {
                "success": False,
                "output": self.last_output,
                "error": str(e),
                "returncode": -1,
            }

    def run_stream(self, task: str, callback: Callable[[str], None], timeout: int = 300) -> bool:
        """流式运行任务（实时输出回调）"""
        _env = self._build_env()
        cmd = self._get_cmd(["--print", task])

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=self.t8_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=_env,
                shell=False,
            )
            while True:
                chunk = proc.stdout.read(4096)
                if not chunk:
                    break
                text = chunk.decode('utf-8', errors='replace')
                self.last_output += text
                callback(text)

            proc.wait(timeout=timeout)
            return proc.returncode == 0

        except subprocess.TimeoutExpired:
            proc.kill()
            callback(f"\n[TIMEOUT] Task exceeded {timeout}s\n")
            return False
        except Exception as e:
            callback(f"\n[ERROR] {e}\n")
            return False

    def start_tui(self) -> Optional[subprocess.Popen]:
        """
        启动交互式 TUI（长期运行）
        返回 Popen 对象用于后续控制
        """
        _env = self._build_env()
        cmd = self._get_cmd()

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=self.t8_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=_env,
                shell=False,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
            )
            return proc
        except Exception as e:
            print(f"[Bridge] Start TUI failed: {e}")
            return None


# ============================================================
# HTTP API 服务
# ============================================================

try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.responses import PlainTextResponse
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


if HAS_FASTAPI:
    app = FastAPI(title="Claude Code Bridge API", version="3.0.0 (T8)")

    # 全局状态
    cli_bridge: Optional[ClawCLIBridge] = None
    ws_clients: list[WebSocket] = []


    @app.on_event("startup")
    async def startup():
        global cli_bridge
        t8_dir = os.environ.get(
            "T8_DIR",
            r"G:\work_software\claw\.workbuddy\AI工具\claude-code-t8-main"
        )

        if os.path.isdir(t8_dir):
            cli_bridge = ClawCLIBridge(t8_dir=t8_dir)
            print(f"[Bridge] T8 initialized: {t8_dir}")
            print(f"[Bridge] API: {cli_bridge.config.get('OPENAI_BASE_URL')}")
            print(f"[Bridge] Model: {cli_bridge.config.get('OPENAI_MODEL')}")
        else:
            print(f"[Bridge] T8 not found: {t8_dir}")


    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "mode": "cli" if cli_bridge else "tui",
            "timestamp": datetime.now().isoformat()
        }


    @app.post("/task")
    async def run_task(data: dict):
        """
        运行任务
        POST /task
        Body: {"task": "写一个Arduino舵机代码", "timeout": 300}
        """
        if not cli_bridge:
            raise HTTPException(status_code=500, detail="T8 Bridge not initialized")

        task = data.get("task", "")
        timeout = data.get("timeout", 300)

        if not task:
            raise HTTPException(status_code=400, detail="Task is required")

        _safe_print(f"\n[API] Task: {task[:80]}...")
        result = cli_bridge.run_task(task, timeout)

        # 打印 AI 回复摘要（用 safe_print 避免 GBK 编码崩溃）
        output = result.get("output", "").strip()
        if output:
            preview = output[:200] + ("..." if len(output) > 200 else "")
            _safe_print(f"[API] Reply: {preview}")
        if result.get("error"):
            _safe_print(f"[API] Error: {result['error'][:200]}")

        return result


    @app.post("/task-stream")
    async def run_task_stream(data: dict):
        """流式运行任务"""
        if not cli_bridge:
            raise HTTPException(status_code=500, detail="T8 Bridge not initialized")

        task = data.get("task", "")
        timeout = data.get("timeout", 300)

        if not task:
            raise HTTPException(status_code=400, detail="Task is required")

        output_lines = []
        cli_bridge.run_stream(task, lambda line: output_lines.append(line), timeout)

        return {
            "success": True,
            "output": "\n".join(output_lines),
            "lines": len(output_lines)
        }


    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket 实时流"""
        await websocket.accept()
        ws_clients.append(websocket)

        try:
            while True:
                data = await websocket.receive_text()
                try:
                    cmd = json.loads(data)
                    task = cmd.get("task", "")
                    if cli_bridge and task:
                        def send_line(line: str):
                            asyncio.create_task(websocket.send_text(line))
                        cli_bridge.run_stream(task, send_line, cmd.get("timeout", 300))
                except json.JSONDecodeError:
                    await websocket.send_text(f"[ERROR] Invalid JSON\n")
        except WebSocketDisconnect:
            ws_clients.remove(websocket)


# ============================================================
# 主程序
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Claude Code T8 Bridge (OpenAI Compatible)")
    parser.add_argument("--port", type=int, default=8767, help="HTTP API port")
    parser.add_argument("--task", type=str, default=None, help="Run task directly and exit")
    parser.add_argument("--timeout", type=int, default=300, help="Task timeout (seconds)")
    parser.add_argument("--test", action="store_true", help="Test mode (run T8 with --help)")
    parser.add_argument("--tui", action="store_true", help="Launch interactive TUI")
    parser.add_argument("--t8-dir", type=str, default=None, help="T8 project directory")
    parser.add_argument("--api-key", type=str, default=None, help="OpenAI API key")
    parser.add_argument("--model", type=str, default=None, help="Model name (e.g. claude-opus-4-6)")
    parser.add_argument("--base-url", type=str, default=None, help="API base URL")
    args = parser.parse_args()

    # 打印横幅
    print("=" * 60)
    print("  Claude Code Bridge - Middleware v3.0 (T8 / OpenAI API)")
    print("=" * 60)

    # 确定 T8 目录
    t8_dir = args.t8_dir or os.environ.get(
        "T8_DIR",
        r"G:\work_software\claw\.workbuddy\AI工具\claude-code-t8-main"
    )

    print(f"\n[Config]")
    print(f"  T8 Dir:    {t8_dir}")
    print(f"  Exists:    {os.path.isdir(t8_dir)}")

    if not os.path.isdir(t8_dir):
        print("\n[ERROR] T8 directory not found!")
        print(f"  Please check: {t8_dir}")
        sys.exit(1)

    # 显示 API 配置
    base_url = args.base_url or os.environ.get("OPENAI_BASE_URL", T8_DEFAULT_CONFIG["OPENAI_BASE_URL"])
    model = args.model or os.environ.get("OPENAI_MODEL", T8_DEFAULT_CONFIG["OPENAI_MODEL"])
    print(f"  API URL:   {base_url}")
    print(f"  Model:     {model}")

    # 初始化 Bridge
    bridge = ClawCLIBridge(
        t8_dir=t8_dir,
        api_key=args.api_key,
        model=args.model,
        base_url=args.base_url,
    )

    # 覆盖 API key
    if args.api_key:
        bridge.config["OPENAI_API_KEY"] = args.api_key
    if args.model:
        bridge.config["OPENAI_MODEL"] = args.model
    if args.base_url:
        bridge.config["OPENAI_BASE_URL"] = args.base_url

    print(f"  Node:      {bridge.node_exe}")
    print(f"  Bun:       {bridge.bun_exe}")
    print(f"  API Key:   {'[OK]' if bridge.config.get('OPENAI_API_KEY') else '[MISSING]'}")

    if args.task:
        # 直接运行任务
        print(f"\n[Task] {args.task[:80]}...")
        print("-" * 40)
        result = bridge.run_task(args.task, args.timeout)
        _safe_print(result["output"])
        if result["error"]:
            print(f"[Error] {result['error']}")
        sys.exit(0 if result["success"] else 1)

    if args.test:
        # 测试模式
        print(f"\n[Test] Running: node ./bin/claude-code-tudou --help")
        result = bridge.run_task("--help", 30)
        print(result["output"] if result["success"] else f"[Error] {result['error']}")
        sys.exit(0 if result["success"] else 1)

    if args.tui:
        # 启动交互式 TUI
        print(f"\n[TUI] Launching interactive TUI...")
        proc = bridge.start_tui()
        if proc:
            print(f"[TUI] Started: PID={proc.pid}")
            # 读取并打印初始输出
            try:
                while True:
                    chunk = proc.stdout.read(4096)
                    if not chunk:
                        break
                    print(chunk, end='', flush=True)
            except KeyboardInterrupt:
                print("\n[Ctrl+C] Stopping TUI...")
                proc.terminate()
        sys.exit(0)

    # 启动 HTTP API 服务
    if HAS_FASTAPI:
        print(f"\n[Server] HTTP API on port {args.port}")
        print(f"  POST http://localhost:{args.port}/task")
        print(f"  POST http://localhost:{args.port}/task-stream")
        print(f"  WS   ws://localhost:{args.port}/ws")
        print(f"\n  Example:")
        print(f'  curl -X POST http://localhost:{args.port}/task \\')
        print(f'    -H "Content-Type: application/json" \\')
        print(f'    -d \'{{"task": "write hello world", "timeout": 300}}\'')
        print()
        uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info")
    else:
        print("\n[ERROR] FastAPI not installed.")
        print("  pip install fastapi uvicorn")
        sys.exit(1)


if __name__ == "__main__":
    main()

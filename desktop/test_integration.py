"""ParaJudge 桌面端集成测试

测试内容：
1. ServerRunner 能否成功启动 uvicorn 子进程
2. 后端 API 在子进程模式下是否正常响应
3. 静态资源（前端、JS、桥接文件）能否被服务
4. 优雅停止子进程
"""
import logging
import socket
import time
import urllib.request
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

from desktop.config import AppConfig
from desktop.server_runner import ServerRunner


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def http_get(url: str, timeout: float = 5.0):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        body = r.read()
        try:
            return r.status, json.loads(body), body
        except Exception:
            return r.status, None, body


def main() -> int:
    port = find_free_port()
    print(f'\n=== 集成测试：使用端口 {port} ===\n')

    server = ServerRunner(host='127.0.0.1', port=port, log_level='warning')

    # 1. 启动
    print('[1/5] 启动后端子进程...')
    t0 = time.time()
    if not server.start():
        print('  [FAIL] fork 失败')
        return 1
    print(f'  PID = {server.pid}')

    # 2. 等待就绪
    print('[2/5] 等待后端就绪...')
    if not server.wait_ready(timeout=20):
        print('  [FAIL] 等待就绪超时')
        server.stop()
        return 2
    print(f'  耗时: {time.time() - t0:.2f}s')

    base = f'http://127.0.0.1:{port}'

    # 3. 验证 API
    print('[3/5] 验证 API...')
    checks = [
        ('/api/health', 'status'),
        ('/api/version', 'name'),
        ('/api/judges', 'total'),
        ('/api/llm/providers', 'providers'),
        ('/api/examples/questions', 'total'),
    ]
    for path, expect_key in checks:
        try:
            status, data, _ = http_get(base + path)
            assert status == 200, f'HTTP {status}'
            assert expect_key in data, f'字段 {expect_key} 缺失'
            val = data[expect_key]
            print(f'  ✓ {path:40s} {expect_key}={val}')
        except Exception as e:
            print(f'  ✗ {path}: {e}')
            server.stop()
            return 3

    # 4. 验证静态资源
    print('[4/5] 验证前端静态资源...')
    static_checks = [
        '/ui/index.html',
        '/ui/pages/debate-room.html',
        '/ui/pages/verdict-report.html',
        '/ui/js/api.js',
        '/ui/js/desktop-bridge.js',
        '/ui/css/style.css',
    ]
    for path in static_checks:
        try:
            status, _, body = http_get(base + path)
            assert status == 200, f'HTTP {status}'
            print(f'  ✓ {path:40s} {len(body):6d} bytes')
        except Exception as e:
            print(f'  ✗ {path}: {e}')
            server.stop()
            return 4

    # 5. 验证一次完整辩论
    print('[5/5] 端到端一次完整辩论（mock LLM）...')
    try:
        req = urllib.request.Request(
            base + '/api/parajudge/run',
            data=json.dumps({
                'problem': '集成测试问题',
                'rounds': 1,
                'max_evidence': 3,
                'llm': {'provider': 'mock', 'model': 'mock-model'},
            }).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            result = json.loads(r.read())
        assert 'judgment' in result
        assert 'transcript' in result
        assert 'evidence_brief' in result
        j = result['judgment']
        print(f'  ✓ run_id = {result["run_id"]}')
        print(f'  ✓ winner = {j["winner"]}')
        print(f'  ✓ pro={j["pro_final_score"]}, con={j["con_final_score"]}')
        print(f'  ✓ judges = {len(j["judge_scores"])}')
    except Exception as e:
        print(f'  ✗ 端到端测试失败: {e}')
        server.stop()
        return 5

    # 优雅停止
    print('\n[停止] 优雅停止后端...')
    server.stop()
    print('  ✓ 已停止')

    print('\n=== ✅ 所有集成测试通过 ===\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

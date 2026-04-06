import subprocess, time, os
env = dict(os.environ)
env['OPENAI_API_KEY'] = 'sk-7v3vT0WqpIB9vRvoUQ2LlwwqHFt5NIO2tCHQfMmsxEZMWeJO'
env['T8_DIR'] = r'G:\work_software\claw\.workbuddy\AI工具\claude-code-t8-main'
p = subprocess.Popen(
    ['python', '-m', 'uvicorn', 'claw_tui_bridge:app', '--host', '127.0.0.1', '--port', '8767'],
    cwd=r'G:\work_software\claw\.workbuddy\脚本',
    env=env,
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)
print('Service PID:', p.pid)
time.sleep(3)
# Read output
try:
    output = p.stdout.read1(4096)
    print('Output:', output.decode('utf-8', errors='replace')[:500])
except:
    pass

"""
音频合并脚本 - 使用 ffmpeg 合并 TTS 输出的分段音频
用法：python tts_concat.py
输入：comfyui_api/tts_output/ 目录下所有 story_v3_*.flac 或 story_*.flac
输出：story_full.flac（合并后完整音频）
依赖：ffmpeg 已加入 PATH
"""
import subprocess, os, sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(SCRIPT_DIR, '..', 'comfyui_api', 'tts_output')
OUT = 'story_full.flac'
LIST = os.path.join(DIR, 'concat_list.txt')

# 获取所有 story_v3_*.flac / story_*.flac 文件并排序
files = sorted([
    f for f in os.listdir(DIR)
    if (f.startswith('story_v3_') or f.startswith('story_'))
    and f.endswith('.flac')
    and 'full' not in f
])
print(f'找到 {len(files)} 个文件: {files[:3]}...' if len(files) > 3 else f'找到 {len(files)} 个文件: {files}')

if not files:
    print('没有找到可合并的音频文件')
    sys.exit(1)

# 创建文件列表
with open(LIST, 'w', encoding='utf-8') as f:
    for fname in files:
        f.write(f"file '{fname}'\n")
print(f'文件列表已写: {LIST}')

# ffmpeg concat
cmd = [
    'ffmpeg', '-y',
    '-f', 'concat', '-safe', '0',
    '-i', LIST,
    '-acodec', 'pcm_s16le',
    os.path.join(DIR, OUT)
]
print('Running ffmpeg...')
r = subprocess.run(cmd, capture_output=True, text=True, cwd=DIR)
if r.returncode == 0:
    size = os.path.getsize(os.path.join(DIR, OUT))
    print(f'[OK] 合并成功! 文件: {os.path.join(DIR, OUT)}')
    print(f'大小: {size / 1024 / 1024:.1f} MB')
else:
    print(f'[FAIL] 失败: {r.stderr[-800:]}')

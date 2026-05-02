"""
TTS 剧本生成器 - Qwen3-TTS VoiceDesign 版
用法：python tts_voice_design.py
输入：修改同目录下的 story_text_input.txt，写入剧本正文
输出：comfyui_api/tts_output/story_v3_*.flac + story_v3_full.wav（自动合并）
"""
import json, sys, re, urllib.request, time, subprocess, os, shutil, tempfile, winsound
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SERVER = "http://127.0.0.1:8188"

VOICE_INSTRUCT = {
    "narrator": "沉稳厚重的男声，语速适中，叙事感强，适合读旁白和场景描写，中年男性音色",
    "yurisu":   "温柔磁性的男中音，语速偏慢，语气平和温暖，带有坚定感，青年男性音色",
    "lasput":   "清冷高傲的女声，语调平稳偏冷，节奏利落，略带冷淡距离感，青年女性音色",
    "aiya":     "俏皮狡黠的年轻女声，语速略快，语气灵动活泼，带点调侃和神秘感，少女音色",
}

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BASE_WORKFLOW_PATH = os.path.join(SCRIPT_DIR, "Qwen3-TD-TTS_VoiceDesign.json")
OUTPUT_DIR         = os.path.join(SCRIPT_DIR, "..", "comfyui_api", "tts_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── API ──────────────────────────────────────────────────────────────────────

def api_get(path):
    url = f"{SERVER}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())

def api_post(path, data):
    url = f"{SERVER}{path}"
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

def wait_for_done(prompt_id, timeout=600):
    start = time.time()
    last_dot = -1
    while time.time() - start < timeout:
        try:
            hist = api_get(f"/history/{prompt_id}")
            if prompt_id in hist:
                outputs = hist[prompt_id].get("outputs", {})
                if outputs:
                    print(f"[OK] 完成 ({int(time.time()-start)}s)")
                    return outputs
                if hist[prompt_id].get("status", {}).get("completed"):
                    print(f"[OK] 完成-缓存 ({int(time.time()-start)}s)")
                    return outputs or {}
        except Exception:
            pass
        sec = int(time.time() - start)
        if sec != last_dot and sec % 5 == 0:
            print(f"\r  等待中... {sec}s", end="", flush=True)
            last_dot = sec
        time.sleep(2)
    print(f"[WARN] 超时 {timeout}s")
    return None

def clear_queue():
    for _ in range(10):
        try:
            req = urllib.request.Request(f"{SERVER}/interrupt", method="POST")
            urllib.request.urlopen(req, timeout=3)
        except:
            pass
        time.sleep(0.3)

def check_queue():
    with urllib.request.urlopen(f"{SERVER}/queue", timeout=10) as r:
        q = json.loads(r.read().decode())
    return len(q.get("queue_running", [])), len(q.get("queue_pending", []))

# ── 工作流构建 ────────────────────────────────────────────────────────────────

def load_workflow():
    with open(BASE_WORKFLOW_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_cleanup_nodes():
    with open(CLEANUP_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def build_workflow(text, role, seg_idx):
    wf = load_workflow()
    cleanup = load_cleanup_nodes()
    instruct = VOICE_INSTRUCT.get(role, VOICE_INSTRUCT["narrator"])

    max_id = 0
    for nid in wf:
        try:
            max_id = max(max_id, int(nid))
        except:
            pass

    for nid, node in wf.items():
        if node.get("class_type") == "TDQwen3TTSVoiceDesign":
            node["inputs"]["text"]    = text
            node["inputs"]["instruct"] = instruct
        # 修复 model_path 前缀
        if node.get("class_type") == "TDQwen3TTSModelLoader":
            mp = node["inputs"].get("model_path", "")
            if mp and not mp.startswith("Qwen/"):
                node["inputs"]["model_path"] = "Qwen/" + mp
        # 移除不需要的 LoadAudio 引用
        if node.get("class_type") == "LoadAudio":
            node["inputs"]["audio"] = ""

    # 追加清理节点
    for cnid, cnode in cleanup.items():
        new_id = str(max_id + int(cnid) + 10)
        wf[new_id] = json.loads(json.dumps(cnode))

    return wf

def submit_workflow(workflow):
    result = api_post("/prompt", {"prompt": workflow})
    pid = result.get("prompt_id")
    if not pid:
        print("  [ERROR] No prompt_id")
        return None
    print(f"  PID: {pid[:8]}...", end=" ", flush=True)
    return pid

# ── 文件监控下载（VoiceDesign 专用）───────────────────────────────────────────

def get_comfy_temp_files():
    """获取 ComfyUI temp 目录中的 wav 文件列表"""
    files = []
    # 查 ComfyUI 输出目录
    for subfolder in ["temp", "output"]:
        try:
            url = f"{SERVER}/api/files?subfolder={subfolder}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        name = item.get("name", "")
                        if name.endswith(".wav"):
                            files.append((subfolder, name))
        except Exception:
            pass
    return files

def download_vd_audio(outputs, seg_idx):
    """
    VoiceDesign 版下载：音频在 PreviewAudio 节点，格式 .flac
    输出结构: {"10": {"audio": [{"filename": "...flac", "type": "temp", "subfolder": ""}]}}
    """
    for nid, no in outputs.items():
        if not isinstance(no, dict):
            continue
        al = no.get("audio")
        if isinstance(al, list) and al:
            info  = al[0]
            fname = info.get("filename", "")
            atype = info.get("type", "temp")
            subfolder = info.get("subfolder", "")
            dl_url = f"{SERVER}/view?filename={fname}&type={atype}"
            if subfolder:
                dl_url += f"&subfolder={subfolder}"
            ext = fname.rsplit(".", 1)[-1] if "." in fname else "flac"
            # 保存为 .wav 扩展名方便播放
            tmp = os.path.join(tempfile.gettempdir(), f"vd_{seg_idx:03d}.flac")
            try:
                with urllib.request.urlopen(dl_url, timeout=60) as r:
                    with open(tmp, "wb") as f:
                        shutil.copyfileobj(r, f)
                print(f"    下载成功: {fname} ({os.path.getsize(tmp)//1024} KB)")
                return tmp
            except Exception as e:
                print(f"    下载失败: {e}")
    return None

# ── 正文解析 ──────────────────────────────────────────────────────────────────

def parse_story(text):
    """
    解析正文，识别角色台词与旁白。
    支持格式：
      - 尤里西斯：台词  / 尤里西斯说：台词
      - 拉丝普汀：台词  / 拉丝普汀说：台词
      - 艾娅：台词      / 艾娅说：台词
      - 艾娅的声音飘出来：台词
      - 艾娅从书页里飘出来：台词
      - 艾娅的声音从书页里飘出来：台词
    其余 → 旁白
    """
    ROLE_MAP = {
        "尤里西斯": "yurisu",
        "拉丝普汀": "lasput",
        "艾娅":     "aiya",
    }

    segments = []
    lines = text.split("\n")
    narrator_buf = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        matched_role   = None
        matched_text   = None

        # ── 艾娅特殊格式（多种变体）──────────────────────────────
        aiya_patterns = [
            (re.compile(r'^艾娅(?:的)?(?:说|低语说|轻声道|嘀咕说)[：:]\s*(.+)'), "aiya"),
            (re.compile(r'^艾娅(?:的)?声音(?:从书页里)?飘出来[：:]\s*(.+)'), "aiya"),
            (re.compile(r'^艾娅(?:从书页里)?飘出来[：:]\s*(.+)'), "aiya"),
            (re.compile(r'^艾娅(?:的)?声音[：:]\s*(.+)'), "aiya"),
            (re.compile(r'^艾娅从(?:书页里|书中)飘(?:出|来)[：:]\s*(.+)'), "aiya"),
            # 艾娅的声音从书页里飘出来：台词（冒号在中间）
            (re.compile(r'^艾娅(?:的)?声音(?:从书页里)?飘出来[：:]\s*(.+)'), "aiya"),
        ]
        for pat, role in aiya_patterns:
            m = pat.match(stripped)
            if m:
                matched_role = role
                matched_text = m.group(1).strip()
                break

        # ── 标准角色格式 ─────────────────────────────────────
        if not matched_role:
            char_patterns = [
                re.compile(rf'^({k})(?:说|低语说|轻声道)?[：:]\s*(.+)')
                for k in ROLE_MAP.keys()
            ]
            for pat in char_patterns:
                m = pat.match(stripped)
                if m:
                    matched_role = ROLE_MAP[m.group(1)]
                    matched_text = m.group(2).strip()
                    break

        # ── 收尾 buffer ───────────────────────────────────────
        if matched_role and matched_text:
            if narrator_buf.strip():
                segments.append(("narrator", narrator_buf.strip()))
                narrator_buf = ""
            if matched_text:
                segments.append((matched_role, matched_text))
        else:
            narrator_buf += " " + stripped

    if narrator_buf.strip():
        segments.append(("narrator", narrator_buf.strip()))

    return segments

# ── 合并+播放 ─────────────────────────────────────────────────────────────────

def concat_wav(audio_files, output_dir, session_name):
    if not audio_files:
        return None
    list_file = os.path.join(output_dir, "concat_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for af in audio_files:
            f.write(f"file '{os.path.basename(af)}'\n")
    out_wav = os.path.join(output_dir, f"{session_name}_full.wav")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-acodec", "pcm_s16le", out_wav]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=output_dir)
    if r.returncode == 0:
        print(f"[OK] 合并完成: {os.path.getsize(out_wav)/1024:.0f} KB")
        return out_wav
    else:
        print(f"[ERROR] 合并失败: {r.stderr[-300:]}")
        return None

def play_wav(path):
    try:
        winsound.PlaySound(path, winsound.SND_FILENAME)
    except Exception as e:
        print(f"播放失败: {e}")

# ── 主程序 ─────────────────────────────────────────────────────────────────────

def main(text_path, session_name="story_v3"):
    with open(text_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print("文本为空！")
        sys.exit(1)

    # 清队列
    print("检查队列...")
    running, pending = check_queue()
    if running or pending:
        print(f"队列非空 (running={running}, pending={pending})，正在清空...")
        clear_queue()
        time.sleep(3)

    # 解析
    print("解析剧本...")
    segments = parse_story(text)
    print(f"共 {len(segments)} 个片段:")
    role_names = {"narrator": "旁白", "yurisu": "尤里", "lasput": "拉丝", "aiya": "艾娅"}
    for i, (role, seg) in enumerate(segments):
        tag = role_names.get(role, role)
        preview = seg[:40] + "..." if len(seg) > 40 else seg
        print(f"  [{i+1:02d}] {tag:3s}: {preview}")

    audio_files = []
    failed = []

    # 先清空 temp 中的旧 vd_ 文件
    tmpdir = tempfile.gettempdir()
    for f in os.listdir(tmpdir):
        if f.startswith('vd_') and f.endswith('.flac'):
            try:
                os.remove(os.path.join(tmpdir, f))
            except:
                pass

    for i, (role, seg_text) in enumerate(segments):
        if role == "narrator" and len(seg_text) < 15:
            print(f"[{i+1}/{len(segments)}] [SKIP] 跳过短旁白 ({len(seg_text)}字)")
            continue

        tag = role_names.get(role, role)
        print(f"\n[{i+1}/{len(segments)}] {tag}: {seg_text[:40]}{'...' if len(seg_text)>40 else ''}")

        workflow = build_workflow(seg_text, role, i)
        pid = submit_workflow(workflow)
        if not pid:
            failed.append((i, role, seg_text))
            continue

        # 等待完成
        result = wait_for_done(pid)
        if result is not None:
            # VoiceDesign：用 outputs 直接下载
            wav_path = download_vd_audio(result, i)
            if wav_path and os.path.exists(wav_path):
                out_path = os.path.join(OUTPUT_DIR, f"{session_name}_{i:03d}_{role}.flac")
                shutil.copy(wav_path, out_path)
                audio_files.append(out_path)
                print(f"  -> {os.path.basename(out_path)} ({os.path.getsize(out_path)//1024} KB)")
            else:
                print(f"  [WARN] 未能获取音频文件")
                failed.append((i, role, seg_text))
        else:
            failed.append((i, role, seg_text))

        time.sleep(1)

    print(f"\n{'='*50}")
    print(f"生成完成！成功: {len(audio_files)}, 失败: {len(failed)}")

    if failed:
        print("\n失败片段:")
        for idx, role, seg in failed:
            print(f"  [{idx+1}] {role}: {seg[:60]}...")

    if audio_files:
        full_wav = concat_wav(audio_files, OUTPUT_DIR, session_name)
        if full_wav:
            print(f"\n>> 播放完整音频: {full_wav}")
            play_wav(full_wav)

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    text_path = os.path.join(script_dir, "story_text_input.txt")
    session = "story_v3"
    if len(sys.argv) > 1:
        text_path = sys.argv[1]
    if len(sys.argv) > 2:
        session = sys.argv[2]
    main(text_path, session)

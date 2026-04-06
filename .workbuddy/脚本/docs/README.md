# 脚本说明

> 所有脚本基于 `G:\work_software\claw\.workbuddy\` 工作目录

---

## TTS 有声小说 🎙️

有两套不同的 TTS 实现，根据需求选用：

---

### 方案 A：VoiceDesign（现行主力）— 多人对话有声小说

| 脚本 | 作用 | 用法 |
|------|------|------|
| `tts_voice_design.py` | TTS 分段生成 | `python tts_voice_design.py` |
| `tts_concat.py` | 音频合并（ffmpeg）| `python tts_concat.py` |

**工作流：** 修改 `story_text_input.txt` → `python tts_voice_design.py` → `python tts_concat.py`

| 文件 | 说明 |
|------|------|
| `story_text_input.txt` | 剧本正文模板 |
| `Qwen3-TD-TTS_VoiceDesign.json` | ComfyUI TTS Workflow |
| `tts_output/` | 输出目录 |

**角色标签格式：**
```
[旁白]xxx
[尤里西斯]xxx
[拉丝普汀]xxx
[艾娅]xxx
```

**输出目录结构：**
```
tts_output/
  story_v3_000_narrator.flac  ← 旁白
  story_v3_001_yurisu.flac    ← 尤里西斯
  story_v3_005_lasput.flac    ← 拉丝普汀
  story_v3_012_aiya.flac      ← 艾娅
  story_v3_full.wav           ← 合并后完整音频
  concat_list.txt             ← ffmpeg 合并列表
```

---

### 方案 B：声纹克隆（TDQwen3TTSVoiceClone）— 克隆真实人类语音

**Workflow：** `Qwen3-TD-TTS_旧版.json`

| 节点 | 说明 |
|------|------|
| `TDQwen3TTSModelLoader` | 加载模型 `Qwen/Qwen3-TTS-12Hz-1.7B-Base` |
| `TDQwen3TTSVoiceClone` | 声纹克隆生成，模式：`x_vector_only_mode` |
| `PreviewAudio` | 预览/输出音频 |

**x_vector_only_mode 参数：**
- **`true`**：仅用声纹模式，只参考音频中的声纹来生成 text 内容
- **`false`**：语气融合模式，参考 ref_text 的语气 + 参考音频一起生成 text

**使用方法（ComfyUI 内手动操作）：**
1. 加载 `Qwen3-TD-TTS_旧版.json`
2. 把 `LoadAudio` 节点指向参考音频
3. 在 `TDQwen3TTSVoiceClone` 节点填入文本和 ref_text
4. 设置 `x_vector_only_mode` 为 `true`（纯声纹）或 `false`（语气融合）
5. 运行，输出 WAV 音频

---

## Claude Code T8 API 网桥 🌐

| 脚本 | 作用 | 用法 |
|------|------|------|
| `claw_tui_bridge.py` | HTTP → Claude Code T8 桥接 | 启动后 `POST http://localhost:8767/task` |
| `start_server.py` | 一键启动（带环境检测） | `python start_server.py` |

**T8 配置（已内置）：**
- 端点：`https://ai.t8star.cn/v1`
- 模型：`claude-opus-4-6`
- API Key：通过 `--api-key` 参数传入

**HTTP 接口：**
```
POST http://localhost:8767/task
Body: {"task": "你的任务", "timeout": 300}
```

---

## ComfyUI Workflow 文件（位于 `../comfyui_api/`）

| 文件 | 用途 |
|------|------|
| `bbb_QwenRapid.json` | 生图 workflow — BBB |
| `fali_QwenRapid.json` | 生图 workflow — 法丽 |
| `j1_sfw.json` | 生图 workflow — J1 |
| `nunchaku_Qwen_多视图极速版.json` | 多视图极速版 |
| `QwenRapid_AIO_写真工作流.json` | 写真工作流 |
| `WAN22GGUF_终极加速.json` | WAN2.2 GGUF 加速 |

**ComfyUI 地址：** `http://127.0.0.1:8188`
**模型：** `Qwen-Rapid-AIO-NSFW-v18.safetensors`

---

## 存储布局

```
G:\work_software\claw\.workbuddy\
├── 脚本/              ← 主力脚本（固化在此）
│   ├── tts_voice_design.py
│   ├── tts_concat.py
│   ├── claw_tui_bridge.py
│   ├── start_server.py
│   ├── story_text_input.txt
│   ├── Qwen3-TD-TTS_VoiceDesign.json  ← 方案A：多人对话版
│   ├── Qwen3-TD-TTS_旧版.json         ← 方案B：声纹克隆版
│   └── README.md
├── comfyui_api/       ← ComfyUI workflow + TTS输出
│   ├── bbb_QwenRapid.json
│   ├── fali_QwenRapid.json
│   ├── j1_sfw.json
│   ├── WAN22GGUF_终极加速.json
│   ├── QwenRapid_AIO_写真工作流.json
│   ├── nunchaku_Qwen_多视图极速版.json
│   └── tts_output/       ← TTS 生成物
├── AI酒馆/            ← SillyTavern 角色设定
│   └── fali/
│       └── fali.png      ← 法丽立绘图
├── memory/            ← 猫猫工作记忆
└── ...其他资料目录
```

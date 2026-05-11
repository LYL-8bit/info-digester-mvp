# 人工代处理服务 SOP

## 1. 接单

用户需要提供：

- YouTube 链接。
- 想要的用途：学习笔记 / 技术步骤 / 选题参考，默认学习笔记。
- 是否需要 Markdown 文件，默认需要。

接单前确认：

- 视频主题属于 AI、编程、技术教程、独立开发或效率工具。
- 首单体验只处理 30 分钟内视频。
- 标准单次只处理 90 分钟内视频。
- 暂不承诺处理无字幕视频。

## 2. 提取字幕

优先使用已有 `.vtt` 字幕文件。

### 方式 A：本地操作台

第一次使用先安装依赖：

```powershell
pip install -r .\service_mvp\requirements.txt
```

启动操作台：

```powershell
streamlit run .\service_mvp\app.py
```

浏览器会打开本地页面，通常是：

```text
http://localhost:8501
```

在操作台里输入：

- YouTube 链接
- 案例编号，例如 `case_003`
- 案例标题

然后按页面顺序完成：创建案例目录、下载字幕、清洗字幕、复制 Prompt。

### 方式 B：命令行

如果需要从 YouTube 下载字幕，cookie 路径由项目根目录的 `.env` 管理：

```text
YTDLP_COOKIE_FILE=D:/MVP/service_mvp/cookies/cookies.txt
```

检查 `.env` 是否能读到 cookie 文件：

```powershell
python .\service_mvp\scripts\download_subtitles.py --check-env
```

下载英文自动字幕：

```powershell
python .\service_mvp\scripts\download_subtitles.py "YouTube链接" -o ".\service_mvp\cases\case_001"
```

如果 cookie 文件缺失，脚本会提示并继续尝试下载公开视频字幕。脚本只显示 cookie 文件路径是否存在，不显示 cookie 内容。

清洗命令：

```powershell
python .\service_mvp\scripts\clean_vtt.py ".\service_mvp\cases\case_001\视频字幕.en.vtt" -o ".\service_mvp\cases\case_001\transcript.txt"
```

如果系统 `python` 指向 Windows Store 占位程序，可使用 Codex 内置 Python：

```powershell
C:\Users\Liang\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe .\service_mvp\scripts\clean_vtt.py ".\视频字幕.en.vtt" -o ".\service_mvp\cases\case_001\transcript.txt"
```

用 `yt-dlp` 下载字幕时，先只下载字幕，不做音频转写。

## 3. 生成笔记

把清洗后的字幕复制到 AI 工具中，使用 `02_固定Prompt.md`。

生成后必须人工检查：

- 是否有明显幻觉。
- 技术命令是否和原文一致。
- 中文是否像学习笔记，而不是机器翻译。
- 是否能直接保存到 Obsidian。

## 4. 质量评分

低于 8 分不发布、不交付。

评分标准：

| 项目 | 分值 |
| --- | ---: |
| 能不能 30 秒看懂视频价值 | 2 |
| 核心观点是否清楚 | 2 |
| 技术步骤是否可执行 | 2 |
| 术语解释是否有用 | 1 |
| Markdown 是否干净可收藏 | 2 |
| 是否有行动清单 | 1 |

## 5. 交付

交付格式：

- 微信文本：适合快速试用。
- Markdown 文件：适合付费用户和程序员。

交付话术：

> 我整理好了，这版是按“可直接收藏到 Obsidian”的结构做的。你可以先看“一句话总结”和“是否值得看”，如果觉得有用，我也可以继续帮你处理下一条视频。

## 6. 复购追问

交付后 12-24 小时发：

> 这份笔记对你筛选视频/学习有没有帮助？如果你平时有固定关注的英文频道，我可以按同样格式继续帮你整理，5 条体验包是 49 元。

# Info Digester MVP

英文 YouTube / 技术视频 → 中文 Markdown 学习笔记的服务型 MVP。

当前定位不是先做复杂 SaaS，而是先验证：用户是否愿意为“高质量中文学习笔记”付费。

## 当前能力

- 下载 YouTube 字幕：`yt-dlp`
- 清洗 `.vtt` 字幕为 `transcript.txt`
- 根据固定 Prompt 生成中文 Markdown 笔记
- Streamlit 本地操作台
- 小红书推广素材与接单 SOP

## 快速启动

### 1. 创建虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r service_mvp/requirements.txt
```

### 2. 配置环境变量

复制示例文件：

```bash
cp .env.example .env
```

如果需要 YouTube 登录态，编辑 `.env`：

```text
YTDLP_COOKIE_FILE=/absolute/path/to/cookies.txt
```

不需要 cookie 时可以留空或不创建 `.env`。

### 3. 启动操作台

```bash
streamlit run service_mvp/app.py
```

## 命令行用法

下载字幕：

```bash
python service_mvp/scripts/download_subtitles.py "https://www.youtube.com/watch?v=VIDEO_ID" -o service_mvp/cases/case_demo --lang en
```

清洗字幕：

```bash
python service_mvp/scripts/clean_vtt.py service_mvp/cases/case_demo/demo.en.vtt -o service_mvp/cases/case_demo/transcript.txt
```

## 目录说明

```text
service_mvp/
  app.py                         Streamlit 本地接单操作台
  scripts/                       字幕下载、清洗、环境变量工具
  cases/                         案例/交付样例
  tracking/                      运营记录模板
  xiaohongshu/                   小红书发布素材
  01_服务SOP.md                  接单 SOP
  02_固定Prompt.md               笔记生成 Prompt
  03_交付模板.md                 客户交付模板
```

## 敏感文件

不要提交：

- `.env`
- cookies 文件
- 用户订单数据
- 真实客户交付内容
- API Key / Token

已在 `.gitignore` 中排除主要敏感文件。

## 产品化路线

详见：

```text
docs/PRODUCTIZATION_PLAN.md
```

## 当前商业目标

第一阶段目标：

- 7 天内拿到 20 个感兴趣用户
- 5 个试用用户
- 1 个真实付费用户

定价验证：

- 首单体验：9.9 元 / 条
- 标准单次：19.9 元 / 条
- 小套餐：49 元 / 5 条

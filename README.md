# Info Digester MVP

英文 YouTube / 技术视频 → 中文 Markdown 学习笔记的服务型 MVP。

当前定位不是先做复杂 SaaS，而是先验证：用户是否愿意为“高质量中文学习笔记”付费。

## 当前能力

- 下载 YouTube 字幕：`yt-dlp`
- 清洗 `.vtt` 字幕为 `transcript.txt`
- 根据固定 Prompt 生成中文 Markdown 笔记
- Streamlit 本地操作台
- 接单 SOP（运营材料见 `docs/business/`）

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
TELEGRAM_BOT_TOKEN=123456:telegram_bot_token_from_botfather
OPENAI_COMPATIBLE_BASE_URL=https://api.deepseek.com
OPENAI_COMPATIBLE_API_KEY=your_ai_api_key
OPENAI_COMPATIBLE_MODEL=deepseek-v4-flash
OPENAI_COMPATIBLE_TEMPERATURE=0.2
OPENAI_COMPATIBLE_MAX_TOKENS=4096
```

不需要 cookie 时可以留空或不创建 `.env`。Telegram Bot 不启用时，`TELEGRAM_BOT_TOKEN` 也可以留空。

### 3. 启动操作台

```bash
streamlit run service_mvp/app.py
```

## 命令行用法

启动 Telegram Bot 接单入口：

```bash
export TELEGRAM_BOT_TOKEN="你的 BotFather Token"
python service_mvp/scripts/telegram_bot.py
```

第一版 Bot 的行为：

```text
用户发送 YouTube 链接
Bot 自动创建 case_tg_<chat_id>_<message_id>
Bot 写入 service_mvp/tracking/orders.csv
Bot 回复订单号和案例编号
Bot 自动下载英文字幕、清洗字幕、调用 OpenAI-compatible API 生成中文 Markdown
Bot 自动把中文笔记发回用户，并把订单标记为 delivered
```

如果没有配置 `OPENAI_COMPATIBLE_API_KEY`，Bot 仍会接单，但会回复自动处理失败提示；配置 API Key 后才是真正全自动。

后台交付：

```text
1. 在 Streamlit 里选择对应 case_tg_<chat_id>_<message_id>
2. 把最终内容保存到该 case 的 delivery.md
3. 点击“发送 delivery.md 给 Telegram 用户”
4. 系统会通过 Bot 发回用户，并把订单标记为 delivered
```

注意：当前交付稿按 Telegram 文本消息发送，建议控制在 3900 字以内；更长内容后续再改为文件发送。

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

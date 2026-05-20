# Info Digester 产品化实施计划

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 把当前本地 Streamlit 接单操作台，逐步产品化为可接单、可交付、可统计成本、最终可变现的 YouTube → 中文 Markdown 笔记服务。

**Architecture:** 先保持轻量本地/单机架构，不急着做复杂 SaaS。第一阶段用 Streamlit + CLI 提高交付效率；第二阶段增加 Telegram Bot 和 SQLite 用户/额度系统；第三阶段再考虑支付、后台和部署。

**Tech Stack:** Python, Streamlit, yt-dlp, SQLite, Telegram Bot API, Docker, GitHub Actions。

---

## Phase 0：仓库基础工程化

### Task 0.1: 补齐项目说明

**Objective:** 让任何人 clone 仓库后知道项目是什么、怎么运行、哪些文件不能提交。

**Files:**
- Create: `README.md`
- Modify: `.env.example`
- Modify: `service_mvp/requirements.txt`

**Verification:**

```bash
python -m compileall -q .
```

Expected: no output / exit 0。

### Task 0.2: 增加基础测试

**Objective:** 给字幕清洗核心逻辑加最小测试，避免后续产品化时改坏。

**Files:**
- Create: `tests/test_clean_vtt.py`
- Modify: `service_mvp/requirements.txt`

**Verification:**

```bash
pytest -q
```

Expected: all tests pass。

---

## Phase 1：提升当前接单交付效率

### Task 1.1: 标准化案例目录结构

**Objective:** 每个订单有统一结构，便于交付、复盘、统计。

**Target structure:**

```text
service_mvp/cases/case_YYYYMMDD_slug/
  source_url.txt
  transcript.txt
  prompt.txt
  note.md
  delivery.md
  metadata.json
```

**Files:**
- Modify: `service_mvp/app.py`
- Create: `service_mvp/scripts/case_manager.py`

**Verification:**

在 Streamlit 输入案例编号后，点击创建，自动生成上述文件或模板。

### Task 1.2: 一键生成完整 Prompt 文件

**Objective:** 当前页面可复制 Prompt，但应同时落盘保存，方便追踪和复用。

**Files:**
- Modify: `service_mvp/app.py`

**Verification:**

生成字幕后，点击按钮应创建：

```text
service_mvp/cases/<case_id>/prompt.txt
```

### Task 1.3: 增加交付质量检查结果保存

**Objective:** 把页面 checkbox 的质量检查结果保存到 `metadata.json`，而不是只显示在 UI。

**Files:**
- Modify: `service_mvp/app.py`
- Create/Modify: `service_mvp/scripts/case_manager.py`

**Verification:**

勾选检查项后点击保存，`metadata.json` 包含检查状态。

---

## Phase 2：最小可收费版本

### Task 2.1: 增加订单记录表

**Objective:** 用 CSV/SQLite 记录每个订单：链接、客户、价格、状态、交付路径。

**Files:**
- Create: `service_mvp/scripts/order_store.py`
- Modify: `service_mvp/app.py`

**Initial fields:**

```text
order_id, customer_name, customer_contact, youtube_url, price_cny, status, created_at, delivered_at, case_dir
```

**Verification:**

新增订单后，记录写入本地 SQLite 或 CSV。

### Task 2.2: 成本估算字段

**Objective:** 记录每条视频处理成本，判断是否能覆盖 token 费用。

**Fields:**

```text
transcript_chars, prompt_chars, output_chars, estimated_cost_usd
```

**Verification:**

每个 case 页面显示估算成本。

---

## Phase 3：Telegram Bot MVP

### Task 3.1: 创建 Telegram Bot 骨架

**Objective:** 用户发 YouTube 链接，Bot 返回“已收到，正在处理”的最小闭环。

**Files:**
- Create: `bot/main.py`
- Create: `bot/config.py`
- Modify: `requirements.txt` or `service_mvp/requirements.txt`

**Environment:**

```text
TELEGRAM_BOT_TOKEN=xxx
```

**Verification:**

```bash
python bot/main.py
```

给 bot 发消息，应收到回复。

### Task 3.2: 接入字幕下载与清洗

**Objective:** Bot 收到 YouTube 链接后自动下载字幕并生成 transcript。

**Files:**
- Modify: `bot/main.py`
- Reuse: `service_mvp/scripts/download_subtitles.py`
- Reuse: `service_mvp/scripts/clean_vtt.py`

**Verification:**

发 YouTube 链接后，Bot 返回清洗后的 transcript 摘要或文件。

### Task 3.3: 加每日免费额度

**Objective:** 控制成本，免费用户每天最多 3 次。

**Files:**
- Create: `bot/storage.py`
- Modify: `bot/main.py`

**Verification:**

同一 Telegram user 超过 3 次后，Bot 返回付费提示。

---

## Phase 4：部署和商业验证

### Task 4.1: Docker 化

**Objective:** 一条命令部署到 VPS。

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

**Verification:**

```bash
docker compose up -d
```

Streamlit 或 Bot 正常启动。

### Task 4.2: 增加 GitHub Actions 基础检查

**Objective:** 每次 push 自动跑语法检查和测试。

**Files:**
- Create: `.github/workflows/ci.yml`

**Verification:**

GitHub Actions 显示通过。

### Task 4.3: 发布首轮推广素材

**Objective:** 用现有小红书模板发布 3 条内容，拿真实反馈。

**Files:**
- Reuse: `service_mvp/04_小红书发布模板.md`
- Reuse: `service_mvp/05_私信销售话术.md`

**Verification:**

在 tracking 中记录：曝光、点赞、收藏、评论、私信、试用、付款。

---

## 当前优先级

立刻做：

1. Phase 0：README、依赖、测试、CI。
2. Phase 1：本地接单操作台增强。
3. Phase 3：Telegram Bot MVP。

暂时不做：

- 复杂 Web SaaS 登录系统
- 在线支付自动开通
- 多租户后台
- 复杂数据库权限
- 自动发布小红书

原因：当前目标是先赚回每月 token 成本，最短路径是服务型 MVP + 半自动接单。

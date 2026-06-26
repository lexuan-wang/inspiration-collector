# 灵感收集器

一个注重隐私的碎片化知识捕捉工具。手机随手记录语音/文字 →（可选）AI 自动整理口语、分类、打标签、提炼核心洞见 → 存入你的私有 GitHub 仓库 → 电脑 Obsidian 自动同步。

## 隐私架构（两仓库分离）

```
仓库 A（public）          仓库 B（private）
inspiration-collector     my-inspirations
只放工具网页              只放你的灵感数据
无任何个人数据            完全私密
手机可访问                token 写入
```

- **工具网页是公开的，但里面没有任何数据** —— 别人打开只看到登录框
- **你的灵感全部写进私有仓库 B** —— 谁都看不到
- **token 和 API Key 只存在你手机浏览器里** —— 永不上传

---

## AI 整理（可选，DeepSeek）

工具支持接入 **DeepSeek API**，把口语化的零散文字自动整理成书面表达，并自动完成分类、打标签、提炼一句「核心洞见」。

- **填了 DeepSeek Key** → 按钮显示「✨ AI 整理」，点一下由 AI 整理（去口语化但保留原意）、自动选好分类、自动填标签、底部显示紫色「💡 核心洞见」。
- **留空** → 按钮显示「✨ 整理文本」，回退到本地正则规则做基础口语清理，不联网、不花钱。

> Key 在 [platform.deepseek.com](https://platform.deepseek.com) 创建（`sk-...`），只存在你浏览器的 localStorage，调用时浏览器直接请求 DeepSeek，不经过任何第三方服务器。

---

## 部署步骤

### 第 1 步：建两个仓库

1. **公开工具仓库**（承载网页）：把本项目所有文件推到一个 **public** 仓库，例如 `inspiration-collector`
   ```bash
   cd inspiration-collector
   git init
   git remote add origin https://github.com/你的用户名/inspiration-collector.git
   git add .
   git commit -m "灵感收集器"
   git push -u origin main
   ```

2. **私有数据仓库**（存灵感）：在 GitHub 上新建一个 **private** 仓库，例如 `my-inspirations`，勾选 "Add a README"。**这个仓库里什么都不用放，等灵感自动写入。**

### 第 2 步：开启 GitHub Pages

在**公开工具仓库**的 Settings → Pages → Source 选 `main` 分支 → 保存。
几分钟后访问：`https://你的用户名.github.io/inspiration-collector/`

### 第 3 步：创建 GitHub Token

GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate new token：
- **Repository access**：只选你的**私有数据仓库** `my-inspirations`
- **Permissions** → Repository permissions → **Contents** 设为 **Read and write**
- 生成后复制 token（`github_pat_...`）

### 第 4 步（可选）：创建 DeepSeek API Key

想用 AI 整理就到 [platform.deepseek.com](https://platform.deepseek.com) 注册并创建 API Key（`sk-...`）。不想用可跳过，工具会用基础规则整理。

### 第 5 步：手机上使用

1. 手机浏览器打开 `https://你的用户名.github.io/inspiration-collector/`
2. 填入：GitHub 用户名、**私有数据仓库名**（`my-inspirations`）、token；如有 DeepSeek Key 一并填入「DeepSeek API Key（可选）」框
3. 浏览器菜单 → "添加到主屏幕"，变成 App 图标
4. 之后随手记录，点「✨ AI 整理」预览整理结果，再一键上传

### 第 6 步：电脑同步到 Obsidian

```bash
python3 sync.py
```
首次运行会问你**私有数据仓库地址**和 **Obsidian Vault 路径**，之后自动拉取所有灵感。

可设为定时任务（macOS）：
```bash
crontab -e
# 每 30 分钟同步一次
*/30 * * * * cd /path/to/inspiration-collector && python3 sync.py >> sync.log 2>&1
```

---

## 功能

- 🎤 浏览器语音转文字（Chrome）
- ✨ AI 整理（接入 DeepSeek）：去口语化、自动分类、自动打标签、提炼核心洞见；未配置 Key 时回退到本地正则做基础口语清理
- 🗂 分类：收件箱 / 学术研究 / 博士论文 / 讲座会议 / 阅读笔记 / 灵感想法 / 生活随想 / 工作
- 🏷 自由标签 + 背景说明
- 📄 每条灵感 = 一个独立 `.md` 文件，按分类存入 `entries/`
- 📱 PWA 离线可用，可"添加到主屏幕"

## 数据格式

每条灵感存为带 frontmatter 的 Markdown，可直接被 Obsidian 识别（`insight` 仅在 AI 提炼出核心洞见时出现）：

```markdown
---
date: 2026-06-26T13:00:00.000Z
category: 博士论文
tags: [国际传播, 规范竞争]
insight: "可将规范竞争概念引入论文分析框架"
context: "听完xx讲座的想法"
---

# 关于规范竞争的初步思考

整理后的正文内容……

> **💡 核心洞见：** 可将规范竞争概念引入论文分析框架

> **背景：** 听完xx讲座的想法
```

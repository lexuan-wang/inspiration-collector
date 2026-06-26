# 灵感收集器

一个注重隐私的碎片化知识捕捉工具。手机随手记录语音/文字 → 自动整理分类 → 存入你的私有 GitHub 仓库 → 电脑 Obsidian 自动同步。

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
- **token 只存在你手机浏览器里** —— 永不上传

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

### 第 3 步：创建 Token

GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate new token：
- **Repository access**：只选你的**私有数据仓库** `my-inspirations`
- **Permissions** → Repository permissions → **Contents** 设为 **Read and write**
- 生成后复制 token（`github_pat_...`）

### 第 4 步：手机上使用

1. 手机浏览器打开 `https://你的用户名.github.io/inspiration-collector/`
2. 填入：用户名、**私有数据仓库名**（`my-inspirations`）、token
3. 浏览器菜单 → "添加到主屏幕"，变成 App 图标
4. 之后随手记录，一键上传

### 第 5 步：电脑同步到 Obsidian

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
- ✨ 一键去除口语词（嗯、那个、就是说…）
- 🗂 分类：收件箱 / 学术研究 / 博士论文 / 讲座会议 / 阅读笔记 / 灵感想法 / 生活随想 / 工作
- 🏷 自由标签 + 背景说明
- 📄 每条灵感 = 一个独立 `.md` 文件，按分类存入 `entries/`
- 📱 PWA 离线可用，可"添加到主屏幕"

## 数据格式

每条灵感存为带 frontmatter 的 Markdown，可直接被 Obsidian 识别：

```markdown
---
date: 2026-06-26T13:00:00.000Z
category: 博士论文
tags: [国际传播, 方法论]
context: "跟第二章理论框架有关"
---

# 关于规范竞争的初步思考

整理后的正文内容……

> **背景：** 跟第二章理论框架有关
```

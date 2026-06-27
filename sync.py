#!/usr/bin/env python3
"""
灵感同步脚本 - 通过 GitHub API 从私有数据仓库拉取灵感到本地 Obsidian Vault

用 api.github.com 的 HTTPS 直接下载文件，绕开 git 协议在部分网络下不稳定的问题。

使用方法:
  python3 sync.py

首次运行会依次询问：私有数据仓库地址 / GitHub Token / Obsidian Vault 路径 / 目标文件夹，
配置保存在本脚本同目录的 .sync_config.json（含 token，已被 .gitignore 忽略）。
之后可设为定时任务自动运行（见 README）。

注意:
- 要同步的是存放灵感数据的【私有仓库】(例如 my-inspirations)，不是公开工具仓库。
- macOS 上若报 CERTIFICATE_VERIFY_FAILED，先装证书包: python3 -m pip install --user certifi
"""

import os
import json
import sys
import ssl
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlparse

CONFIG_FILE = Path(__file__).parent / '.sync_config.json'
API = 'https://api.github.com'

# 用 certifi 的根证书，避免 macOS 上 Python 找不到证书报 SSL 错；没装 certifi 就用系统默认。
try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CTX = ssl.create_default_context()


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return None


def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def setup():
    print('=== 灵感同步配置 ===')
    print('提示: 这里填【私有数据仓库】，就是存灵感的那个 (例如 my-inspirations)。')
    repo_url = input('GitHub 私有数据仓库地址 (如 https://github.com/lexuan-wang/my-inspirations): ').strip()
    token = input('GitHub Token (github_pat_...): ').strip()
    vault_path = os.path.expanduser(input('Obsidian Vault 路径: ').strip())
    target_folder = input('Vault 中的目标文件夹 (默认 灵感收集): ').strip() or '灵感收集'
    cfg = {
        'repo_url': repo_url,
        'token': token,
        'vault_path': vault_path,
        'target_folder': target_folder
    }
    save_config(cfg)
    print('配置已保存到', CONFIG_FILE)
    print('（该文件含 token，已被 .gitignore 忽略，不会被提交到公开仓库）')
    return cfg


def owner_repo(repo_url):
    parts = [x for x in urlparse(repo_url).path.split('/') if x]
    if len(parts) < 2:
        print('错误: 仓库地址格式不对，应类似 https://github.com/用户名/仓库名')
        sys.exit(1)
    repo = parts[1][:-4] if parts[1].endswith('.git') else parts[1]
    return parts[0], repo


def api_get(url, token, accept='application/vnd.github+json'):
    req = urllib.request.Request(url)
    req.add_header('Authorization', 'Bearer ' + token)
    req.add_header('Accept', accept)
    req.add_header('User-Agent', 'inspiration-sync')
    try:
        with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        print('GitHub API 失败 (HTTP %s)' % e.code)
        if e.code in (401, 403):
            print('→ token 无效或无该私有仓库 Contents 读取权限')
        elif e.code == 404:
            print('→ 找不到仓库/路径，检查仓库地址与 token 权限')
        sys.exit(1)
    except Exception as e:
        print('网络错误: %s' % e)
        sys.exit(1)


def sync(cfg):
    token = cfg.get('token', '')
    owner, repo = owner_repo(cfg['repo_url'])
    vault = Path(cfg['vault_path'])
    target = vault / cfg['target_folder']

    if not vault.exists():
        print('错误: Vault 路径不存在: %s' % vault)
        sys.exit(1)

    info = json.loads(api_get('%s/repos/%s/%s' % (API, owner, repo), token))
    branch = info.get('default_branch', 'main')

    tree = json.loads(api_get('%s/repos/%s/%s/git/trees/%s?recursive=1' % (API, owner, repo, branch), token))
    if tree.get('truncated'):
        print('提示: 文件较多，本次列表可能不完整，但已下载到的部分有效。')

    items = [t for t in tree.get('tree', [])
             if t.get('type') == 'blob'
             and t.get('path', '').startswith('entries/')
             and t.get('path', '').endswith('.md')]

    if not items:
        print('仓库里还没有灵感文件（entries/ 下没有 .md），等待首条灵感...')
        return

    target.mkdir(parents=True, exist_ok=True)

    copied = 0
    for it in items:
        rel = it['path'][len('entries/'):]
        dest = target / rel
        if dest.exists():
            continue
        raw = api_get('%s/repos/%s/%s/contents/%s?ref=%s' % (API, owner, repo, it['path'], branch),
                      token, 'application/vnd.github.raw')
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, 'wb') as f:
            f.write(raw)
        copied += 1
        print('  同步: ' + rel)

    if copied:
        print('同步完成，新增 %d 个文件' % copied)
    else:
        print('已是最新，无需同步')


def main():
    cfg = load_config()
    if not cfg:
        cfg = setup()
    sync(cfg)


if __name__ == '__main__':
    main()

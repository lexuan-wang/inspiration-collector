#!/usr/bin/env python3
"""
灵感同步脚本 - 自动从 GitHub 私有数据仓库拉取最新灵感到本地 Obsidian Vault

使用方法:
  python3 sync.py

首次运行会提示配置（仓库地址 / token / Obsidian 路径），之后可设为定时任务自动运行。

macOS 定时任务:
  crontab -e
  */30 * * * * cd /path/to/this/folder && python3 sync.py >> sync.log 2>&1

Windows 定时任务:
  使用"任务计划程序"，每30分钟运行一次此脚本

注意: 要同步的是存放灵感数据的【私有仓库】(例如 my-inspirations)，
      不是公开的工具仓库 (inspiration-collector)。私有仓库需要 token 认证。
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

CONFIG_FILE = Path(__file__).parent / '.sync_config.json'

# 不要让 git 在认证失败时弹出交互式输入（定时任务里会卡死）
os.environ.setdefault('GIT_TERMINAL_PROMPT', '0')

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return None

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def setup():
    print('=== 灵感同步配置 ===\n')
    print('提示: 这里要填【私有数据仓库】，就是存灵感的那个 (例如 my-inspirations)。\n')

    repo_url = input('GitHub 私有数据仓库地址 (例如: https://github.com/lexuan-wang/my-inspirations): ').strip()
    token = input('GitHub Token (private 仓库必填, 就用手机上那个 github_pat_...): ').strip()
    vault_path = input('Obsidian Vault 路径 (例如: ~/Documents/MyVault): ').strip()
    vault_path = os.path.expanduser(vault_path)
    target_folder = input('Vault 中的目标文件夹 (默认: 灵感收集): ').strip() or '灵感收集'

    cfg = {
        'repo_url': repo_url,
        'token': token,
        'vault_path': vault_path,
        'target_folder': target_folder
    }

    save_config(cfg)
    print(f'\n配置已保存到 {CONFIG_FILE}')
    print('（该文件含 token，已被 .gitignore 忽略，不会被提交到公开仓库）')
    return cfg

def authed_url(repo_url, token):
    """把 token 嵌进 https 地址用于认证；无 token 则原样返回。"""
    if not token:
        return repo_url
    parts = urlparse(repo_url)
    if parts.scheme != 'https':
        return repo_url
    # 形如 https://<token>@github.com/owner/repo.git
    netloc = parts.hostname or ''
    if parts.port:
        netloc += f':{parts.port}'
    netloc = f'{token}@{netloc}'
    return urlunparse((parts.scheme, netloc, parts.path, parts.params, parts.query, parts.fragment))

def run_git(args):
    """运行 git 命令，失败时给出清晰提示而不是泄露 token。"""
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        msg = (result.stderr or result.stdout or '').strip()
        print(f'git 命令失败: {msg}')
        if 'Authentication failed' in msg or 'could not read' in msg or 'terminal prompts disabled' in msg:
            print('→ 认证失败，请检查 token 是否正确、是否对该私有仓库有 Contents 读取权限。')
        sys.exit(1)

def sync(cfg):
    repo_url = cfg['repo_url']
    token = cfg.get('token', '')
    url = authed_url(repo_url, token)
    vault_path = Path(cfg['vault_path'])
    target = vault_path / cfg['target_folder']
    clone_dir = Path(__file__).parent / '.repo_cache'

    if not vault_path.exists():
        print(f'错误: Vault 路径不存在: {vault_path}')
        sys.exit(1)

    if not clone_dir.exists():
        print('首次克隆仓库...')
        run_git(['git', 'clone', url, str(clone_dir)])
    else:
        # 刷新远端地址（token 可能已更新），再拉取
        run_git(['git', '-C', str(clone_dir), 'remote', 'set-url', 'origin', url])
        print('拉取最新更新...')
        run_git(['git', '-C', str(clone_dir), 'pull', '--ff-only'])

    entries_dir = clone_dir / 'entries'
    if not entries_dir.exists():
        print('仓库中还没有 entries 文件夹，等待首条灵感...')
        return

    target.mkdir(parents=True, exist_ok=True)

    copied = 0
    for md_file in entries_dir.rglob('*.md'):
        rel = md_file.relative_to(entries_dir)
        dest_dir = target / rel.parent
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / md_file.name

        if not dest.exists() or md_file.stat().st_mtime > dest.stat().st_mtime:
            import shutil
            shutil.copy2(md_file, dest)
            copied += 1
            print(f'  同步: {rel}')

    if copied:
        print(f'\n同步完成，新增/更新 {copied} 个文件')
    else:
        print('已是最新，无需同步')

def main():
    cfg = load_config()
    if not cfg:
        cfg = setup()
        print()

    sync(cfg)

if __name__ == '__main__':
    main()

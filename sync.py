#!/usr/bin/env python3
"""
灵感同步脚本 - 自动从 GitHub 拉取最新灵感到本地 Obsidian Vault

使用方法:
  python3 sync.py

首次运行会提示配置，之后可以设为定时任务自动运行。

macOS 定时任务:
  crontab -e
  */30 * * * * cd /path/to/this/folder && python3 sync.py >> sync.log 2>&1

Windows 定时任务:
  使用"任务计划程序"，每30分钟运行一次此脚本
"""

import os
import json
import subprocess
import sys
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / '.sync_config.json'

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

    repo_url = input('GitHub 仓库地址 (例如: https://github.com/lexuan-wang/inspiration-collector): ').strip()
    vault_path = input('Obsidian Vault 路径 (例如: ~/Documents/MyVault): ').strip()
    vault_path = os.path.expanduser(vault_path)
    target_folder = input('Vault 中的目标文件夹 (默认: 灵感收集): ').strip() or '灵感收集'

    cfg = {
        'repo_url': repo_url,
        'vault_path': vault_path,
        'target_folder': target_folder
    }

    save_config(cfg)
    print(f'\n配置已保存到 {CONFIG_FILE}')
    return cfg

def sync(cfg):
    repo_url = cfg['repo_url']
    vault_path = Path(cfg['vault_path'])
    target = vault_path / cfg['target_folder']
    clone_dir = Path(__file__).parent / '.repo_cache'

    if not vault_path.exists():
        print(f'错误: Vault 路径不存在: {vault_path}')
        sys.exit(1)

    if not clone_dir.exists():
        print(f'首次克隆仓库...')
        subprocess.run(['git', 'clone', repo_url, str(clone_dir)], check=True)
    else:
        print('拉取最新更新...')
        subprocess.run(['git', '-C', str(clone_dir), 'pull', '--ff-only'], check=True)

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

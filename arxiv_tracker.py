#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arXiv智能论文追踪器
基于胶水编程原则：能抄不写，能连不造，能复用不原创
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arXiv智能论文追踪器
基于胶水编程原则：能抄不写，能连不造，能复用不原创
"""

import argparse
import json
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set
from unittest.mock import patch
import urllib3
import requests

# 必须在导入arxiv之前设置SSL相关环境变量
def setup_ssl_context(verify_ssl: bool):
    """设置SSL上下文 - 必须在import arxiv之前调用"""
    if not verify_ssl:
        os.environ['PYTHONHTTPSVERIFY'] = '0'
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import arxiv
from tqdm import tqdm
import pandas as pd


class ArxivTracker:
    """arXiv论文追踪器 - 胶水代码核心类"""

    def __init__(self, config: Dict):
        self.config = config
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=3.0,
            num_retries=5
        )
        self.history_file = Path(config.get('history_file', 'papers_history.json'))
        self.seen_ids = self._load_history()
        self.results = []

    def _load_history(self) -> Set[str]:
        """加载历史记录用于去重"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except (json.JSONDecodeError, IOError):
                return set()
        return set()

    def _save_history(self):
        """保存历史记录"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.seen_ids), f, indent=2, ensure_ascii=False)

    def _build_query(self) -> str:
        """构建arXiv查询字符串"""
        query_parts = []

        # 添加分类过滤
        if self.config.get('categories'):
            cat_query = ' OR '.join([f"cat:{cat}" for cat in self.config['categories']])
            query_parts.append(f"({cat_query})")

        # 添加关键词搜索
        if self.config.get('keywords'):
            keyword_fields = self.config.get('keyword_fields', ['all'])
            keyword_query = ' OR '.join([
                f"{field}:{kw}" for field in keyword_fields for kw in self.config['keywords']
            ])
            query_parts.append(f"({keyword_query})")

        return ' AND '.join(query_parts) if query_parts else 'cat:cs.*'

    def search_papers(self) -> List[arxiv.Result]:
        """搜索论文 - 使用arxiv官方SDK"""
        query_str = self._build_query()

        # 使用官方SDK构建搜索
        search = arxiv.Search(
            query=query_str,
            max_results=self.config.get('max_results', 10),
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        # 获取结果并显示进度
        results = []
        total = self.config.get('max_results', 10)

        print(f"\n🔍 正在搜索arXiv论文...")
        print(f"📋 查询语句: {query_str}")

        for result in tqdm(self.client.results(search), total=total, desc="获取论文"):
            # 去重过滤
            if result.entry_id.split('/')[-1] not in self.seen_ids:
                results.append(result)
                self.seen_ids.add(result.entry_id.split('/')[-1])

        # 保存历史
        self._save_history()

        print(f"✅ 找到 {len(results)} 篇新论文\n")

        return results

    def parse_paper(self, result: arxiv.Result) -> Dict:
        """解析论文信息"""
        authors = ', '.join([author.name for author in result.authors[:3]])
        if len(result.authors) > 3:
            authors += f" et al. ({len(result.authors)} authors)"

        return {
            'arxiv_id': result.entry_id.split('/')[-1],
            'title': result.title,
            'authors': authors,
            'summary': result.summary.replace('\n', ' ')[:300] + '...',
            'published': result.published.strftime('%Y-%m-%d'),
            'categories': ', '.join(result.categories),
            'url': result.entry_id,
            'pdf_url': result.pdf_url
        }

    def output_results(self, papers: List[Dict]):
        """多格式输出结果"""
        if not papers:
            print("📭 暂无新论文")
            return

        df = pd.DataFrame(papers)
        date_str = datetime.now().strftime('%Y-%m-%d')
        output_dir = Path(self.config.get('output_dir', 'outputs'))
        output_dir.mkdir(exist_ok=True)

        output_formats = self.config.get('output_formats', ['console'])

        for fmt in output_formats:
            if fmt == 'console':
                self._print_to_console(papers)
            elif fmt == 'txt':
                self._save_txt(df, output_dir, date_str)
            elif fmt == 'md':
                self._save_markdown(papers, output_dir, date_str)
            elif fmt == 'csv':
                df.to_csv(output_dir / f'{date_str}_results.csv', index=False, encoding='utf-8')
                print(f"💾 CSV已保存: {output_dir / f'{date_str}_results.csv'}")
            elif fmt == 'json':
                df.to_json(output_dir / f'{date_str}_results.json', orient='records',
                          force_ascii=False, indent=2)
                print(f"💾 JSON已保存: {output_dir / f'{date_str}_results.json'}")

    def _print_to_console(self, papers: List[Dict]):
        """终端格式化输出"""
        print("=" * 80)
        print(f"📚 arXiv论文追踪结果 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 80)

        for i, paper in enumerate(papers, 1):
            print(f"\n【{i}】{paper['title']}")
            print(f"    ID: {paper['arxiv_id']}")
            print(f"    作者: {paper['authors']}")
            print(f"    发布: {paper['published']} | 分类: {paper['categories']}")
            print(f"    摘要: {paper['summary']}")
            print(f"    链接: {paper['url']}")
            print(f"    PDF: {paper['pdf_url']}")

        print("\n" + "=" * 80)

    def _save_txt(self, df: pd.DataFrame, output_dir: Path, date_str: str):
        """保存为TXT格式"""
        filepath = output_dir / f'{date_str}_results.txt'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"arXiv论文追踪结果 - {date_str}\n")
            f.write("=" * 80 + "\n\n")
            for _, row in df.iterrows():
                f.write(f"【{row['arxiv_id']}】{row['title']}\n")
                f.write(f"作者: {row['authors']}\n")
                f.write(f"发布: {row['published']} | 分类: {row['categories']}\n")
                f.write(f"摘要: {row['summary']}\n")
                f.write(f"链接: {row['url']}\n")
                f.write(f"PDF: {row['pdf_url']}\n\n")
        print(f"💾 TXT已保存: {filepath}")

    def _save_markdown(self, papers: List[Dict], output_dir: Path, date_str: str):
        """保存为Markdown格式"""
        filepath = output_dir / f'{date_str}_results.md'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# arXiv论文追踪结果 - {date_str}\n\n")
            f.write(f"**查询时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(f"**论文数量**: {len(papers)}\n\n")
            f.write("---\n\n")

            for paper in papers:
                f.write(f"## {paper['title']}\n\n")
                f.write(f"**arXiv ID**: `{paper['arxiv_id']}`  \n")
                f.write(f"**作者**: {paper['authors']}  \n")
                f.write(f"**发布日期**: {paper['published']}  \n")
                f.write(f"**分类**: {paper['categories']}\n\n")
                f.write(f"**摘要**: {paper['summary']}\n\n")
                f.write(f"**链接**: [论文页面]({paper['url']}) | [PDF下载]({paper['pdf_url']})\n\n")
                f.write("---\n\n")
        print(f"💾 Markdown已保存: {filepath}")

    def run(self):
        """运行主流程"""
        papers = self.search_papers()
        self.results = [self.parse_paper(p) for p in papers]
        self.output_results(self.results)


def load_config(config_path: str) -> Dict:
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"⚠️  配置文件加载失败: {e}")
        return None


def interactive_config() -> Dict:
    """交互式配置生成"""
    print("\n🔧 交互式配置向导")
    print("=" * 50)

    config = {}

    # 分类选择
    print("\n请输入arXiv分类（用空格分隔，直接回车跳过）")
    print("常用分类: cs.CV(计算机视觉) cs.LG(机器学习) cs.AI(人工智能)")
    print("         cs.CL(自然语言处理) cs.CR(密码学) stat.ML(统计机器学习)")
    cats = input("分类> ").strip()
    if cats:
        config['categories'] = cats.split()

    # 关键词输入
    print("\n请输入关键词（用空格分隔，直接回车跳过）")
    kws = input("关键词> ").strip()
    if kws:
        config['keywords'] = kws.split()
        print("\n关键词搜索范围:")
        print("  1. 标题 (ti:)")
        print("  2. 摘要 (abs:)")
        print("  3. 全部 (all:)")
        field_choice = input("选择 (默认3)> ").strip() or "3"
        field_map = {'1': ['ti:'], '2': ['abs:'], '3': ['all:']}
        config['keyword_fields'] = field_map.get(field_choice, ['all:'])

    # 论文数量
    max_results = input("\n获取论文数量 (默认10)> ").strip() or "10"
    config['max_results'] = int(max_results)

    # 输出格式
    print("\n输出格式 (多选用空格分隔):")
    print("  console  - 终端显示")
    print("  txt      - 文本文件")
    print("  md       - Markdown文件")
    print("  csv      - CSV文件")
    print("  json     - JSON文件")
    formats = input("格式 (默认: console)> ").strip() or "console"
    config['output_formats'] = formats.split()

    # 静默模式
    silent = input("\n启用静默模式? (y/N, 默认N)> ").strip().lower()
    config['silent'] = silent == 'y'

    return config


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description='arXiv智能论文追踪器 - 基于胶水编程原则',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s --config config.json                    # 使用配置文件
  %(prog)s --categories cs.CV cs.LG --keywords GPT # 命令行参数
  %(prog)s --interactive                          # 交互式配置
  %(prog)s --config config.json --silent          # 静默模式

Crontab配置示例:
  0 8 * * * /usr/bin/python3 %(prog)s --config config.json --silent
        """
    )

    parser.add_argument('--config', '-c', help='配置文件路径 (JSON格式)')
    parser.add_argument('--categories', nargs='+', help='arXiv分类 (如 cs.CV cs.LG)')
    parser.add_argument('--keywords', nargs='+', help='搜索关键词')
    parser.add_argument('--keyword-fields', nargs='+', choices=['ti:', 'abs:', 'all:'],
                       default=['all:'], help='关键词搜索字段')
    parser.add_argument('--max-results', type=int, default=10, help='最大结果数 (默认: 10)')
    parser.add_argument('--output-dir', '-o', default='outputs', help='输出目录 (默认: outputs)')
    parser.add_argument('--output-formats', nargs='+',
                       choices=['console', 'txt', 'md', 'csv', 'json'],
                       default=['console'], help='输出格式')
    parser.add_argument('--history-file', default='papers_history.json', help='历史记录文件')
    parser.add_argument('--silent', '-s', action='store_true', help='静默模式')
    parser.add_argument('--interactive', '-i', action='store_true', help='交互式配置')
    parser.add_argument('--no-verify-ssl', action='store_true',
                       help='禁用SSL验证（用于证书问题环境）')

    args = parser.parse_args()

    # 配置优先级: 配置文件 > 命令行参数 > 交互式
    config = {}

    # 1. 尝试加载配置文件
    if args.config:
        config = load_config(args.config)
        if not config:
            if not args.silent:
                print("❌ 无法加载配置文件，程序退出")
            sys.exit(1)

    # 2. 命令行参数覆盖配置文件
    if args.categories:
        config['categories'] = args.categories
    if args.keywords:
        config['keywords'] = args.keywords
        config['keyword_fields'] = args.keyword_fields
    if hasattr(args, 'max_results'):
        config['max_results'] = args.max_results
    if hasattr(args, 'output_dir'):
        config['output_dir'] = args.output_dir
    if hasattr(args, 'output_formats'):
        config['output_formats'] = args.output_formats
    if hasattr(args, 'history_file'):
        config['history_file'] = args.history_file
    if hasattr(args, 'silent'):
        config['silent'] = args.silent

    # 3. 交互式模式
    if args.interactive or (not config and not args.categories and not args.keywords):
        if not args.silent:
            config = interactive_config()
            # 保存交互式配置
            config_path = 'config.json'
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"\n✅ 配置已保存到 {config_path}")

    # 设置默认值
    config.setdefault('categories', [])
    config.setdefault('keywords', [])
    config.setdefault('keyword_fields', ['all:'])
    config.setdefault('max_results', 10)
    config.setdefault('output_dir', 'outputs')
    config.setdefault('output_formats', ['console'])
    config.setdefault('history_file', 'papers_history.json')
    config.setdefault('silent', False)
    config.setdefault('verify_ssl', not args.no_verify_ssl)

    # SSL问题提示
    if not config['verify_ssl'] and not config['silent']:
        print("⚠️  SSL验证已禁用，仅用于调试目的")

    # 在创建tracker之前设置SSL上下文
    setup_ssl_context(config.get('verify_ssl', True))

    # 运行追踪器
    try:
        tracker = ArxivTracker(config)
        if config['silent']:
            # 静默模式重定向输出
            import io
            import contextlib

            with contextlib.redirect_stdout(io.StringIO()):
                tracker.run()
            print(f"✅ 完成，获取 {len(tracker.results)} 篇论文")
        else:
            tracker.run()

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(0)
    except requests.exceptions.SSLError as e:
        print("\n❌ SSL连接错误")
        print("这可能是由网络环境或证书问题导致的")
        print("请尝试以下解决方案：")
        print("  1. 使用 --no-verify-ssl 参数禁用SSL验证")
        print("  2. 检查网络连接")
        print("  3. 更新系统证书: sudo apt-get install ca-certificates")
        if not args.silent:
            print(f"\n详细错误: {e}")
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ 错误: {error_msg}")

        # SSL错误提示
        if 'SSL' in error_msg or 'EOF' in error_msg:
            print("💡 提示: 尝试使用 --no-verify-ssl 参数")

        if not args.silent:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

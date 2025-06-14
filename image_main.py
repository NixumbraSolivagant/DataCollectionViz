#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import logging
from image_crawler import ImageCrawler
from image_viewer import ImageViewer, ImageManager
import tkinter as tk

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('image_system.log'),
            logging.StreamHandler()
        ]
    )

def crawl_images(args):
    """爬取图片"""
    print("开始爬取引力波相关图片...")
    
    crawler = ImageCrawler(
        save_dir=args.save_dir,
        max_images=args.max_images
    )
    
    crawler.crawl_images()
    
    print(f"爬取完成！图片保存在: {args.save_dir}")

def view_images(args):
    """查看图片"""
    print("启动图片查看器...")
    
    root = tk.Tk()
    app = ImageViewer(root, images_dir=args.images_dir)
    root.mainloop()

def show_stats(args):
    """显示统计信息"""
    manager = ImageManager(images_dir=args.images_dir)
    stats = manager.get_image_stats()
    
    print("\n=== 图片统计信息 ===")
    print(f"原始图片数量: {stats['raw_count']}")
    print(f"处理后图片数量: {stats['processed_count']}")
    print(f"总文件大小: {stats['total_size'] / 1024 / 1024:.2f} MB")
    
    if stats['metadata']:
        print(f"\n=== 元数据信息 ===")
        metadata = stats['metadata']
        print(f"总下载数量: {metadata.get('total_downloaded', 0)}")
        print(f"成功下载: {len(metadata.get('successful_urls', []))}")
        print(f"失败下载: {len(metadata.get('failed_urls', []))}")
        print(f"搜索关键词: {', '.join(metadata.get('search_keywords', [])[:5])}...")

def export_metadata(args):
    """导出元数据"""
    manager = ImageManager(images_dir=args.images_dir)
    output_path = args.output or "image_metadata_export.json"
    
    manager.export_metadata(output_path)
    print(f"元数据已导出到: {output_path}")

def main():
    """主函数"""
    setup_logging()
    
    parser = argparse.ArgumentParser(description="引力波图片爬取和查看系统")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 爬取图片命令
    crawl_parser = subparsers.add_parser('crawl', help='爬取图片')
    crawl_parser.add_argument('--save-dir', default='images', help='保存目录')
    crawl_parser.add_argument('--max-images', type=int, default=500, help='最大图片数量')
    
    # 查看图片命令
    view_parser = subparsers.add_parser('view', help='查看图片')
    view_parser.add_argument('--images-dir', default='images', help='图片目录')
    
    # 统计信息命令
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')
    stats_parser.add_argument('--images-dir', default='images', help='图片目录')
    
    # 导出元数据命令
    export_parser = subparsers.add_parser('export', help='导出元数据')
    export_parser.add_argument('--images-dir', default='images', help='图片目录')
    export_parser.add_argument('--output', help='输出文件路径')
    
    args = parser.parse_args()
    
    if not args.command:
        # 如果没有指定命令，显示帮助
        parser.print_help()
        return
    
    try:
        if args.command == 'crawl':
            crawl_images(args)
        elif args.command == 'view':
            view_images(args)
        elif args.command == 'stats':
            show_stats(args)
        elif args.command == 'export':
            export_metadata(args)
    except KeyboardInterrupt:
        print("\n操作被用户中断")
    except Exception as e:
        print(f"发生错误: {str(e)}")
        logging.error(f"程序错误: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
引力波数据爬虫与可视化系统
主程序入口

功能包括：
1. 网页爬虫 - 爬取GWOSC事件列表和数据文件
2. 数据处理 - 分析和处理引力波数据
3. 数据存储 - 本地文件存储和管理
4. Web可视化 - Flask Web应用
5. 桌面GUI - Tkinter图形界面
6. 异常处理 - 完善的错误处理机制
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT
from database import DataManager
from crawler import GWOSCCrawler
from data_processor import DataProcessor
from web_app import app as flask_app
from gui_app import GWOSCGUI

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_environment():
    """设置运行环境"""
    try:
        # 创建必要的目录
        from config import DATA_DIR, CACHE_DIR, LOGS_DIR
        for directory in [DATA_DIR, CACHE_DIR, LOGS_DIR]:
            os.makedirs(directory, exist_ok=True)
        
        # 初始化数据管理器
        db = DataManager()
        logger.info("环境设置完成")
        return True
        
    except Exception as e:
        logger.error(f"环境设置失败: {e}")
        return False

def run_crawler(limit=None):
    """运行爬虫"""
    try:
        logger.info("启动爬虫...")
        crawler = GWOSCCrawler()
        success_count = crawler.crawl_all_events(limit=limit)
        if success_count > 0:
            logger.info(f"成功处理 {success_count} 个数据文件")
            return True
        else:
            logger.error("事件列表爬取失败")
            return False
    except Exception as e:
        logger.error(f"爬虫运行失败: {e}")
        return False

def run_web_app():
    """运行Web应用"""
    try:
        logger.info("启动Web应用...")
        from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG
        
        print(f"Web应用启动在: http://{FLASK_HOST}:{FLASK_PORT}")
        print("按 Ctrl+C 停止服务器")
        
        flask_app.run(
            host=FLASK_HOST,
            port=FLASK_PORT,
            debug=FLASK_DEBUG,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        logger.info("Web应用已停止")
    except Exception as e:
        logger.error(f"Web应用运行失败: {e}")

def run_gui_app():
    """运行GUI应用"""
    try:
        logger.info("启动GUI应用...")
        app = GWOSCGUI()
        app.run()
        
    except Exception as e:
        logger.error(f"GUI应用运行失败: {e}")

def analyze_event(event_name, detectors=None):
    """分析指定事件"""
    try:
        logger.info(f"分析事件: {event_name}")
        
        processor = DataProcessor()
        results = processor.analyze_event_data(event_name, detectors)
        
        if results:
            # 保存分析结果
            output_dir = processor.save_analysis_results(event_name, results)
            logger.info(f"分析完成，结果保存到: {output_dir}")
            
            # 显示统计信息
            if 'detectors' in results:
                for detector, data in results['detectors'].items():
                    stats = data.get('statistics', {})
                    logger.info(f"探测器 {detector} 统计信息:")
                    for key, value in stats.items():
                        logger.info(f"  {key}: {value}")
            
            return True
        else:
            logger.error(f"事件 {event_name} 分析失败")
            return False
            
    except Exception as e:
        logger.error(f"分析事件失败: {e}")
        return False

def download_event(event_name):
    """下载指定事件数据"""
    try:
        logger.info(f"下载事件数据: {event_name}")
        
        crawler = GWOSCCrawler()
        success = crawler.download_event_data(event_name)
        
        if success:
            logger.info(f"事件 {event_name} 数据下载成功")
            return True
        else:
            logger.error(f"事件 {event_name} 数据下载失败")
            return False
            
    except Exception as e:
        logger.error(f"下载事件数据失败: {e}")
        return False

def list_events():
    """列出所有事件"""
    try:
        logger.info("获取事件列表...")
        db = DataManager()
        events = db.get_all_events()
        
        if events:
            print(f"\n找到 {len(events)} 个事件:")
            print("-" * 80)
            for event in events[:20]:  # 只显示前20个
                event_name = event.get('common_name') or event.get('event_id', 'Unknown')
                gps_time = event.get('gps_time', 'N/A')
                mass1 = event.get('mass_1_source', 'N/A')
                mass2 = event.get('mass_2_source', 'N/A')
                distance = event.get('luminosity_distance', 'N/A')
                
                print(f"事件: {event_name}")
                print(f"  GPS时间: {gps_time}")
                print(f"  质量1: {mass1} {event.get('mass_1_source_unit', '')}")
                print(f"  质量2: {mass2} {event.get('mass_2_source_unit', '')}")
                print(f"  距离: {distance} {event.get('luminosity_distance_unit', '')}")
                print("-" * 80)
        else:
            print("没有找到任何事件")
            
    except Exception as e:
        logger.error(f"获取事件列表失败: {e}")

def show_event_info(event_name):
    """显示事件详细信息"""
    try:
        logger.info(f"获取事件信息: {event_name}")
        db = DataManager()
        event = db.get_event_by_name(event_name)
        
        if event:
            print(f"\n事件详细信息: {event_name}")
            print("=" * 80)
            
            # 基本信息
            print("基本信息:")
            print(f"  事件ID: {event.get('event_id', 'N/A')}")
            print(f"  通用名称: {event.get('common_name', 'N/A')}")
            print(f"  版本: {event.get('version', 'N/A')}")
            print(f"  目录: {event.get('catalog', 'N/A')}")
            print(f"  GPS时间: {event.get('gps_time', 'N/A')}")
            print(f"  GraceDB ID: {event.get('gracedb_id', 'N/A')}")
            
            # 物理参数
            print("\n物理参数:")
            print(f"  质量1: {event.get('mass_1_source', 'N/A')} {event.get('mass_1_source_unit', '')}")
            print(f"  质量2: {event.get('mass_2_source', 'N/A')} {event.get('mass_2_source_unit', '')}")
            print(f"  总质量: {event.get('total_mass_source', 'N/A')} {event.get('total_mass_source_unit', '')}")
            print(f"  啁啾质量: {event.get('chirp_mass_source', 'N/A')} {event.get('chirp_mass_source_unit', '')}")
            print(f"  距离: {event.get('luminosity_distance', 'N/A')} {event.get('luminosity_distance_unit', '')}")
            print(f"  红移: {event.get('redshift', 'N/A')} {event.get('redshift_unit', '')}")
            print(f"  有效自旋: {event.get('chi_eff', 'N/A')} {event.get('chi_eff_unit', '')}")
            
            # 应变数据
            strain_data = event.get('strain_data', [])
            if strain_data:
                print(f"\n应变数据 ({len(strain_data)} 个文件):")
                for i, strain in enumerate(strain_data[:5]):  # 只显示前5个
                    print(f"  {i+1}. 探测器: {strain.get('detector', 'N/A')}")
                    print(f"     采样率: {strain.get('sampling_rate', 'N/A')} Hz")
                    print(f"     持续时间: {strain.get('duration', 'N/A')} 秒")
                    print(f"     格式: {strain.get('format', 'N/A')}")
                    print(f"     URL: {strain.get('url', 'N/A')}")
            
            # 数据文件
            data_files = event.get('data_files', [])
            if data_files:
                print(f"\n已下载数据文件 ({len(data_files)} 个):")
                for file_info in data_files:
                    print(f"  探测器: {file_info.get('detector', 'N/A')}")
                    print(f"  文件路径: {file_info.get('file_path', 'N/A')}")
                    print(f"  文件大小: {file_info.get('file_size', 'N/A')} bytes")
                    print(f"  下载状态: {file_info.get('download_status', 'N/A')}")
            
        else:
            print(f"未找到事件: {event_name}")
            
    except Exception as e:
        logger.error(f"获取事件信息失败: {e}")

def show_help():
    """显示帮助信息"""
    help_text = """
引力波数据爬虫与可视化系统

使用方法:
    python main.py [选项] [参数]

选项:
    -h, --help              显示此帮助信息
    -w, --web               启动Web应用
    -g, --gui               启动GUI应用
    -c, --crawl [LIMIT]     运行爬虫获取事件列表
    -d, --download EVENT    下载指定事件的数据
    -a, --analyze EVENT     分析指定事件的数据
    -l, --list              列出所有事件
    -i, --info EVENT        显示事件详细信息
    -s, --setup             设置运行环境

示例:
    python main.py --web                    # 启动Web应用
    python main.py --gui                    # 启动GUI应用
    python main.py --crawl                  # 爬取事件列表
    python main.py --crawl 5                # 爬取前5个事件
    python main.py --download GW150914      # 下载GW150914事件数据
    python main.py --analyze GW150914       # 分析GW150914事件数据
    python main.py --list                   # 列出所有事件
    python main.py --info GW150914          # 显示GW150914详细信息
    python main.py --setup                  # 设置运行环境

功能说明:
    1. 网页爬虫: 自动爬取GWOSC事件列表和32sec 16KHz的txt数据文件
    2. 数据处理: 进行FFT、功率谱密度、峰值检测等分析
    3. 数据存储: 使用本地文件存储事件信息和文件记录
    4. Web可视化: 提供交互式网页界面展示分析结果
    5. 桌面GUI: 提供Tkinter图形界面应用
    6. 异常处理: 完善的错误处理和日志记录机制
"""
    print(help_text)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="引力波数据爬虫与可视化系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --web                    # 启动Web应用
  python main.py --gui                    # 启动GUI应用
  python main.py --crawl                  # 爬取事件列表
  python main.py --download GW150914      # 下载GW150914事件数据
  python main.py --analyze GW150914       # 分析GW150914事件数据
        """
    )
    
    parser.add_argument('-w', '--web', action='store_true',
                       help='启动Web应用')
    parser.add_argument('-g', '--gui', action='store_true',
                       help='启动GUI应用')
    parser.add_argument('-c', '--crawl', nargs='?', const=None, type=int,
                       metavar='LIMIT', help='运行爬虫获取事件列表')
    parser.add_argument('-d', '--download', metavar='EVENT',
                       help='下载指定事件的数据')
    parser.add_argument('-a', '--analyze', metavar='EVENT',
                       help='分析指定事件的数据')
    parser.add_argument('-l', '--list', action='store_true',
                       help='列出所有事件')
    parser.add_argument('-i', '--info', metavar='EVENT',
                       help='显示事件详细信息')
    parser.add_argument('-s', '--setup', action='store_true',
                       help='设置运行环境')
    
    args = parser.parse_args()
    
    # 如果没有参数，显示帮助
    if len(sys.argv) == 1:
        show_help()
        return
    
    # 设置环境
    if not setup_environment():
        logger.error("环境设置失败，程序退出")
        return
    
    try:
        # 处理各种选项
        if args.web:
            run_web_app()
        elif args.gui:
            run_gui_app()
        elif args.crawl is not None:
            run_crawler(limit=args.crawl)
        elif args.download:
            download_event(args.download)
        elif args.analyze:
            analyze_event(args.analyze)
        elif args.list:
            list_events()
        elif args.info:
            show_event_info(args.info)
        elif args.setup:
            logger.info("环境设置完成")
        else:
            show_help()
            
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行失败: {e}")

if __name__ == '__main__':
    main() 
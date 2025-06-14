#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
from image_crawler import ImageCrawler
from image_processor import ImageProcessor
from image_viewer import ImageManager

def test_image_crawler():
    """测试图片爬虫"""
    print("=== 测试图片爬虫 ===")
    
    # 创建爬虫实例（限制数量为5张用于测试）
    crawler = ImageCrawler(save_dir="test_images", max_images=5)
    
    # 测试单个图片下载
    test_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400&h=300&fit=crop"
    print(f"测试下载图片: {test_url}")
    
    result = crawler.download_image(test_url)
    if result:
        print(f"下载成功: {result}")
    else:
        print("下载失败")
    
    # 测试图片处理
    print("\n=== 测试图片处理 ===")
    processor = ImageProcessor(input_dir="test_images/raw", output_dir="test_images/processed")
    
    # 检查是否有图片可以处理
    if os.path.exists("test_images/raw"):
        files = os.listdir("test_images/raw")
        if files:
            print(f"找到 {len(files)} 个文件进行测试处理")
            # 只处理第一个文件
            test_file = files[0]
            input_path = os.path.join("test_images/raw", test_file)
            output_path = os.path.join("test_images/processed", f"test_{test_file}")
            
            success = processor.process_single_image(input_path, output_path, 
                                                   operations=['resize', 'enhance_contrast'])
            if success:
                print(f"图片处理成功: {output_path}")
            else:
                print("图片处理失败")
        else:
            print("没有找到图片文件")
    else:
        print("原始图片目录不存在")
    
    # 测试图片管理器
    print("\n=== 测试图片管理器 ===")
    manager = ImageManager(images_dir="test_images")
    stats = manager.get_image_stats()
    
    print(f"原始图片数量: {stats['raw_count']}")
    print(f"处理后图片数量: {stats['processed_count']}")
    print(f"总文件大小: {stats['total_size'] / 1024:.2f} KB")

def test_image_processor():
    """测试图片处理器"""
    print("\n=== 测试图片处理器功能 ===")
    
    processor = ImageProcessor()
    
    # 测试各种处理操作
    print("可用的处理操作:")
    operations = [
        'resize', 'enhance_contrast', 'enhance_sharpness', 'enhance_brightness',
        'gaussian_blur', 'edge_enhancement', 'grayscale', 'sepia', 'vintage',
        'edge_detection', 'watermark'
    ]
    
    for op in operations:
        print(f"  - {op}")
    
    # 测试统计功能
    stats = processor.get_processing_stats()
    print(f"\n处理统计: {stats}")

def cleanup_test_files():
    """清理测试文件"""
    import shutil
    
    test_dir = "test_images"
    if os.path.exists(test_dir):
        print(f"\n清理测试目录: {test_dir}")
        shutil.rmtree(test_dir)

def main():
    """主测试函数"""
    print("开始测试图片爬取系统...")
    
    try:
        # 测试图片爬虫
        test_image_crawler()
        
        # 测试图片处理器
        test_image_processor()
        
        print("\n=== 测试完成 ===")
        print("所有模块导入和基本功能测试通过！")
        
        # 询问是否清理测试文件
        response = input("\n是否清理测试文件？(y/n): ")
        if response.lower() == 'y':
            cleanup_test_files()
        else:
            print("测试文件保留在 test_images/ 目录中")
            
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
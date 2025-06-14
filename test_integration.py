#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import requests
import time

def test_web_app():
    """测试Web应用是否正常运行"""
    print("=== 测试Web应用集成 ===")
    
    try:
        # 测试主页
        print("测试主页...")
        response = requests.get("http://localhost:5000/", timeout=10)
        if response.status_code == 200:
            print("✓ 主页访问成功")
        else:
            print(f"✗ 主页访问失败: {response.status_code}")
            return False
        
        # 测试图片相关页面
        print("测试图片库页面...")
        response = requests.get("http://localhost:5000/images", timeout=10)
        if response.status_code == 200:
            print("✓ 图片库页面访问成功")
        else:
            print(f"✗ 图片库页面访问失败: {response.status_code}")
        
        print("测试图片爬取页面...")
        response = requests.get("http://localhost:5000/images/crawl", timeout=10)
        if response.status_code == 200:
            print("✓ 图片爬取页面访问成功")
        else:
            print(f"✗ 图片爬取页面访问失败: {response.status_code}")
        
        print("测试图片处理页面...")
        response = requests.get("http://localhost:5000/images/process", timeout=10)
        if response.status_code == 200:
            print("✓ 图片处理页面访问成功")
        else:
            print(f"✗ 图片处理页面访问失败: {response.status_code}")
        
        print("测试图片查看器页面...")
        response = requests.get("http://localhost:5000/images/viewer", timeout=10)
        if response.status_code == 200:
            print("✓ 图片查看器页面访问成功")
        else:
            print(f"✗ 图片查看器页面访问失败: {response.status_code}")
        
        # 测试API
        print("测试图片统计API...")
        response = requests.get("http://localhost:5000/api/images/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✓ 图片统计API访问成功")
                print(f"  原始图片: {data['stats']['raw_count']}")
                print(f"  处理后图片: {data['stats']['processed_count']}")
            else:
                print(f"✗ 图片统计API返回错误: {data.get('error')}")
        else:
            print(f"✗ 图片统计API访问失败: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到Web应用，请确保应用正在运行")
        return False
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {str(e)}")
        return False

def test_modules():
    """测试模块导入"""
    print("\n=== 测试模块导入 ===")
    
    try:
        from image_crawler import ImageCrawler
        print("✓ ImageCrawler 导入成功")
    except ImportError as e:
        print(f"✗ ImageCrawler 导入失败: {e}")
    
    try:
        from image_processor import ImageProcessor
        print("✓ ImageProcessor 导入成功")
    except ImportError as e:
        print(f"✗ ImageProcessor 导入失败: {e}")
    
    try:
        from image_viewer import ImageManager
        print("✓ ImageManager 导入成功")
    except ImportError as e:
        print(f"✗ ImageManager 导入失败: {e}")

def test_directories():
    """测试目录结构"""
    print("\n=== 测试目录结构 ===")
    
    # 检查图片目录
    if os.path.exists("images"):
        print("✓ images 目录存在")
        if os.path.exists("images/raw"):
            print("✓ images/raw 目录存在")
        else:
            print("✗ images/raw 目录不存在")
        if os.path.exists("images/processed"):
            print("✓ images/processed 目录存在")
        else:
            print("✗ images/processed 目录不存在")
    else:
        print("✗ images 目录不存在")
    
    # 检查模板文件
    templates = [
        "templates/images.html",
        "templates/images_crawl.html", 
        "templates/images_process.html",
        "templates/images_viewer.html"
    ]
    
    for template in templates:
        if os.path.exists(template):
            print(f"✓ {template} 存在")
        else:
            print(f"✗ {template} 不存在")

def main():
    """主测试函数"""
    print("开始测试引力波数据系统集成...")
    
    # 测试模块导入
    test_modules()
    
    # 测试目录结构
    test_directories()
    
    # 测试Web应用
    print("\n请确保Web应用正在运行 (python web_app.py)")
    input("按回车键继续测试Web应用...")
    
    test_web_app()
    
    print("\n=== 测试完成 ===")
    print("如果所有测试都通过，说明集成成功！")
    print("您可以访问 http://localhost:5000 查看完整的Web应用")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
import threading

class ImageSystemGUI:
    """图片系统图形界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("引力波图片爬取系统")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="引力波图片爬取和可视化系统", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 功能按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.BOTH, expand=True)
        
        # 爬取图片按钮
        crawl_btn = ttk.Button(button_frame, text="🕷️ 爬取图片", 
                              command=self.start_crawling, style="Action.TButton")
        crawl_btn.pack(fill=tk.X, pady=5)
        
        # 查看图片按钮
        view_btn = ttk.Button(button_frame, text="🖼️ 查看图片", 
                             command=self.start_viewer, style="Action.TButton")
        view_btn.pack(fill=tk.X, pady=5)
        
        # 图片处理按钮
        process_btn = ttk.Button(button_frame, text="⚙️ 图片处理", 
                                command=self.start_processing, style="Action.TButton")
        process_btn.pack(fill=tk.X, pady=5)
        
        # 统计信息按钮
        stats_btn = ttk.Button(button_frame, text="📊 统计信息", 
                              command=self.show_stats, style="Action.TButton")
        stats_btn.pack(fill=tk.X, pady=5)
        
        # 导出数据按钮
        export_btn = ttk.Button(button_frame, text="📤 导出数据", 
                               command=self.export_data, style="Action.TButton")
        export_btn.pack(fill=tk.X, pady=5)
        
        # 设置按钮
        settings_btn = ttk.Button(button_frame, text="⚙️ 设置", 
                                 command=self.show_settings, style="Action.TButton")
        settings_btn.pack(fill=tk.X, pady=5)
        
        # 帮助按钮
        help_btn = ttk.Button(button_frame, text="❓ 帮助", 
                             command=self.show_help, style="Action.TButton")
        help_btn.pack(fill=tk.X, pady=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(20, 0))
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # 日志文本框
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 配置样式
        style = ttk.Style()
        style.configure("Action.TButton", font=("Arial", 12), padding=10)
        
    def log_message(self, message):
        """添加日志消息"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def start_crawling(self):
        """开始爬取图片"""
        self.status_var.set("正在爬取图片...")
        self.log_message("开始爬取引力波相关图片...")
        
        def crawl_thread():
            try:
                # 运行爬取命令
                result = subprocess.run([
                    sys.executable, "image_main.py", "crawl", 
                    "--max-images", "50"  # 限制数量用于演示
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    self.log_message("图片爬取完成！")
                    self.status_var.set("爬取完成")
                    messagebox.showinfo("完成", "图片爬取完成！")
                else:
                    self.log_message(f"爬取失败: {result.stderr}")
                    self.status_var.set("爬取失败")
                    messagebox.showerror("错误", f"爬取失败: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                self.log_message("爬取超时")
                self.status_var.set("爬取超时")
                messagebox.showwarning("警告", "爬取操作超时")
            except Exception as e:
                self.log_message(f"发生错误: {str(e)}")
                self.status_var.set("发生错误")
                messagebox.showerror("错误", f"发生错误: {str(e)}")
        
        # 在新线程中运行爬取
        thread = threading.Thread(target=crawl_thread)
        thread.daemon = True
        thread.start()
        
    def start_viewer(self):
        """启动图片查看器"""
        self.status_var.set("启动图片查看器...")
        self.log_message("启动图片查看器...")
        
        def viewer_thread():
            try:
                subprocess.run([sys.executable, "image_main.py", "view"], 
                             timeout=30)
            except subprocess.TimeoutExpired:
                pass
            except Exception as e:
                self.log_message(f"查看器启动失败: {str(e)}")
                messagebox.showerror("错误", f"查看器启动失败: {str(e)}")
        
        thread = threading.Thread(target=viewer_thread)
        thread.daemon = True
        thread.start()
        
    def start_processing(self):
        """开始图片处理"""
        self.status_var.set("正在处理图片...")
        self.log_message("开始图片处理...")
        
        def process_thread():
            try:
                from image_processor import ImageProcessor
                
                processor = ImageProcessor()
                processor.batch_process(operations=['resize', 'enhance_contrast', 'enhance_sharpness'])
                
                self.log_message("图片处理完成！")
                self.status_var.set("处理完成")
                messagebox.showinfo("完成", "图片处理完成！")
                
            except Exception as e:
                self.log_message(f"处理失败: {str(e)}")
                self.status_var.set("处理失败")
                messagebox.showerror("错误", f"处理失败: {str(e)}")
        
        thread = threading.Thread(target=process_thread)
        thread.daemon = True
        thread.start()
        
    def show_stats(self):
        """显示统计信息"""
        try:
            from image_viewer import ImageManager
            
            manager = ImageManager()
            stats = manager.get_image_stats()
            
            stats_text = f"""
图片统计信息:
- 原始图片数量: {stats['raw_count']}
- 处理后图片数量: {stats['processed_count']}
- 总文件大小: {stats['total_size'] / 1024 / 1024:.2f} MB
"""
            
            if stats['metadata']:
                metadata = stats['metadata']
                stats_text += f"""
元数据信息:
- 总下载数量: {metadata.get('total_downloaded', 0)}
- 成功下载: {len(metadata.get('successful_urls', []))}
- 失败下载: {len(metadata.get('failed_urls', []))}
"""
            
            self.log_message(stats_text)
            messagebox.showinfo("统计信息", stats_text)
            
        except Exception as e:
            self.log_message(f"获取统计信息失败: {str(e)}")
            messagebox.showerror("错误", f"获取统计信息失败: {str(e)}")
    
    def export_data(self):
        """导出数据"""
        try:
            from image_viewer import ImageManager
            
            manager = ImageManager()
            output_path = "image_metadata_export.json"
            manager.export_metadata(output_path)
            
            self.log_message(f"数据已导出到: {output_path}")
            messagebox.showinfo("完成", f"数据已导出到: {output_path}")
            
        except Exception as e:
            self.log_message(f"导出失败: {str(e)}")
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def show_settings(self):
        """显示设置"""
        settings_text = """
系统设置:
- 图片保存目录: images/
- 最大图片数量: 500
- 图片格式: JPG, PNG, GIF, BMP, TIFF, WebP
- 处理质量: 85%

搜索关键词:
- 引力波 gravitational wave
- 太极计划 Taiji program
- LIGO gravitational wave detector
- 等等...
"""
        self.log_message(settings_text)
        messagebox.showinfo("设置", settings_text)
    
    def show_help(self):
        """显示帮助"""
        help_text = """
使用说明:

1. 爬取图片: 从网络爬取引力波相关图片
2. 查看图片: 启动图形界面查看器
3. 图片处理: 批量处理下载的图片
4. 统计信息: 查看图片统计和元数据
5. 导出数据: 导出图片元数据
6. 设置: 查看系统配置

快捷键:
- 查看器中: ←→ 切换图片, ↑↓ 缩放, Esc 重置

注意事项:
- 确保网络连接稳定
- 图片处理可能需要较长时间
- 遵守相关网站使用条款
"""
        self.log_message(help_text)
        messagebox.showinfo("帮助", help_text)

def main():
    """主函数"""
    root = tk.Tk()
    app = ImageSystemGUI(root)
    
    # 显示欢迎消息
    app.log_message("欢迎使用引力波图片爬取系统！")
    app.log_message("请选择要执行的操作...")
    
    root.mainloop()

if __name__ == "__main__":
    main() 
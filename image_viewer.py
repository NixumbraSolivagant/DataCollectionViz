import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import json
import threading
from datetime import datetime

class ImageViewer:
    def __init__(self, root, images_dir="images"):
        self.root = root
        self.images_dir = images_dir
        self.current_index = 0
        self.image_files = []
        self.current_mode = "processed"  # "raw" or "processed"
        
        self.setup_ui()
        self.load_images()
        
    def setup_ui(self):
        """设置用户界面"""
        self.root.title("引力波图片查看器")
        self.root.geometry("1000x700")
        
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 模式选择
        ttk.Label(control_frame, text="图片模式:").pack(side=tk.LEFT, padx=(0, 5))
        self.mode_var = tk.StringVar(value="processed")
        mode_combo = ttk.Combobox(control_frame, textvariable=self.mode_var, 
                                 values=["raw", "processed"], state="readonly", width=10)
        mode_combo.pack(side=tk.LEFT, padx=(0, 10))
        mode_combo.bind("<<ComboboxSelected>>", self.on_mode_change)
        
        # 刷新按钮
        ttk.Button(control_frame, text="刷新", command=self.refresh_images).pack(side=tk.LEFT, padx=(0, 10))
        
        # 统计信息
        self.stats_label = ttk.Label(control_frame, text="")
        self.stats_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 图片信息
        self.info_label = ttk.Label(control_frame, text="")
        self.info_label.pack(side=tk.RIGHT)
        
        # 图片显示区域
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(fill=tk.BOTH, expand=True)
        
        # 图片画布
        self.canvas = tk.Canvas(image_frame, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        v_scrollbar = ttk.Scrollbar(image_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar = ttk.Scrollbar(image_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 导航按钮
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(nav_frame, text="上一张", command=self.prev_image).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(nav_frame, text="下一张", command=self.next_image).pack(side=tk.LEFT, padx=(0, 5))
        
        # 缩放控制
        ttk.Label(nav_frame, text="缩放:").pack(side=tk.LEFT, padx=(20, 5))
        self.zoom_var = tk.DoubleVar(value=1.0)
        zoom_scale = ttk.Scale(nav_frame, from_=0.1, to=3.0, variable=self.zoom_var, 
                              orient=tk.HORIZONTAL, length=200)
        zoom_scale.pack(side=tk.LEFT, padx=(0, 10))
        zoom_scale.bind("<ButtonRelease-1>", self.on_zoom_change)
        
        # 键盘绑定
        self.root.bind("<Left>", lambda e: self.prev_image())
        self.root.bind("<Right>", lambda e: self.next_image())
        self.root.bind("<Up>", lambda e: self.zoom_in())
        self.root.bind("<Down>", lambda e: self.zoom_out())
        self.root.bind("<Escape>", lambda e: self.reset_zoom())
        
    def load_images(self):
        """加载图片列表"""
        self.image_files = []
        
        # 确定图片目录
        if self.current_mode == "processed":
            image_dir = os.path.join(self.images_dir, "processed")
        else:
            image_dir = os.path.join(self.images_dir, "raw")
        
        if not os.path.exists(image_dir):
            self.stats_label.config(text="图片目录不存在")
            return
        
        # 获取所有图片文件
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        for filename in os.listdir(image_dir):
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                self.image_files.append(os.path.join(image_dir, filename))
        
        self.image_files.sort()
        self.current_index = 0
        
        # 更新统计信息
        self.update_stats()
        
        # 显示第一张图片
        if self.image_files:
            self.show_current_image()
        else:
            self.stats_label.config(text="没有找到图片")
    
    def update_stats(self):
        """更新统计信息"""
        total = len(self.image_files)
        current = self.current_index + 1 if self.image_files else 0
        self.stats_label.config(text=f"图片 {current}/{total} ({self.current_mode}模式)")
    
    def show_current_image(self):
        """显示当前图片"""
        if not self.image_files or self.current_index >= len(self.image_files):
            return
        
        try:
            # 加载图片
            image_path = self.image_files[self.current_index]
            with Image.open(image_path) as img:
                # 获取原始尺寸
                original_width, original_height = img.size
                
                # 计算显示尺寸
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                
                if canvas_width <= 1 or canvas_height <= 1:
                    # 如果画布尺寸还未确定，使用默认尺寸
                    canvas_width, canvas_height = 800, 600
                
                # 计算缩放比例
                scale_x = canvas_width / original_width
                scale_y = canvas_height / original_height
                scale = min(scale_x, scale_y) * self.zoom_var.get()
                
                # 调整图片大小
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 转换为PhotoImage
                self.photo = ImageTk.PhotoImage(img)
                
                # 清除画布
                self.canvas.delete("all")
                
                # 在画布中央显示图片
                x = (canvas_width - new_width) // 2
                y = (canvas_height - new_height) // 2
                self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
                
                # 更新画布滚动区域
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
                
                # 更新信息标签
                filename = os.path.basename(image_path)
                file_size = os.path.getsize(image_path) / 1024  # KB
                self.info_label.config(text=f"{filename} | {original_width}x{original_height} | {file_size:.1f}KB")
                
        except Exception as e:
            messagebox.showerror("错误", f"无法加载图片: {str(e)}")
    
    def prev_image(self):
        """显示上一张图片"""
        if self.image_files and self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()
            self.update_stats()
    
    def next_image(self):
        """显示下一张图片"""
        if self.image_files and self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.show_current_image()
            self.update_stats()
    
    def zoom_in(self):
        """放大"""
        self.zoom_var.set(min(3.0, self.zoom_var.get() + 0.1))
        self.show_current_image()
    
    def zoom_out(self):
        """缩小"""
        self.zoom_var.set(max(0.1, self.zoom_var.get() - 0.1))
        self.show_current_image()
    
    def reset_zoom(self):
        """重置缩放"""
        self.zoom_var.set(1.0)
        self.show_current_image()
    
    def on_zoom_change(self, event=None):
        """缩放改变事件"""
        self.show_current_image()
    
    def on_mode_change(self, event=None):
        """模式改变事件"""
        self.current_mode = self.mode_var.get()
        self.load_images()
    
    def refresh_images(self):
        """刷新图片列表"""
        self.load_images()

class ImageManager:
    """图片管理器"""
    def __init__(self, images_dir="images"):
        self.images_dir = images_dir
        
    def get_image_stats(self):
        """获取图片统计信息"""
        stats = {
            'raw_count': 0,
            'processed_count': 0,
            'total_size': 0,
            'metadata': None
        }
        
        # 统计原始图片
        raw_dir = os.path.join(self.images_dir, "raw")
        if os.path.exists(raw_dir):
            for filename in os.listdir(raw_dir):
                filepath = os.path.join(raw_dir, filename)
                if os.path.isfile(filepath):
                    stats['raw_count'] += 1
                    stats['total_size'] += os.path.getsize(filepath)
        
        # 统计处理后的图片
        processed_dir = os.path.join(self.images_dir, "processed")
        if os.path.exists(processed_dir):
            for filename in os.listdir(processed_dir):
                filepath = os.path.join(processed_dir, filename)
                if os.path.isfile(filepath):
                    stats['processed_count'] += 1
                    stats['total_size'] += os.path.getsize(filepath)
        
        # 读取元数据
        metadata_path = os.path.join(self.images_dir, 'metadata.json')
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    stats['metadata'] = json.load(f)
            except:
                pass
        
        return stats
    
    def cleanup_duplicates(self):
        """清理重复图片"""
        # 这里可以实现重复图片检测和清理逻辑
        pass
    
    def export_metadata(self, output_path):
        """导出元数据"""
        stats = self.get_image_stats()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

def main():
    """主函数"""
    root = tk.Tk()
    app = ImageViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main() 
import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import json
from datetime import datetime
import logging

class ImageProcessor:
    """图片处理工具类"""
    
    def __init__(self, input_dir="images/raw", output_dir="images/processed"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processed_count = 0
        self.failed_count = 0
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def resize_image(self, image, max_size=(800, 600)):
        """调整图片大小"""
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        return image
    
    def enhance_contrast(self, image, factor=1.2):
        """增强对比度"""
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)
    
    def enhance_sharpness(self, image, factor=1.1):
        """增强锐度"""
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(factor)
    
    def enhance_brightness(self, image, factor=1.05):
        """增强亮度"""
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)
    
    def apply_gaussian_blur(self, image, radius=0.5):
        """应用高斯模糊"""
        return image.filter(ImageFilter.GaussianBlur(radius=radius))
    
    def apply_edge_enhancement(self, image):
        """边缘增强"""
        return image.filter(ImageFilter.EDGE_ENHANCE)
    
    def convert_to_grayscale(self, image):
        """转换为灰度图"""
        return image.convert('L')
    
    def apply_sepia_filter(self, image):
        """应用复古滤镜"""
        # 转换为RGB模式
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 应用复古效果
        width, height = image.size
        pixels = image.load()
        
        for x in range(width):
            for y in range(height):
                r, g, b = pixels[x, y]
                
                # 复古色调转换
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                
                pixels[x, y] = (min(255, tr), min(255, tg), min(255, tb))
        
        return image
    
    def apply_vintage_filter(self, image):
        """应用复古滤镜（另一种方法）"""
        # 转换为RGB模式
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 调整色调
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(0.8)
        
        # 调整饱和度
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.2)
        
        return image
    
    def detect_edges(self, image):
        """边缘检测"""
        # 转换为灰度图
        if image.mode != 'L':
            image = image.convert('L')
        
        # 使用Canny边缘检测
        img_array = np.array(image)
        edges = cv2.Canny(img_array, 100, 200)
        
        return Image.fromarray(edges)
    
    def create_watermark(self, image, text="GWOSC"):
        """添加水印"""
        from PIL import ImageDraw, ImageFont
        
        # 创建可绘制的图片副本
        watermarked = image.copy()
        draw = ImageDraw.Draw(watermarked)
        
        # 尝试使用系统字体
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
        
        # 获取图片尺寸
        width, height = image.size
        
        # 计算水印位置（右下角）
        text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else font.getsize(text)
        x = width - text_width - 10
        y = height - text_height - 10
        
        # 绘制半透明水印
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 128))
        
        return watermarked
    
    def process_single_image(self, input_path, output_path, operations=None):
        """处理单张图片"""
        try:
            with Image.open(input_path) as img:
                # 默认操作
                if operations is None:
                    operations = ['resize', 'enhance_contrast', 'enhance_sharpness']
                
                # 执行操作
                for operation in operations:
                    if operation == 'resize':
                        img = self.resize_image(img)
                    elif operation == 'enhance_contrast':
                        img = self.enhance_contrast(img)
                    elif operation == 'enhance_sharpness':
                        img = self.enhance_sharpness(img)
                    elif operation == 'enhance_brightness':
                        img = self.enhance_brightness(img)
                    elif operation == 'gaussian_blur':
                        img = self.apply_gaussian_blur(img)
                    elif operation == 'edge_enhancement':
                        img = self.apply_edge_enhancement(img)
                    elif operation == 'grayscale':
                        img = self.convert_to_grayscale(img)
                    elif operation == 'sepia':
                        img = self.apply_sepia_filter(img)
                    elif operation == 'vintage':
                        img = self.apply_vintage_filter(img)
                    elif operation == 'edge_detection':
                        img = self.detect_edges(img)
                    elif operation == 'watermark':
                        img = self.create_watermark(img)
                
                # 保存处理后的图片
                img.save(output_path, 'JPEG', quality=85)
                
                self.processed_count += 1
                self.logger.info(f"处理完成: {os.path.basename(input_path)}")
                return True
                
        except Exception as e:
            self.logger.error(f"处理失败 {input_path}: {str(e)}")
            self.failed_count += 1
            return False
    
    def batch_process(self, operations=None, file_pattern=None):
        """批量处理图片"""
        self.logger.info("开始批量处理图片...")
        
        if not os.path.exists(self.input_dir):
            self.logger.error(f"输入目录不存在: {self.input_dir}")
            return
        
        # 获取所有图片文件
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        image_files = []
        
        for filename in os.listdir(self.input_dir):
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                if file_pattern is None or file_pattern in filename:
                    image_files.append(filename)
        
        self.logger.info(f"找到 {len(image_files)} 张图片需要处理")
        
        # 处理每张图片
        for filename in image_files:
            input_path = os.path.join(self.input_dir, filename)
            output_filename = f"processed_{filename}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            self.process_single_image(input_path, output_path, operations)
        
        self.logger.info(f"批量处理完成！成功: {self.processed_count}, 失败: {self.failed_count}")
    
    def create_thumbnail(self, input_path, output_path, size=(200, 150)):
        """创建缩略图"""
        try:
            with Image.open(input_path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(output_path, 'JPEG', quality=85)
            return True
        except Exception as e:
            self.logger.error(f"创建缩略图失败 {input_path}: {str(e)}")
            return False
    
    def batch_create_thumbnails(self, size=(200, 150)):
        """批量创建缩略图"""
        thumbnails_dir = os.path.join(self.output_dir, "thumbnails")
        os.makedirs(thumbnails_dir, exist_ok=True)
        
        self.logger.info("开始创建缩略图...")
        
        if not os.path.exists(self.input_dir):
            self.logger.error(f"输入目录不存在: {self.input_dir}")
            return
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        count = 0
        
        for filename in os.listdir(self.input_dir):
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                input_path = os.path.join(self.input_dir, filename)
                output_filename = f"thumb_{filename}"
                output_path = os.path.join(thumbnails_dir, output_filename)
                
                if self.create_thumbnail(input_path, output_path, size):
                    count += 1
        
        self.logger.info(f"缩略图创建完成！共创建 {count} 张缩略图")
    
    def get_processing_stats(self):
        """获取处理统计信息"""
        return {
            'processed_count': self.processed_count,
            'failed_count': self.failed_count,
            'success_rate': self.processed_count / (self.processed_count + self.failed_count) if (self.processed_count + self.failed_count) > 0 else 0
        }

def main():
    """主函数 - 演示用法"""
    processor = ImageProcessor()
    
    # 基本处理
    print("执行基本图片处理...")
    processor.batch_process(operations=['resize', 'enhance_contrast', 'enhance_sharpness'])
    
    # 创建缩略图
    print("创建缩略图...")
    processor.batch_create_thumbnails()
    
    # 显示统计信息
    stats = processor.get_processing_stats()
    print(f"处理统计: {stats}")

if __name__ == "__main__":
    main() 
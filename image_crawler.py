import os
import requests
import time
import random
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import hashlib
from PIL import Image, ImageEnhance, ImageFilter
import io
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

class ImageCrawler:
    def __init__(self, save_dir="images", max_images=500, api_key=None):
        self.save_dir = save_dir
        self.max_images = max_images
        self.downloaded_count = 0
        self.failed_urls = []
        self.successful_urls = []
        self.api_key = api_key
        
        # 创建保存目录
        os.makedirs(save_dir, exist_ok=True)
        os.makedirs(os.path.join(save_dir, "raw"), exist_ok=True)
        os.makedirs(os.path.join(save_dir, "processed"), exist_ok=True)
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('image_crawler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 用户代理列表
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101'
        ]
        
        # 搜索关键词
        self.keywords = ["爱党", "爱国", "文化自信"]
        
        # 图片扩展名
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        
        # 图片源网站
        self.image_sources = {
            'baidu': 'https://image.baidu.com/search/index?tn=baiduimage&word={}',
            'sogou': 'https://pic.sogou.com/pics?query={}',
            '360': 'https://image.so.com/i?q={}',
            'bing': 'https://cn.bing.com/images/search?q={}'
        }
        
    def get_random_user_agent(self):
        return random.choice(self.user_agents)
    
    def get_headers(self):
        return {
            'Authorization': self.api_key,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        }
    
    def is_valid_image_url(self, url):
        """检查URL是否为有效的图片链接"""
        if not url:
            self.logger.debug("URL为空")
            return False
        
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            self.logger.debug(f"无效的URL格式: {url}")
            return False
            
        path = parsed.path.lower()
        is_valid = any(path.endswith(ext) for ext in self.image_extensions)
        if not is_valid:
            self.logger.debug(f"URL不是图片格式: {url}")
        return is_valid
    
    def download_image(self, url, filename=None):
        """下载单张图片"""
        try:
            if not filename:
                # 生成文件名
                url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
                parsed_url = urlparse(url)
                ext = os.path.splitext(parsed_url.path)[1]
                if not ext or ext.lower() not in self.image_extensions:
                    ext = '.jpg'
                filename = f"{url_hash}{ext}"
            
            filepath = os.path.join(self.save_dir, "raw", filename)
            
            # 检查文件是否已存在
            if os.path.exists(filepath):
                self.logger.info(f"图片已存在: {filename}")
                return filepath
            
            response = requests.get(url, headers=self.get_headers(), timeout=30)
            response.raise_for_status()
            
            # 检查内容类型
            content_type = response.headers.get('content-type', '').lower()
            if not any(img_type in content_type for img_type in ['image/', 'jpeg', 'png', 'gif']):
                self.logger.warning(f"非图片内容: {url}")
                return None
            
            # 保存图片
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"成功下载: {filename} from {url}")
            self.successful_urls.append(url)
            self.downloaded_count += 1
            return filepath
            
        except Exception as e:
            self.logger.error(f"下载失败 {url}: {str(e)}")
            self.failed_urls.append(url)
            return None
    
    def process_image(self, input_path, output_path):
        """处理图片：调整大小、增强对比度、锐化"""
        try:
            with Image.open(input_path) as img:
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 调整大小，保持宽高比
                max_size = (800, 600)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # 增强对比度
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.2)
                
                # 增强锐度
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.1)
                
                # 保存处理后的图片
                img.save(output_path, 'JPEG', quality=85)
                
            return True
            
        except Exception as e:
            self.logger.error(f"图片处理失败 {input_path}: {str(e)}")
            return False
    
    def process_all_images(self):
        """处理所有下载的图片"""
        self.logger.info("开始处理图片...")
        
        raw_dir = os.path.join(self.save_dir, "raw")
        processed_dir = os.path.join(self.save_dir, "processed")
        
        processed_count = 0
        
        for filename in os.listdir(raw_dir):
            if processed_count >= self.max_images:
                break
                
            input_path = os.path.join(raw_dir, filename)
            output_filename = f"processed_{filename}"
            output_path = os.path.join(processed_dir, output_filename)
            
            if self.process_image(input_path, output_path):
                processed_count += 1
                self.logger.info(f"处理完成: {output_filename}")
        
        self.logger.info(f"图片处理完成，共处理 {processed_count} 张图片")
        return processed_count
    
    def save_metadata(self):
        """保存元数据"""
        metadata = {
            'total_downloaded': self.downloaded_count,
            'successful_urls': self.successful_urls,
            'failed_urls': self.failed_urls,
            'timestamp': time.time()
        }
        
        metadata_path = os.path.join(self.save_dir, 'metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"元数据已保存到: {metadata_path}")
    
    def crawl_images(self):
        """开始爬取图片"""
        self.logger.info("开始爬取图片...")
        
        try:
            for keyword in self.keywords:
                if self.downloaded_count >= self.max_images:
                    break
                self.logger.info(f"搜索关键词: {keyword}")
                page = 1
                per_page = 80
                while self.downloaded_count < self.max_images:
                    search_url = f"https://api.pexels.com/v1/search?query={keyword}&per_page={per_page}&page={page}"
                    response = requests.get(search_url, headers=self.get_headers(), timeout=30)
                    if response.status_code != 200:
                        self.logger.warning(f"Pexels API请求失败: {response.status_code}")
                        break
                    data = response.json()
                    photos = data.get('photos', [])
                    if not photos:
                        break
                    for photo in photos:
                        if self.downloaded_count >= self.max_images:
                            break
                        src = photo.get('src', {}).get('large2x') or photo.get('src', {}).get('large')
                        if src and self.is_valid_image_url(src):
                            self.download_image(src)
                            time.sleep(random.uniform(0.5, 1.2))
                    page += 1
            
            self.logger.info("开始处理图片...")
            raw_dir = os.path.join(self.save_dir, "raw")
            processed_dir = os.path.join(self.save_dir, "processed")
            
            processed_count = 0
            for filename in os.listdir(raw_dir):
                if filename.lower().endswith(tuple(self.image_extensions)):
                    input_path = os.path.join(raw_dir, filename)
                    output_path = os.path.join(processed_dir, filename)
                    if self.process_image(input_path, output_path):
                        processed_count += 1
            
            self.logger.info(f"图片处理完成，共处理 {processed_count} 张图片")
        
            # 保存元数据
            self.save_metadata()
        
            self.logger.info(f"爬取完成！共下载 {self.downloaded_count} 张图片")
            self.logger.info(f"成功: {len(self.successful_urls)}, 失败: {len(self.failed_urls)}")
        
        except Exception as e:
            self.logger.error(f"爬取过程出错: {str(e)}")

def main():
    """主函数"""
    api_key = "1jLTRhpcXAgr15WUa5scpuwqDjIEHWAD1c4Q3Ulf40Y7OZEZPaiLPFHG"  # 已自动填入你的Pexels API Key
    crawler = ImageCrawler(max_images=500, api_key=api_key)
    crawler.crawl_images()

if __name__ == "__main__":
    main() 
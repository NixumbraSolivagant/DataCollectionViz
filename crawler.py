import requests
import json
import os
import time
import logging
import gzip
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from config import (
    GWOSC_BASE_URL, GWOSC_DATA_URL, GWOSC_DOWNLOAD_BASE,
    REQUEST_TIMEOUT, MAX_RETRIES, CHUNK_SIZE, DATA_DIR
)
from database import DataManager

logger = logging.getLogger(__name__)

class GWOSCCrawler:
    """GWOSC数据爬虫类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.db = DataManager()
    
    def get_events_list(self):
        """获取事件列表 - 使用JSON API"""
        try:
            logger.info("开始获取事件列表...")
            
            response = self.session.get(GWOSC_DATA_URL, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            events_data = response.json()
            
            if 'events' in events_data:
                events = events_data['events']
                logger.info(f"成功获取 {len(events)} 个事件")
                return self._parse_events_data(events)
            
            logger.warning("未找到events数据")
            return []
            
        except Exception as e:
            logger.error(f"获取事件列表失败: {e}")
            return []
    
    def _parse_events_data(self, events_data):
        """解析事件数据"""
        parsed_events = []
        
        for event_id, event_info in events_data.items():
            try:
                # 解析基本信息
                event_data = {
                    'event_id': event_id,
                    'common_name': event_info.get('commonName'),
                    'version': event_info.get('version'),
                    'catalog': event_info.get('catalog.shortName'),
                    'gps_time': event_info.get('GPS'),
                    'gracedb_id': event_info.get('gracedb_id'),
                    'reference': event_info.get('reference'),
                    'json_url': event_info.get('jsonurl'),
                    
                    # 物理参数
                    'mass_1_source': event_info.get('mass_1_source'),
                    'mass_1_source_lower': event_info.get('mass_1_source_lower'),
                    'mass_1_source_upper': event_info.get('mass_1_source_upper'),
                    'mass_1_source_unit': event_info.get('mass_1_source_unit'),
                    
                    'mass_2_source': event_info.get('mass_2_source'),
                    'mass_2_source_lower': event_info.get('mass_2_source_lower'),
                    'mass_2_source_upper': event_info.get('mass_2_source_upper'),
                    'mass_2_source_unit': event_info.get('mass_2_source_unit'),
                    
                    'network_matched_filter_snr': event_info.get('network_matched_filter_snr'),
                    'network_matched_filter_snr_lower': event_info.get('network_matched_filter_snr_lower'),
                    'network_matched_filter_snr_upper': event_info.get('network_matched_filter_snr_upper'),
                    'network_matched_filter_snr_unit': event_info.get('network_matched_filter_snr_unit'),
                    
                    'luminosity_distance': event_info.get('luminosity_distance'),
                    'luminosity_distance_lower': event_info.get('luminosity_distance_lower'),
                    'luminosity_distance_upper': event_info.get('luminosity_distance_upper'),
                    'luminosity_distance_unit': event_info.get('luminosity_distance_unit'),
                    
                    'chi_eff': event_info.get('chi_eff'),
                    'chi_eff_lower': event_info.get('chi_eff_lower'),
                    'chi_eff_upper': event_info.get('chi_eff_upper'),
                    'chi_eff_unit': event_info.get('chi_eff_unit'),
                    
                    'total_mass_source': event_info.get('total_mass_source'),
                    'total_mass_source_lower': event_info.get('total_mass_source_lower'),
                    'total_mass_source_upper': event_info.get('total_mass_source_upper'),
                    'total_mass_source_unit': event_info.get('total_mass_source_unit'),
                    
                    'chirp_mass_source': event_info.get('chirp_mass_source'),
                    'chirp_mass_source_lower': event_info.get('chirp_mass_source_lower'),
                    'chirp_mass_source_upper': event_info.get('chirp_mass_source_upper'),
                    'chirp_mass_source_unit': event_info.get('chirp_mass_source_unit'),
                    
                    'chirp_mass': event_info.get('chirp_mass'),
                    'chirp_mass_lower': event_info.get('chirp_mass_lower'),
                    'chirp_mass_upper': event_info.get('chirp_mass_upper'),
                    'chirp_mass_unit': event_info.get('chirp_mass_unit'),
                    
                    'redshift': event_info.get('redshift'),
                    'redshift_lower': event_info.get('redshift_lower'),
                    'redshift_upper': event_info.get('redshift_upper'),
                    'redshift_unit': event_info.get('redshift_unit'),
                    
                    'far': event_info.get('far'),
                    'far_lower': event_info.get('far_lower'),
                    'far_upper': event_info.get('far_upper'),
                    'far_unit': event_info.get('far_unit'),
                    
                    'p_astro': event_info.get('p_astro'),
                    'p_astro_lower': event_info.get('p_astro_lower'),
                    'p_astro_upper': event_info.get('p_astro_upper'),
                    'p_astro_unit': event_info.get('p_astro_unit'),
                    
                    'final_mass_source': event_info.get('final_mass_source'),
                    'final_mass_source_lower': event_info.get('final_mass_source_lower'),
                    'final_mass_source_upper': event_info.get('final_mass_source_upper'),
                    'final_mass_source_unit': event_info.get('final_mass_source_unit'),
                    
                    # 应变数据
                    'strain_data': event_info.get('strain', []),
                    
                    # 参数数据
                    'parameters': event_info.get('parameters', {})
                }
                
                parsed_events.append(event_data)
                
            except Exception as e:
                logger.error(f"解析事件 {event_id} 失败: {e}")
                continue
        
        logger.info(f"成功解析 {len(parsed_events)} 个事件")
        return parsed_events

    def get_strain_data_urls(self, event_data):
        """从事件数据中提取应变数据URL"""
        # 检查strain和strain_data字段
        strain_data = event_data.get('strain_data', []) or event_data.get('strain', [])
        data_urls = []
        
        for strain in strain_data:
            # 只筛选32秒txt格式数据
            if strain.get('duration') == 32 and strain.get('format') == 'txt':
                data_urls.append({
                    'url': strain.get('url'),
                    'detector': strain.get('detector'),
                    'gps_start': strain.get('GPSstart'),
                    'sampling_rate': strain.get('sampling_rate'),
                    'duration': strain.get('duration'),
                    'format': strain.get('format'),
                    'filename': os.path.basename(strain.get('url', ''))
                })
        
        return data_urls

    def download_data_file(self, url, event_name, detector, filename):
        """下载数据文件并自动解压"""
        try:
            # 创建事件目录
            event_dir = os.path.join(DATA_DIR, event_name)
            os.makedirs(event_dir, exist_ok=True)
            
            file_path = os.path.join(event_dir, filename)
            
            # 检查文件是否已存在
            if os.path.exists(file_path):
                logger.info(f"文件已存在: {file_path}")
                self.db.insert_data_file(event_name, detector, file_path, os.path.getsize(file_path))
                # 自动解压
                if file_path.endswith('.gz'):
                    self._auto_unzip(file_path, event_name, detector)
                return True
            
            # 下载文件
            logger.info(f"开始下载: {url}")
            response = self.session.get(url, stream=True, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # 处理gzip压缩文件
            if url.endswith('.gz'):
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                self._auto_unzip(file_path, event_name, detector)
            else:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
            
            file_size = os.path.getsize(file_path)
            self.db.insert_data_file(event_name, detector, file_path, file_size)
            
            logger.info(f"下载完成: {file_path} ({file_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"下载文件失败 {url}: {e}")
            self.db.log_download(event_name, detector, 'failed', str(e))
            return False

    def _auto_unzip(self, gz_path, event_name, detector):
        """自动解压gz文件，并将解压后的txt文件路径写入数据库"""
        try:
            if not gz_path.endswith('.gz'):
                return
            txt_path = gz_path[:-3]  # 去掉.gz
            if os.path.exists(txt_path):
                logger.info(f"已解压: {txt_path}")
                self.db.insert_data_file(event_name, detector, txt_path, os.path.getsize(txt_path))
                return
            import gzip
            with gzip.open(gz_path, 'rb') as f_in, open(txt_path, 'wb') as f_out:
                f_out.write(f_in.read())
            logger.info(f"自动解压完成: {txt_path}")
            self.db.insert_data_file(event_name, detector, txt_path, os.path.getsize(txt_path))
        except Exception as e:
            logger.error(f"自动解压失败: {gz_path}: {e}")

    def get_event_detail(self, event_data):
        """获取单个事件的详细信息"""
        try:
            # 使用事件数据中的json_url
            json_url = event_data.get('json_url')
            if not json_url:
                logger.warning(f"事件 {event_data.get('common_name')} 没有json_url")
                return None
            
            logger.info(f"获取事件详情: {json_url}")
            response = self.session.get(json_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            api_data = response.json()
            # 提取events字段中的数据
            if 'events' in api_data:
                events = api_data['events']
                # 使用事件ID作为键
                event_id = event_data.get('event_id')
                if event_id and event_id in events:
                    event_detail = events[event_id]
                else:
                    # 如果没有找到，尝试使用通用名称
                    common_name = event_data.get('common_name')
                    if common_name and common_name in events:
                        event_detail = events[common_name]
                    else:
                        logger.warning(f"未找到事件 {event_id or common_name} 的详细信息")
                        return None
            else:
                event_detail = api_data
            
            logger.info(f"成功获取事件详情: {event_data.get('common_name')}")
            return event_detail
            
        except Exception as e:
            logger.error(f"获取事件详情失败 {event_data.get('common_name')}: {e}")
            return None

    def crawl_all_events(self, limit=None):
        """爬取所有事件"""
        try:
            logger.info("开始爬取所有事件...")
            
            events = self.get_events_list()
            if limit:
                events = events[:limit]
            
            total_events = len(events)
            success_count = 0
            
            for i, event in enumerate(events, 1):
                event_name = event.get('common_name') or event.get('event_id')
                logger.info(f"处理事件 {i}/{total_events}: {event_name}")
                
                # 获取事件详细信息
                event_detail = self.get_event_detail(event)
                if event_detail:
                    # 合并详细信息到事件数据中
                    event.update(event_detail)
                
                # 保存事件基本信息
                self.db.insert_event(event)
                
                # 获取并下载应变数据
                data_urls = self.get_strain_data_urls(event)
                
                for data_url in data_urls:
                    success = self.download_data_file(
                        data_url['url'],
                        event_name,
                        data_url['detector'],
                        data_url['filename']
                    )
                    if success:
                        success_count += 1
                
                # 添加延迟避免请求过快
                time.sleep(1)
            
            logger.info(f"爬取完成: 成功处理 {success_count} 个数据文件")
            return success_count
            
        except Exception as e:
            logger.error(f"爬取事件失败: {e}")
            return 0

    def download_event_data(self, event_name, max_retries=MAX_RETRIES):
        """下载指定事件的数据"""
        try:
            logger.info(f"开始下载事件数据: {event_name}")
            # 从数据库获取事件信息
            from database import DataManager
            db = DataManager()
            event = db.get_event_by_name(event_name)
            if not event:
                logger.error(f"事件 {event_name} 不存在于数据库")
                return False
            # 获取事件详情（用json_url）
            event_detail = self.get_event_detail(event)
            if event_detail:
                event.update(event_detail)
            # 保存最新事件信息
            db.insert_event(event)
            # 获取并下载应变数据
            data_urls = self.get_strain_data_urls(event)
            if not data_urls:
                logger.warning(f"事件 {event_name} 没有找到32秒txt数据")
                return False
            success_count = 0
            for data_url in data_urls:
                success = self.download_data_file(
                    data_url['url'],
                    event_name,
                    data_url['detector'],
                    data_url['filename']
                )
                if success:
                    success_count += 1
            logger.info(f"事件 {event_name} 下载完成: {success_count}/{len(data_urls)} 个文件")
            return success_count > 0
        except Exception as e:
            logger.error(f"下载事件 {event_name} 数据失败: {e}")
            return False
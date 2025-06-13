import json
import os
import logging
from datetime import datetime
from config import EVENTS_FILE, DATA_FILES_DIR, DOWNLOAD_LOG_FILE, LOG_FILE

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataManager:
    """本地文件数据管理类"""
    def __init__(self):
        self.events_file = EVENTS_FILE
        self.data_files_dir = DATA_FILES_DIR
        self.download_log_file = DOWNLOAD_LOG_FILE
        self.init_storage()

    def init_storage(self):
        """初始化存储"""
        try:
            # 创建数据文件目录
            os.makedirs(self.data_files_dir, exist_ok=True)
            
            # 初始化事件文件
            if not os.path.exists(self.events_file):
                self.save_events({})
            
            # 初始化下载日志文件
            if not os.path.exists(self.download_log_file):
                self.save_download_logs([])
            
            logger.info("本地存储初始化完成")
        except Exception as e:
            logger.error(f"存储初始化失败: {e}")
            raise

    def load_events(self):
        """加载事件数据"""
        try:
            if os.path.exists(self.events_file):
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"加载事件数据失败: {e}")
            return {}

    def save_events(self, events):
        """保存事件数据"""
        try:
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(events, f, ensure_ascii=False, indent=2)
            logger.info("事件数据保存成功")
        except Exception as e:
            logger.error(f"保存事件数据失败: {e}")

    def insert_event(self, event_data):
        """插入/更新事件"""
        try:
            events = self.load_events()
            event_name = event_data.get('common_name') or event_data.get('event_id')
            
            if event_name:
                events[event_name] = {
                    # 基本信息
                    'event_id': event_data.get('event_id'),
                    'common_name': event_data.get('common_name'),
                    'version': event_data.get('version'),
                    'catalog': event_data.get('catalog'),
                    'gps_time': event_data.get('gps_time'),
                    'gracedb_id': event_data.get('gracedb_id'),
                    'reference': event_data.get('reference'),
                    'json_url': event_data.get('json_url'),
                    
                    # 质量参数
                    'mass_1_source': event_data.get('mass_1_source'),
                    'mass_1_source_lower': event_data.get('mass_1_source_lower'),
                    'mass_1_source_upper': event_data.get('mass_1_source_upper'),
                    'mass_1_source_unit': event_data.get('mass_1_source_unit'),
                    
                    'mass_2_source': event_data.get('mass_2_source'),
                    'mass_2_source_lower': event_data.get('mass_2_source_lower'),
                    'mass_2_source_upper': event_data.get('mass_2_source_upper'),
                    'mass_2_source_unit': event_data.get('mass_2_source_unit'),
                    
                    # 网络参数
                    'network_matched_filter_snr': event_data.get('network_matched_filter_snr'),
                    'network_matched_filter_snr_lower': event_data.get('network_matched_filter_snr_lower'),
                    'network_matched_filter_snr_upper': event_data.get('network_matched_filter_snr_upper'),
                    'network_matched_filter_snr_unit': event_data.get('network_matched_filter_snr_unit'),
                    
                    # 距离参数
                    'luminosity_distance': event_data.get('luminosity_distance'),
                    'luminosity_distance_lower': event_data.get('luminosity_distance_lower'),
                    'luminosity_distance_upper': event_data.get('luminosity_distance_upper'),
                    'luminosity_distance_unit': event_data.get('luminosity_distance_unit'),
                    
                    # 自旋参数
                    'chi_eff': event_data.get('chi_eff'),
                    'chi_eff_lower': event_data.get('chi_eff_lower'),
                    'chi_eff_upper': event_data.get('chi_eff_upper'),
                    'chi_eff_unit': event_data.get('chi_eff_unit'),
                    
                    # 质量参数
                    'total_mass_source': event_data.get('total_mass_source'),
                    'total_mass_source_lower': event_data.get('total_mass_source_lower'),
                    'total_mass_source_upper': event_data.get('total_mass_source_upper'),
                    'total_mass_source_unit': event_data.get('total_mass_source_unit'),
                    
                    'chirp_mass_source': event_data.get('chirp_mass_source'),
                    'chirp_mass_source_lower': event_data.get('chirp_mass_source_lower'),
                    'chirp_mass_source_upper': event_data.get('chirp_mass_source_upper'),
                    'chirp_mass_source_unit': event_data.get('chirp_mass_source_unit'),
                    
                    'chirp_mass': event_data.get('chirp_mass'),
                    'chirp_mass_lower': event_data.get('chirp_mass_lower'),
                    'chirp_mass_upper': event_data.get('chirp_mass_upper'),
                    'chirp_mass_unit': event_data.get('chirp_mass_unit'),
                    
                    # 红移参数
                    'redshift': event_data.get('redshift'),
                    'redshift_lower': event_data.get('redshift_lower'),
                    'redshift_upper': event_data.get('redshift_upper'),
                    'redshift_unit': event_data.get('redshift_unit'),
                    
                    # 误报率参数
                    'far': event_data.get('far'),
                    'far_lower': event_data.get('far_lower'),
                    'far_upper': event_data.get('far_upper'),
                    'far_unit': event_data.get('far_unit'),
                    
                    # 天体物理概率
                    'p_astro': event_data.get('p_astro'),
                    'p_astro_lower': event_data.get('p_astro_lower'),
                    'p_astro_upper': event_data.get('p_astro_upper'),
                    'p_astro_unit': event_data.get('p_astro_unit'),
                    
                    # 最终质量
                    'final_mass_source': event_data.get('final_mass_source'),
                    'final_mass_source_lower': event_data.get('final_mass_source_lower'),
                    'final_mass_source_upper': event_data.get('final_mass_source_upper'),
                    'final_mass_source_unit': event_data.get('final_mass_source_unit'),
                    
                    # 应变数据
                    'strain_data': event_data.get('strain_data', []),
                    
                    # 参数数据
                    'parameters': event_data.get('parameters', {}),
                    
                    # 元数据
                    'updated_at': datetime.now().isoformat()
                }
                
                self.save_events(events)
                logger.info(f"事件 {event_name} 插入/更新成功")
                return True
            return False
        except Exception as e:
            logger.error(f"插入事件数据失败: {e}")
            return False

    def get_all_events(self):
        """获取所有事件"""
        try:
            events = self.load_events()
            return list(events.values())
        except Exception as e:
            logger.error(f"获取事件数据失败: {e}")
            return []

    def get_event_by_name(self, event_name):
        """根据名称获取事件"""
        try:
            events = self.load_events()
            # 直接查找事件名称
            if event_name in events:
                return events[event_name]
            
            # 如果直接查找失败，尝试通过common_name查找
            for key, event_data in events.items():
                if event_data.get('common_name') == event_name:
                    return event_data
            
            logger.warning(f"未找到事件: {event_name}")
            return None
        except Exception as e:
            logger.error(f"获取事件 {event_name} 失败: {e}")
            return None

    def insert_data_file(self, event_name, detector, file_path, file_size=None):
        """插入数据文件记录"""
        try:
            events = self.load_events()
            if event_name in events:
                if 'data_files' not in events[event_name]:
                    events[event_name]['data_files'] = []
                
                # 检查是否已存在
                existing_file = None
                for file_info in events[event_name]['data_files']:
                    if file_info.get('detector') == detector:
                        existing_file = file_info
                        break
                
                if existing_file:
                    existing_file.update({
                        'file_path': file_path,
                        'file_size': file_size,
                        'download_status': 'completed',
                        'download_time': datetime.now().isoformat()
                    })
                else:
                    events[event_name]['data_files'].append({
                        'detector': detector,
                        'file_path': file_path,
                        'file_size': file_size,
                        'download_status': 'completed',
                        'download_time': datetime.now().isoformat()
                    })
                
                self.save_events(events)
                logger.info(f"数据文件记录插入/更新成功: {event_name} - {detector}")
                return True
            return False
        except Exception as e:
            logger.error(f"插入数据文件记录失败: {e}")
            return False

    def log_download(self, event_name, detector, status, message=""):
        """记录下载日志"""
        try:
            logs = self.load_download_logs()
            logs.append({
                'event_name': event_name,
                'detector': detector,
                'status': status,
                'message': message,
                'created_at': datetime.now().isoformat()
            })
            self.save_download_logs(logs)
            logger.info(f"下载日志记录: {event_name} - {detector} - {status}")
        except Exception as e:
            logger.error(f"记录下载日志失败: {e}")

    def load_download_logs(self):
        """加载下载日志"""
        try:
            if os.path.exists(self.download_log_file):
                with open(self.download_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"加载下载日志失败: {e}")
            return []

    def save_download_logs(self, logs):
        """保存下载日志"""
        try:
            with open(self.download_log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存下载日志失败: {e}")

    def get_download_status(self, event_name):
        """获取下载状态"""
        try:
            events = self.load_events()
            if event_name in events and 'data_files' in events[event_name]:
                return events[event_name]['data_files']
            return []
        except Exception as e:
            logger.error(f"获取下载状态失败: {e}")
            return []

    def get_statistics(self):
        """获取统计信息"""
        try:
            events = self.load_events()
            total_events = len(events)
            
            total_files = 0
            total_size = 0
            detectors = set()
            
            for event_name, event_data in events.items():
                if 'data_files' in event_data:
                    for file_info in event_data['data_files']:
                        total_files += 1
                        total_size += file_info.get('file_size', 0)
                        detectors.add(file_info.get('detector', 'Unknown'))
            
            return {
                'total_events': total_events,
                'total_files': total_files,
                'total_size': total_size,
                'detectors': list(detectors),
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

    def search_events(self, criteria):
        """搜索事件"""
        try:
            events = self.load_events()
            results = []
            
            for event_name, event_data in events.items():
                match = True
                
                # 按事件名称搜索
                if 'name' in criteria:
                    search_name = criteria['name'].lower()
                    event_name_lower = event_name.lower()
                    if search_name not in event_name_lower:
                        match = False
                
                # 按探测器搜索
                if 'detector' in criteria and match:
                    search_detector = criteria['detector'].upper()
                    event_detectors = set()
                    if 'data_files' in event_data:
                        for file_info in event_data['data_files']:
                            event_detectors.add(file_info.get('detector', ''))
                    if search_detector not in event_detectors:
                        match = False
                
                # 按质量范围搜索
                if 'mass_range' in criteria and match:
                    min_mass, max_mass = criteria['mass_range']
                    mass_1 = event_data.get('mass_1_source')
                    mass_2 = event_data.get('mass_2_source')
                    
                    if mass_1 and (mass_1 < min_mass or mass_1 > max_mass):
                        match = False
                    if mass_2 and (mass_2 < min_mass or mass_2 > max_mass):
                        match = False
                
                if match:
                    results.append(event_data)
            
            return results
        except Exception as e:
            logger.error(f"搜索事件失败: {e}")
            return [] 
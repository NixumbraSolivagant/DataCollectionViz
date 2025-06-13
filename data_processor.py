import numpy as np
import pandas as pd
import os
import logging
import json
from scipy import signal
from scipy.fft import fft, fftfreq
import matplotlib.pyplot as plt
import seaborn as sns
from config import SAMPLE_RATE, DURATION, DATA_DIR, EVENTS_FILE

logger = logging.getLogger(__name__)

class DataProcessor:
    """引力波数据处理类"""
    
    def __init__(self):
        self.sample_rate = SAMPLE_RATE
        self.duration = DURATION
        self.expected_samples = SAMPLE_RATE * DURATION
    
    def load_data_file(self, file_path):
        """加载数据文件"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 读取数据文件
            data = np.loadtxt(file_path)
            
            # 验证数据长度
            if len(data) != self.expected_samples:
                logger.warning(f"数据长度不匹配: 期望 {self.expected_samples}, 实际 {len(data)}")
            
            logger.info(f"成功加载数据文件: {file_path}, 数据点: {len(data)}")
            return data
            
        except Exception as e:
            logger.error(f"加载数据文件失败 {file_path}: {e}")
            return None
    
    def get_event_info(self, event_name):
        """从数据库获取事件信息"""
        try:
            if os.path.exists(EVENTS_FILE):
                with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
                    events = json.load(f)
                
                event_data = events.get(event_name)
                if event_data:
                    logger.info(f"成功获取事件信息: {event_name}")
                    return event_data
                else:
                    logger.warning(f"未找到事件: {event_name}")
                    return None
            else:
                logger.warning("事件数据库文件不存在")
                return None
                
        except Exception as e:
            logger.error(f"获取事件信息失败: {e}")
            return None
    
    def get_available_detectors(self, event_name):
        """获取事件的可用探测器列表"""
        try:
            event_info = self.get_event_info(event_name)
            if event_info and 'data_files' in event_info:
                detectors = []
                for file_info in event_info['data_files']:
                    detector = file_info.get('detector')
                    if detector and detector not in detectors:
                        detectors.append(detector)
                return detectors
            return []
        except Exception as e:
            logger.error(f"获取探测器列表失败: {e}")
            return []
    
    def get_strain_data_info(self, event_name):
        """获取应变数据信息"""
        try:
            event_info = self.get_event_info(event_name)
            if event_info and 'strain_data' in event_info:
                strain_info = []
                for strain in event_info['strain_data']:
                    # 优先选择16kHz 32秒的txt格式数据
                    if (strain.get('sampling_rate') == 16384 and 
                        strain.get('duration') == 32 and 
                        strain.get('format') == 'txt'):
                        
                        strain_info.append({
                            'detector': strain.get('detector'),
                            'gps_start': strain.get('GPSstart'),
                            'sampling_rate': strain.get('sampling_rate'),
                            'duration': strain.get('duration'),
                            'format': strain.get('format'),
                            'url': strain.get('url'),
                            'filename': os.path.basename(strain.get('url', ''))
                        })
                return strain_info
            return []
        except Exception as e:
            logger.error(f"获取应变数据信息失败: {e}")
            return []
    
    def preprocess_data(self, data):
        """数据预处理"""
        try:
            if data is None or len(data) == 0:
                return None
            
            # 去除均值
            data_centered = data - np.mean(data)
            
            # 应用窗函数 (Hann窗)
            window = signal.windows.hann(len(data_centered))
            data_windowed = data_centered * window
            
            # 高通滤波 (去除低频噪声)
            nyquist = self.sample_rate / 2
            cutoff = 10  # 10 Hz 高通滤波
            b, a = signal.butter(4, cutoff / nyquist, btype='high')
            data_filtered = signal.filtfilt(b, a, data_windowed)
            
            logger.info("数据预处理完成")
            return data_filtered
            
        except Exception as e:
            logger.error(f"数据预处理失败: {e}")
            return data  # 返回原始数据
    
    def compute_fft(self, data):
        """计算快速傅里叶变换"""
        try:
            if data is None or len(data) == 0:
                return None, None
            
            # 计算FFT
            fft_data = fft(data)
            freqs = fftfreq(len(data), 1/self.sample_rate)
            
            # 只取正频率部分
            positive_freqs = freqs[:len(freqs)//2]
            positive_fft = np.abs(fft_data[:len(fft_data)//2])
            
            logger.info("FFT计算完成")
            return positive_freqs, positive_fft
            
        except Exception as e:
            logger.error(f"FFT计算失败: {e}")
            return None, None
    
    def compute_psd(self, data):
        """计算功率谱密度"""
        try:
            if data is None or len(data) == 0:
                return None, None
            
            # 计算功率谱密度
            freqs, psd = signal.welch(data, fs=self.sample_rate, nperseg=min(4096, len(data)//4))
            
            logger.info("功率谱密度计算完成")
            return freqs, psd
            
        except Exception as e:
            logger.error(f"功率谱密度计算失败: {e}")
            return None, None
    
    def detect_peaks(self, data, threshold=0.1):
        """检测峰值"""
        try:
            if data is None or len(data) == 0:
                return []
            
            # 使用scipy的峰值检测
            peaks, properties = signal.find_peaks(np.abs(data), height=threshold*np.max(np.abs(data)))
            
            # 获取峰值信息
            peak_info = []
            for i, peak in enumerate(peaks):
                peak_info.append({
                    'index': peak,
                    'time': peak / self.sample_rate,
                    'amplitude': data[peak],
                    'prominence': properties['peak_heights'][i] if 'peak_heights' in properties else 0
                })
            
            logger.info(f"检测到 {len(peak_info)} 个峰值")
            return peak_info
            
        except Exception as e:
            logger.error(f"峰值检测失败: {e}")
            return []
    
    def analyze_event_data(self, event_name, detectors=None):
        """分析事件数据"""
        try:
            event_info = self.get_event_info(event_name)
            if not event_info:
                logger.error(f"未找到事件信息: {event_name}")
                return None
            
            # 获取可用探测器
            available_detectors = self.get_available_detectors(event_name)
            if not available_detectors:
                logger.error(f"事件 {event_name} 没有可用的数据文件")
                return None
            
            # 如果指定了探测器，只分析指定的探测器
            if detectors:
                available_detectors = [d for d in available_detectors if d in detectors]
            
            analysis_results = {
                'event_info': event_info,
                'detectors': {}
            }
            
            # 分析每个探测器的数据
            for detector in available_detectors:
                logger.info(f"分析探测器: {detector}")
                
                # 查找对应的数据文件
                file_path = None
                for file_info in event_info.get('data_files', []):
                    if file_info.get('detector') == detector:
                        file_path = file_info.get('file_path')
                        break
                
                if not file_path or not os.path.exists(file_path):
                    logger.warning(f"探测器 {detector} 的数据文件不存在: {file_path}")
                    continue
                
                # 加载数据
                data = self.load_data_file(file_path)
                if data is None:
                    continue
                
                # 预处理
                processed_data = self.preprocess_data(data)
                
                # 计算FFT
                freqs, fft_data = self.compute_fft(processed_data)
                
                # 计算功率谱密度
                psd_freqs, psd_data = self.compute_psd(processed_data)
                
                # 检测峰值
                peaks = self.detect_peaks(processed_data)
                
                # 统计信息
                stats = self.compute_statistics(processed_data)
                
                analysis_results['detectors'][detector] = {
                    'raw_data': data,
                    'processed_data': processed_data,
                    'frequencies': freqs,
                    'fft_data': fft_data,
                    'psd_frequencies': psd_freqs,
                    'psd_data': psd_data,
                    'peaks': peaks,
                    'statistics': stats,
                    'file_path': file_path
                }
            
            logger.info(f"事件 {event_name} 分析完成，分析了 {len(analysis_results['detectors'])} 个探测器")
            return analysis_results
            
        except Exception as e:
            logger.error(f"分析事件 {event_name} 失败: {e}")
            return None
    
    def compute_statistics(self, data):
        """计算统计信息"""
        try:
            if data is None or len(data) == 0:
                return {}
            
            stats = {
                'mean': np.mean(data),
                'std': np.std(data),
                'min': np.min(data),
                'max': np.max(data),
                'rms': np.sqrt(np.mean(data**2)),
                'peak_to_peak': np.max(data) - np.min(data),
                'kurtosis': float(pd.Series(data).kurtosis()),
                'skewness': float(pd.Series(data).skew())
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"计算统计信息失败: {e}")
            return {}
    
    def create_visualization_data(self, analysis_results):
        """创建可视化数据"""
        try:
            if not analysis_results or 'detectors' not in analysis_results:
                return None
            
            viz_data = {
                'event_info': analysis_results.get('event_info', {}),
                'detectors': {}
            }
            
            for detector, detector_data in analysis_results['detectors'].items():
                # 准备时间序列数据
                time_series = np.arange(len(detector_data['raw_data'])) / self.sample_rate
                
                # 准备FFT数据
                freqs = detector_data.get('frequencies', [])
                fft_data = detector_data.get('fft_data', [])
                
                # 准备PSD数据
                psd_freqs = detector_data.get('psd_frequencies', [])
                psd_data = detector_data.get('psd_data', [])
                
                # 准备峰值数据
                peaks = detector_data.get('peaks', [])
                peak_times = [peak['time'] for peak in peaks]
                peak_amplitudes = [peak['amplitude'] for peak in peaks]
                
                viz_data['detectors'][detector] = {
                    'time_series': {
                        'time': time_series.tolist(),
                        'raw_data': detector_data['raw_data'].tolist(),
                        'processed_data': detector_data['processed_data'].tolist() if detector_data['processed_data'] is not None else []
                    },
                    'fft': {
                        'frequencies': freqs.tolist() if freqs is not None else [],
                        'magnitude': fft_data.tolist() if fft_data is not None else []
                    },
                    'psd': {
                        'frequencies': psd_freqs.tolist() if psd_freqs is not None else [],
                        'power': psd_data.tolist() if psd_data is not None else []
                    },
                    'peaks': {
                        'times': peak_times,
                        'amplitudes': peak_amplitudes
                    },
                    'statistics': detector_data.get('statistics', {})
                }
            
            return viz_data
            
        except Exception as e:
            logger.error(f"创建可视化数据失败: {e}")
            return None
    
    def save_analysis_results(self, event_name, analysis_results, output_dir=None):
        """保存分析结果"""
        try:
            if output_dir is None:
                output_dir = os.path.join(DATA_DIR, event_name, 'analysis')
            
            os.makedirs(output_dir, exist_ok=True)
            
            # 保存分析结果
            results_file = os.path.join(output_dir, 'analysis_results.json')
            
            # 转换numpy数组为列表以便JSON序列化
            serializable_results = self._make_serializable(analysis_results)
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2)
            
            # 保存可视化数据
            viz_data = self.create_visualization_data(analysis_results)
            if viz_data:
                viz_file = os.path.join(output_dir, 'visualization_data.json')
                with open(viz_file, 'w', encoding='utf-8') as f:
                    json.dump(viz_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"分析结果已保存到: {output_dir}")
            return output_dir
            
        except Exception as e:
            logger.error(f"保存分析结果失败: {e}")
            return None
    
    def _make_serializable(self, obj):
        """将对象转换为可JSON序列化的格式"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        else:
            return obj 
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
            # 规范化文件路径
            file_path = os.path.normpath(file_path)
            logger.info(f"尝试加载文件: {file_path}")
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                # 尝试不同的文件扩展名
                base_path = file_path.replace('.gz', '').replace('-z', '')
                possible_paths = [
                    base_path,
                    base_path + '.gz',
                    base_path + '.txt',
                    base_path + '.txt.gz'
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        file_path = path
                        logger.info(f"找到文件: {file_path}")
                        break
                else:
                    logger.error(f"未找到任何匹配的文件: {base_path}")
                    raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 从文件名中获取采样率信息
            filename = os.path.basename(file_path)
            logger.info(f"正在加载文件: {filename}")
            
            if '16KHZ' in filename.upper():
                expected_rate = 16384
                logger.info("检测到16kHz数据文件")
            elif '4KHZ' in filename.upper():
                expected_rate = 4096
                logger.info("检测到4kHz数据文件")
            else:
                expected_rate = self.sample_rate
                logger.warning(f"无法从文件名确定采样率，使用默认值: {expected_rate}Hz")
            
            # 读取数据文件
            logger.info(f"开始读取数据文件: {file_path}")
            try:
                data = np.loadtxt(file_path)
                logger.info(f"成功读取数据，数据点数量: {len(data)}")
            except Exception as e:
                logger.error(f"读取数据文件失败: {e}", exc_info=True)
                raise
            
            # 验证数据长度
            expected_samples = expected_rate * self.duration
            if len(data) != expected_samples:
                logger.warning(f"数据长度不匹配: 期望 {expected_samples}, 实际 {len(data)}")
                # 如果数据长度不匹配，尝试重采样
                if len(data) > 0:
                    logger.info(f"开始重采样数据到 {expected_samples} 个点")
                    data = signal.resample(data, expected_samples)
                    logger.info(f"数据重采样完成")
            
            logger.info(f"成功加载数据文件: {file_path}, 数据点: {len(data)}")
            return data
            
        except Exception as e:
            logger.error(f"加载数据文件失败 {file_path}: {e}", exc_info=True)
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
                    # 添加数据文件信息
                    if 'data_files' not in event_data:
                        event_data['data_files'] = []
                        # 检查L1探测器数据
                        detectors = ['L1', 'H1']
                        for detector in detectors:
                            prefix = 'L-L1' if detector == 'L1' else 'H-H1'
                            # 检查16kHz数据
                            file_16k = f"{prefix}_GWOSC_16KHZ_R1-1369419303-32.txt"
                            file_16k_path = os.path.join(DATA_DIR, event_name, file_16k)
                            if os.path.exists(file_16k_path):
                                event_data['data_files'].append({
                                    'detector': detector,
                                    'file_path': file_16k_path,
                                    'sampling_rate': 16384,
                                    'duration': 32
                                })
                                logger.info(f"找到{detector}探测器16kHz数据: {file_16k}")
                            # 检查4kHz数据
                            file_4k = f"{prefix}_GWOSC_4KHZ_R1-1369419303-32.txt"
                            file_4k_path = os.path.join(DATA_DIR, event_name, file_4k)
                            if os.path.exists(file_4k_path):
                                event_data['data_files'].append({
                                    'detector': detector,
                                    'file_path': file_4k_path,
                                    'sampling_rate': 4096,
                                    'duration': 32
                                })
                                logger.info(f"找到{detector}探测器4kHz数据: {file_4k}")
                    return event_data
                else:
                    logger.warning(f"未找到事件: {event_name}")
                    return None
            else:
                logger.warning("事件数据库文件不存在")
                return None
                
        except Exception as e:
            logger.error(f"获取事件信息失败: {e}", exc_info=True)
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
                # 首先添加16kHz数据
                for strain in event_info['strain_data']:
                    if (strain.get('sampling_rate') == 16384 and 
                        strain.get('duration') == 32 and 
                        strain.get('format') == 'txt'):
                        
                        url = strain.get('url', '')
                        filename = os.path.basename(url)
                        # 移除.gz后缀
                        if filename.endswith('.gz'):
                            filename = filename[:-3]
                        
                        strain_info.append({
                            'detector': strain.get('detector'),
                            'gps_start': strain.get('GPSstart'),
                            'sampling_rate': strain.get('sampling_rate'),
                            'duration': strain.get('duration'),
                            'format': strain.get('format'),
                            'url': url,
                            'filename': filename
                        })
                
                # 如果没有16kHz数据，再添加4kHz数据
                if not strain_info:
                    for strain in event_info['strain_data']:
                        if (strain.get('sampling_rate') == 4096 and 
                            strain.get('duration') == 32 and 
                            strain.get('format') == 'txt'):
                            
                            url = strain.get('url', '')
                            filename = os.path.basename(url)
                            # 移除.gz后缀
                            if filename.endswith('.gz'):
                                filename = filename[:-3]
                            
                            strain_info.append({
                                'detector': strain.get('detector'),
                                'gps_start': strain.get('GPSstart'),
                                'sampling_rate': strain.get('sampling_rate'),
                                'duration': strain.get('duration'),
                                'format': strain.get('format'),
                                'url': url,
                                'filename': filename
                            })
                
                logger.info(f"找到 {len(strain_info)} 个应变数据文件: {[s['filename'] for s in strain_info]}")
                return strain_info
            return []
        except Exception as e:
            logger.error(f"获取应变数据信息失败: {e}", exc_info=True)
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
            
            # 应用窗函数以减少频谱泄漏
            window = signal.windows.hann(len(data))
            windowed_data = data * window
            
            # 计算FFT
            fft_data = fft(windowed_data)
            freqs = fftfreq(len(data), 1/self.sample_rate)
            
            # 只取正频率部分并归一化
            positive_freqs = freqs[:len(freqs)//2]
            positive_fft = np.abs(fft_data[:len(fft_data)//2])
            positive_fft = positive_fft / len(data)  # 归一化
            
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
            
            # 使用Welch方法计算功率谱密度
            # 使用较大的窗口大小以获得更好的频率分辨率
            nperseg = min(8192, len(data)//2)
            noverlap = nperseg // 2
            
            freqs, psd = signal.welch(
                data,
                fs=self.sample_rate,
                nperseg=nperseg,
                noverlap=noverlap,
                window='hann',
                scaling='density'
            )
            
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
                logger.info(f"探测器 {detector} 预处理后数据长度: {len(processed_data) if processed_data is not None else 0}")
                
                # 计算FFT
                freqs, fft_data = self.compute_fft(processed_data)
                
                # 计算功率谱密度
                psd_freqs, psd_data = self.compute_psd(processed_data)
                
                # 检测峰值
                peaks = self.detect_peaks(processed_data)
                
                # 统计信息
                stats = self.compute_statistics(processed_data)
                
                # 时间轴
                time_axis = np.arange(len(processed_data)) / self.sample_rate if processed_data is not None else []
                
                analysis_results['detectors'][detector] = {
                    'raw_data': data,
                    'processed_data': processed_data,
                    'time': time_axis,
                    'fft_frequencies': freqs,
                    'fft_magnitude': fft_data,
                    'psd_frequencies': psd_freqs,
                    'psd_power': psd_data,
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
        """计算数据统计信息"""
        try:
            if data is None or len(data) == 0:
                return None
            
            # 时域统计
            time_stats = {
                'mean': float(np.mean(data)),
                'std': float(np.std(data)),
                'min': float(np.min(data)),
                'max': float(np.max(data)),
                'peak_to_peak': float(np.max(data) - np.min(data)),
                'rms': float(np.sqrt(np.mean(np.square(data)))),
                'skewness': float(pd.Series(data).skew()),
                'kurtosis': float(pd.Series(data).kurtosis())
            }
            
            # 频域统计
            fft_freq, fft_mag = self.compute_fft(data)
            if fft_freq is not None and fft_mag is not None:
                # 计算主要频率成分
                # 使用更低的阈值以捕获更多的重要频率
                peak_indices = signal.find_peaks(fft_mag, height=np.max(fft_mag)*0.05)[0]
                peak_freqs = fft_freq[peak_indices]
                peak_mags = fft_mag[peak_indices]
                
                # 按幅度排序
                sorted_indices = np.argsort(peak_mags)[::-1]
                peak_freqs = peak_freqs[sorted_indices]
                peak_mags = peak_mags[sorted_indices]
                
                # 获取前5个主要频率
                main_freqs = peak_freqs[:5]
                main_mags = peak_mags[:5]
                
                # 计算带宽（使用-3dB点）
                max_mag = np.max(fft_mag)
                half_power = max_mag / np.sqrt(2)
                bandwidth_mask = fft_mag >= half_power
                bandwidth = float(np.sum(bandwidth_mask) * (fft_freq[1] - fft_freq[0]))
                
                freq_stats = {
                    'main_frequencies': [float(f) for f in main_freqs],
                    'main_magnitudes': [float(m) for m in main_mags],
                    'bandwidth': bandwidth,
                    'total_power': float(np.sum(fft_mag**2))
                }
            else:
                freq_stats = {
                    'main_frequencies': [],
                    'main_magnitudes': [],
                    'bandwidth': 0.0,
                    'total_power': 0.0
                }
            
            # PSD统计
            psd_freq, psd_power = self.compute_psd(data)
            if psd_freq is not None and psd_power is not None:
                # 计算功率带宽（使用-3dB点）
                max_power = np.max(psd_power)
                half_power = max_power / np.sqrt(2)
                power_bandwidth_mask = psd_power >= half_power
                power_bandwidth = float(np.sum(power_bandwidth_mask) * (psd_freq[1] - psd_freq[0]))
                
                # 改进的信噪比计算
                # 使用峰值功率与平均功率的比值
                peak_power = np.max(psd_power)
                mean_power = np.mean(psd_power)
                snr = float(peak_power / mean_power) if mean_power > 0 else 0.0
                
                psd_stats = {
                    'mean_power': float(mean_power),
                    'max_power': float(peak_power),
                    'power_bandwidth': power_bandwidth,
                    'snr': snr
                }
            else:
                psd_stats = {
                    'mean_power': 0.0,
                    'max_power': 0.0,
                    'power_bandwidth': 0.0,
                    'snr': 0.0
                }
            
            # 合并所有统计信息
            stats = {
                'time_domain': time_stats,
                'frequency_domain': freq_stats,
                'psd': psd_stats
            }
            
            logger.info("统计信息计算完成")
            return stats
            
        except Exception as e:
            logger.error(f"计算统计信息失败: {e}", exc_info=True)
            return None
    
    def create_visualization_data(self, analysis_results):
        """创建可视化数据"""
        try:
            if not analysis_results:
                return None
            
            viz_data = {
                'detectors': {},
                'metadata': {
                    'event_name': analysis_results.get('event_info', {}).get('common_name') or analysis_results.get('event_info', {}).get('event_id'),
                    'gps_time': analysis_results.get('event_info', {}).get('gps_time'),
                    'detectors': list(analysis_results.get('detectors', {}).keys())
                }
            }
            
            # 处理每个探测器的数据
            for detector, det_data in analysis_results.get('detectors', {}).items():
                viz_data['detectors'][detector] = {
                    'time_series': {
                        'time': self._make_serializable(det_data.get('time', [])),
                        'raw_data': self._make_serializable(det_data.get('raw_data', [])),
                        'processed_data': self._make_serializable(det_data.get('processed_data', []))
                    },
                    'fft': {
                        'frequencies': self._make_serializable(det_data.get('fft_frequencies', [])),
                        'magnitude': self._make_serializable(det_data.get('fft_magnitude', []))
                    },
                    'psd': {
                        'frequencies': self._make_serializable(det_data.get('psd_frequencies', [])),
                        'power': self._make_serializable(det_data.get('psd_power', []))
                    },
                    'statistics': self._make_serializable(det_data.get('statistics', {}))
                }
            
            # 验证数据是否可以JSON序列化
            try:
                json.dumps(viz_data)
                return viz_data
            except (TypeError, ValueError) as e:
                logger.error(f"数据无法JSON序列化: {e}")
                return None
            
        except Exception as e:
            logger.error(f"创建可视化数据失败: {e}", exc_info=True)
            return None
    
    def _make_serializable(self, obj):
        """确保对象可以被JSON序列化"""
        if isinstance(obj, (np.ndarray, np.generic)):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            return str(obj)
    
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
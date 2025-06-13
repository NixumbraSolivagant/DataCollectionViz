import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import queue
import logging
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from config import GUI_TITLE, GUI_WIDTH, GUI_HEIGHT, LOG_FILE
from database import DataManager
from crawler import GWOSCCrawler
from data_processor import DataProcessor

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

class GWOSCGUI:
    """引力波数据系统GUI应用"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(GUI_TITLE)
        self.root.geometry(f"{GUI_WIDTH}x{GUI_HEIGHT}")
        self.root.configure(bg='#f0f0f0')
        
        # 初始化组件
        self.db = DataManager()
        self.crawler = GWOSCCrawler()
        self.data_processor = DataProcessor()
        
        # 消息队列用于线程间通信
        self.message_queue = queue.Queue()
        
        # 创建界面
        self.create_widgets()
        
        # 启动消息处理
        self.process_messages()
        
        # 加载初始数据
        self.load_events()
    
    def create_widgets(self):
        """创建GUI组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text=GUI_TITLE, 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 左侧控制面板
        self.create_control_panel(main_frame)
        
        # 中间事件列表
        self.create_event_list(main_frame)
        
        # 右侧详情面板
        self.create_detail_panel(main_frame)
        
        # 底部状态栏
        self.create_status_bar(main_frame)
    
    def create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 爬虫控制
        crawler_frame = ttk.LabelFrame(control_frame, text="数据爬取", padding="5")
        crawler_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(crawler_frame, text="爬取事件列表", 
                  command=self.crawl_events).pack(fill=tk.X, pady=2)
        
        ttk.Button(crawler_frame, text="下载选中事件数据", 
                  command=self.download_selected_event).pack(fill=tk.X, pady=2)
        
        ttk.Button(crawler_frame, text="批量下载数据", 
                  command=self.batch_download).pack(fill=tk.X, pady=2)
        
        # 数据分析
        analysis_frame = ttk.LabelFrame(control_frame, text="数据分析", padding="5")
        analysis_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(analysis_frame, text="分析选中事件", 
                  command=self.analyze_selected_event).pack(fill=tk.X, pady=2)
        
        ttk.Button(analysis_frame, text="生成可视化", 
                  command=self.visualize_selected_event).pack(fill=tk.X, pady=2)
        
        # 系统信息
        info_frame = ttk.LabelFrame(control_frame, text="系统信息", padding="5")
        info_frame.pack(fill=tk.X)
        
        self.stats_text = tk.Text(info_frame, height=8, width=25, font=('Arial', 9))
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        # 更新统计信息
        self.update_statistics()
    
    def create_event_list(self, parent):
        """创建事件列表"""
        list_frame = ttk.LabelFrame(parent, text="事件列表", padding="10")
        list_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 搜索框
        search_frame = ttk.Frame(list_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="搜索:").grid(row=0, column=0, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_events)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # 事件列表
        columns = ('事件名称', 'GPS时间', '总质量', '距离', '信噪比', '状态')
        self.event_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题
        for col in columns:
            self.event_tree.heading(col, text=col, command=lambda c=col: self.sort_events(c))
            self.event_tree.column(col, width=100)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.event_tree.yview)
        self.event_tree.configure(yscrollcommand=scrollbar.set)
        
        self.event_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # 绑定选择事件
        self.event_tree.bind('<<TreeviewSelect>>', self.on_event_select)
    
    def create_detail_panel(self, parent):
        """创建详情面板"""
        detail_frame = ttk.LabelFrame(parent, text="事件详情", padding="10")
        detail_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        detail_frame.columnconfigure(0, weight=1)
        
        # 详情信息
        self.detail_text = scrolledtext.ScrolledText(detail_frame, height=10, width=30)
        self.detail_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 图表区域
        chart_frame = ttk.LabelFrame(detail_frame, text="数据可视化", padding="5")
        chart_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(0, weight=1)
        
        # 创建matplotlib图形
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 操作按钮
        button_frame = ttk.Frame(detail_frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(button_frame, text="时间序列", 
                  command=lambda: self.plot_data('time_series')).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="FFT频谱", 
                  command=lambda: self.plot_data('fft')).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="功率谱", 
                  command=lambda: self.plot_data('psd')).pack(side=tk.LEFT, padx=2)
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=0, sticky=tk.W)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, 
                                          mode='determinate')
        self.progress_bar.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
    
    def update_statistics(self):
        """更新统计信息"""
        try:
            stats = self.db.get_statistics()
            
            stats_text = f"""系统统计信息:
            
总事件数: {stats['total_events']}
已下载事件: {stats['downloaded_events']}
数据文件数: {stats['total_files']}

最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
            
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
    
    def load_events(self):
        """加载事件列表"""
        try:
            events = self.db.get_all_events()
            self.populate_event_list(events)
        except Exception as e:
            logger.error(f"加载事件列表失败: {e}")
            messagebox.showerror("错误", f"加载事件列表失败: {e}")
    
    def populate_event_list(self, events):
        """填充事件列表"""
        # 清空现有项目
        for item in self.event_tree.get_children():
            self.event_tree.delete(item)
        
        # 添加事件
        for event in events:
            # 检查下载状态
            download_status = self.db.get_download_status(event['event_name'])
            status = "已下载" if download_status else "未下载"
            
            self.event_tree.insert('', 'end', values=(
                event['event_name'],
                f"{event['gps_time']:.1f}" if event['gps_time'] else '--',
                f"{event['total_mass']:.1f}" if event['total_mass'] else '--',
                f"{event['distance']:.0f}" if event['distance'] else '--',
                f"{event['network_snr']:.1f}" if event['network_snr'] else '--',
                status
            ))
    
    def filter_events(self, *args):
        """过滤事件"""
        search_term = self.search_var.get().lower()
        events = self.db.get_all_events()
        
        if search_term:
            filtered_events = [e for e in events if search_term in e['event_name'].lower()]
        else:
            filtered_events = events
        
        self.populate_event_list(filtered_events)
    
    def sort_events(self, column):
        """排序事件"""
        # 实现排序逻辑
        pass
    
    def on_event_select(self, event):
        """事件选择处理"""
        selection = self.event_tree.selection()
        if selection:
            item = self.event_tree.item(selection[0])
            event_name = item['values'][0]
            self.show_event_details(event_name)
    
    def show_event_details(self, event_name):
        """显示事件详情"""
        try:
            event = self.db.get_event_by_name(event_name)
            if event:
                details = f"""事件名称: {event['event_name']}
版本: {event['version']}
发布: {event['release']}
GPS时间: {event['gps_time']:.1f}
质量1: {event['mass1']:.1f} M☉
质量2: {event['mass2']:.1f} M☉
总质量: {event['total_mass']:.1f} M☉
距离: {event['distance']:.0f} Mpc
网络信噪比: {event['network_snr']:.1f}
有效自旋: {event['chi_eff']:.2f}
红移: {event['redshift']:.3f}
误报率: {event['false_alarm_rate']}
Pastro: {event['pastro']}
最终质量: {event['final_mass']:.1f} M☉"""
                
                self.detail_text.delete(1.0, tk.END)
                self.detail_text.insert(1.0, details)
                
                # 保存当前选中事件
                self.selected_event = event_name
                
        except Exception as e:
            logger.error(f"显示事件详情失败: {e}")
    
    def crawl_events(self):
        """爬取事件列表"""
        def crawl_thread():
            try:
                self.update_status("正在爬取事件列表...")
                self.progress_var.set(0)
                
                success = self.crawler.crawl_all_events()
                
                if success:
                    self.message_queue.put(("success", "事件列表爬取成功"))
                    self.message_queue.put(("load_events", None))
                    self.message_queue.put(("update_stats", None))
                else:
                    self.message_queue.put(("error", "事件列表爬取失败"))
                
            except Exception as e:
                logger.error(f"爬取事件失败: {e}")
                self.message_queue.put(("error", f"爬取失败: {e}"))
            finally:
                self.progress_var.set(100)
                self.update_status("就绪")
        
        threading.Thread(target=crawl_thread, daemon=True).start()
    
    def download_selected_event(self):
        """下载选中事件数据"""
        if not hasattr(self, 'selected_event'):
            messagebox.showwarning("警告", "请先选择一个事件")
            return
        
        def download_thread():
            try:
                self.update_status(f"正在下载事件 {self.selected_event} 的数据...")
                self.progress_var.set(0)
                
                success = self.crawler.download_event_data(self.selected_event)
                
                if success:
                    self.message_queue.put(("success", f"事件 {self.selected_event} 数据下载成功"))
                    self.message_queue.put(("load_events", None))
                    self.message_queue.put(("update_stats", None))
                else:
                    self.message_queue.put(("error", f"事件 {self.selected_event} 数据下载失败"))
                
            except Exception as e:
                logger.error(f"下载事件数据失败: {e}")
                self.message_queue.put(("error", f"下载失败: {e}"))
            finally:
                self.progress_var.set(100)
                self.update_status("就绪")
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def batch_download(self):
        """批量下载数据"""
        # 实现批量下载逻辑
        messagebox.showinfo("信息", "批量下载功能开发中...")
    
    def analyze_selected_event(self):
        """分析选中事件"""
        if not hasattr(self, 'selected_event'):
            messagebox.showwarning("警告", "请先选择一个事件")
            return
        
        def analyze_thread():
            try:
                self.update_status(f"正在分析事件 {self.selected_event}...")
                self.progress_var.set(0)
                
                analysis_results = self.data_processor.analyze_event_data(self.selected_event)
                
                if analysis_results:
                    self.message_queue.put(("success", f"事件 {self.selected_event} 分析完成"))
                    # 保存分析结果
                    self.data_processor.save_analysis_results(self.selected_event, analysis_results)
                else:
                    self.message_queue.put(("error", f"事件 {self.selected_event} 分析失败"))
                
            except Exception as e:
                logger.error(f"分析事件失败: {e}")
                self.message_queue.put(("error", f"分析失败: {e}"))
            finally:
                self.progress_var.set(100)
                self.update_status("就绪")
        
        threading.Thread(target=analyze_thread, daemon=True).start()
    
    def visualize_selected_event(self):
        """可视化选中事件"""
        if not hasattr(self, 'selected_event'):
            messagebox.showwarning("警告", "请先选择一个事件")
            return
        
        # 默认显示时间序列
        self.plot_data('time_series')
    
    def plot_data(self, plot_type):
        """绘制数据图表"""
        if not hasattr(self, 'selected_event'):
            messagebox.showwarning("警告", "请先选择一个事件")
            return
        
        try:
            # 分析数据
            analysis_results = self.data_processor.analyze_event_data(self.selected_event)
            if not analysis_results:
                messagebox.showerror("错误", "没有找到数据文件")
                return
            
            # 清除现有图表
            self.ax.clear()
            
            # 绘制图表
            if plot_type == 'time_series':
                self.plot_time_series(analysis_results)
            elif plot_type == 'fft':
                self.plot_fft(analysis_results)
            elif plot_type == 'psd':
                self.plot_psd(analysis_results)
            
            # 更新画布
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"绘制图表失败: {e}")
            messagebox.showerror("错误", f"绘制图表失败: {e}")
    
    def plot_time_series(self, analysis_results):
        """绘制时间序列"""
        for detector, data in analysis_results.items():
            time_axis = np.arange(len(data['processed_data'])) / self.data_processor.sample_rate
            self.ax.plot(time_axis, data['processed_data'], label=f'{detector} 探测器', linewidth=0.5)
        
        self.ax.set_xlabel('时间 (秒)')
        self.ax.set_ylabel('振幅')
        self.ax.set_title('引力波时间序列数据')
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)
    
    def plot_fft(self, analysis_results):
        """绘制FFT频谱"""
        for detector, data in analysis_results.items():
            self.ax.semilogy(data['frequencies'], data['fft_data'], label=f'{detector} 探测器')
        
        self.ax.set_xlabel('频率 (Hz)')
        self.ax.set_ylabel('幅度')
        self.ax.set_title('快速傅里叶变换 (FFT)')
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xscale('log')
    
    def plot_psd(self, analysis_results):
        """绘制功率谱密度"""
        for detector, data in analysis_results.items():
            self.ax.semilogy(data['psd_frequencies'], data['psd_data'], label=f'{detector} 探测器')
        
        self.ax.set_xlabel('频率 (Hz)')
        self.ax.set_ylabel('功率谱密度')
        self.ax.set_title('功率谱密度 (PSD)')
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xscale('log')
    
    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def process_messages(self):
        """处理消息队列"""
        try:
            while True:
                message_type, message_data = self.message_queue.get_nowait()
                
                if message_type == "success":
                    messagebox.showinfo("成功", message_data)
                elif message_type == "error":
                    messagebox.showerror("错误", message_data)
                elif message_type == "load_events":
                    self.load_events()
                elif message_type == "update_stats":
                    self.update_statistics()
                
        except queue.Empty:
            pass
        
        # 每100ms检查一次消息队列
        self.root.after(100, self.process_messages)
    
    def run(self):
        """运行GUI应用"""
        try:
            self.root.mainloop()
        except Exception as e:
            logger.error(f"GUI运行错误: {e}")
        finally:
            plt.close('all')

if __name__ == '__main__':
    app = GWOSCGUI()
    app.run() 
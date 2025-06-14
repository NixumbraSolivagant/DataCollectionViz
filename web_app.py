from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime
import plotly.graph_objs as go
import plotly.utils
import numpy as np

from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, DATA_DIR
from database import DataManager
from data_processor import DataProcessor
from image_crawler import ImageCrawler
from image_processor import ImageProcessor
from image_viewer import ImageManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 初始化组件
db = DataManager()
data_processor = DataProcessor()
image_manager = ImageManager()

@app.route('/')
def index():
    """主页"""
    try:
        # 获取统计信息
        stats = db.get_statistics()
        
        # 获取最新事件
        events = db.get_all_events()[:10]  # 只显示最新10个
        
        # 获取图片统计信息
        image_stats = image_manager.get_image_stats()
        
        return render_template('index.html', stats=stats, events=events, image_stats=image_stats)
    except Exception as e:
        logger.error(f"主页加载失败: {e}")
        return render_template('error.html', error=str(e))

@app.route('/events')
def events():
    """事件列表页面"""
    try:
        events = db.get_all_events()
        return render_template('events.html', events=events)
    except Exception as e:
        logger.error(f"事件列表加载失败: {e}")
        return render_template('error.html', error=str(e))

@app.route('/event/<event_name>')
def event_detail(event_name):
    """事件详情页面"""
    try:
        event = db.get_event_by_name(event_name)
        if not event:
            return render_template('error.html', error="事件不存在")
        
        # 获取下载状态
        download_status = db.get_download_status(event_name)
        
        # 获取可用探测器
        available_detectors = data_processor.get_available_detectors(event_name)
        
        # 获取应变数据信息
        strain_info = data_processor.get_strain_data_info(event_name)
        
        return render_template('event_detail.html', 
                             event=event, 
                             download_status=download_status,
                             available_detectors=available_detectors,
                             strain_info=strain_info)
    except Exception as e:
        logger.error(f"事件详情加载失败: {e}")
        return render_template('error.html', error=str(e))

# 新增图片相关路由
@app.route('/images')
def images():
    """图片库页面"""
    try:
        # 获取图片统计信息
        image_stats = image_manager.get_image_stats()
        
        # 获取图片列表
        raw_images = []
        processed_images = []
        
        raw_dir = os.path.join("images", "raw")
        processed_dir = os.path.join("images", "processed")
        
        if os.path.exists(raw_dir):
            for filename in os.listdir(raw_dir):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')):
                    raw_images.append(filename)
        
        if os.path.exists(processed_dir):
            for filename in os.listdir(processed_dir):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')):
                    processed_images.append(filename)
        
        return render_template('images.html', 
                             image_stats=image_stats,
                             raw_images=raw_images[:20],  # 只显示前20张
                             processed_images=processed_images[:20])
    except Exception as e:
        logger.error(f"图片库页面加载失败: {e}")
        return render_template('error.html', error=str(e))

@app.route('/images/crawl')
def images_crawl():
    """图片爬取页面"""
    try:
        return render_template('images_crawl.html')
    except Exception as e:
        logger.error(f"图片爬取页面加载失败: {e}")
        return render_template('error.html', error=str(e))

@app.route('/images/process')
def images_process():
    """图片处理页面"""
    try:
        # 获取可用的处理操作
        operations = [
            'resize', 'enhance_contrast', 'enhance_sharpness', 'enhance_brightness',
            'gaussian_blur', 'edge_enhancement', 'grayscale', 'sepia', 'vintage',
            'edge_detection', 'watermark'
        ]
        
        return render_template('images_process.html', operations=operations)
    except Exception as e:
        logger.error(f"图片处理页面加载失败: {e}")
        return render_template('error.html', error=str(e))

@app.route('/images/viewer')
def images_viewer():
    """图片查看器页面"""
    try:
        # 获取图片列表
        raw_images = []
        processed_images = []
        
        raw_dir = os.path.join("images", "raw")
        processed_dir = os.path.join("images", "processed")
        
        if os.path.exists(raw_dir):
            for filename in os.listdir(raw_dir):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')):
                    raw_images.append(filename)
        
        if os.path.exists(processed_dir):
            for filename in os.listdir(processed_dir):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')):
                    processed_images.append(filename)
        
        return render_template('images_viewer.html', 
                             raw_images=raw_images,
                             processed_images=processed_images)
    except Exception as e:
        logger.error(f"图片查看器页面加载失败: {e}")
        return render_template('error.html', error=str(e))

# 图片相关的API路由
@app.route('/api/images/stats')
def api_images_stats():
    """API: 获取图片统计信息"""
    try:
        stats = image_manager.get_image_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"API获取图片统计失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/images/crawl', methods=['POST'])
def api_images_crawl():
    """API: 开始爬取图片"""
    try:
        data = request.get_json()
        max_images = data.get('max_images', 50)  # 默认50张
        
        # 创建爬虫实例
        crawler = ImageCrawler(max_images=max_images)
        
        # 在新线程中运行爬取
        import threading
        def crawl_thread():
            try:
                crawler.crawl_images()
            except Exception as e:
                logger.error(f"图片爬取失败: {e}")
        
        thread = threading.Thread(target=crawl_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': f'开始爬取{max_images}张图片'})
    except Exception as e:
        logger.error(f"API图片爬取失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/images/process', methods=['POST'])
def api_images_process():
    """API: 处理图片"""
    try:
        data = request.get_json()
        operations = data.get('operations', ['resize', 'enhance_contrast', 'enhance_sharpness'])
        
        # 创建处理器实例
        processor = ImageProcessor()
        
        # 在新线程中运行处理
        import threading
        def process_thread():
            try:
                processor.batch_process(operations=operations)
            except Exception as e:
                logger.error(f"图片处理失败: {e}")
        
        thread = threading.Thread(target=process_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': f'开始处理图片，操作: {", ".join(operations)}'})
    except Exception as e:
        logger.error(f"API图片处理失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/images/list')
def api_images_list():
    """API: 获取图片列表"""
    try:
        mode = request.args.get('mode', 'processed')  # raw 或 processed
        
        images = []
        if mode == 'raw':
            image_dir = os.path.join("images", "raw")
        else:
            image_dir = os.path.join("images", "processed")
        
        if os.path.exists(image_dir):
            for filename in os.listdir(image_dir):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')):
                    filepath = os.path.join(image_dir, filename)
                    file_size = os.path.getsize(filepath)
                    images.append({
                        'filename': filename,
                        'size': file_size,
                        'url': f'/images/file/{mode}/{filename}'
                    })
        
        return jsonify({'success': True, 'images': images})
    except Exception as e:
        logger.error(f"API获取图片列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/images/file/<mode>/<filename>')
def serve_image(mode, filename):
    """提供图片文件服务"""
    try:
        if mode not in ['raw', 'processed']:
            return jsonify({'success': False, 'error': '无效的模式'})
        
        filepath = os.path.join("images", mode, filename)
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': '文件不存在'})
        
        return send_file(filepath, mimetype='image/jpeg')
    except Exception as e:
        logger.error(f"提供图片文件失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/events')
def api_events():
    """API: 获取事件列表"""
    try:
        events = db.get_all_events()
        return jsonify({'success': True, 'events': events})
    except Exception as e:
        logger.error(f"API获取事件列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/event/<event_name>')
def api_event_detail(event_name):
    """API: 获取事件详情"""
    try:
        event = db.get_event_by_name(event_name)
        if not event:
            return jsonify({'success': False, 'error': '事件不存在'})
        
        # 获取可用探测器
        available_detectors = data_processor.get_available_detectors(event_name)
        # 转换为对象格式
        detector_objects = [{'name': detector} for detector in available_detectors]
        
        # 获取应变数据信息
        strain_info = data_processor.get_strain_data_info(event_name)
        
        return jsonify({
            'success': True, 
            'event': event,
            'available_detectors': detector_objects,
            'strain_info': strain_info
        })
    except Exception as e:
        logger.error(f"API获取事件详情失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/event/<event_name>/data')
def api_event_data(event_name):
    """API: 获取事件数据"""
    try:
        # 获取请求的探测器
        detectors = request.args.get('detectors')
        if detectors:
            detectors = detectors.split(',')
        
        # 分析事件数据
        analysis_results = data_processor.analyze_event_data(event_name, detectors)
        if not analysis_results:
            return jsonify({'success': False, 'error': '没有找到数据文件'})
        
        # 创建可视化数据
        viz_data = data_processor.create_visualization_data(analysis_results)
        if not viz_data:
            return jsonify({'success': False, 'error': '无法创建可视化数据'})
        
        return jsonify({'success': True, 'data': viz_data})
    except Exception as e:
        logger.error(f"API获取事件数据失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/statistics')
def api_statistics():
    """API: 获取统计信息"""
    try:
        stats = db.get_statistics()
        return jsonify({'success': True, 'statistics': stats})
    except Exception as e:
        logger.error(f"API获取统计信息失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/search')
def api_search():
    """API: 搜索事件"""
    try:
        criteria = {}
        
        # 按名称搜索
        name = request.args.get('name')
        if name:
            criteria['name'] = name
        
        # 按探测器搜索
        detector = request.args.get('detector')
        if detector:
            criteria['detector'] = detector
        
        # 按质量范围搜索
        min_mass = request.args.get('min_mass')
        max_mass = request.args.get('max_mass')
        if min_mass and max_mass:
            criteria['mass_range'] = [float(min_mass), float(max_mass)]
        
        results = db.search_events(criteria)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        logger.error(f"API搜索事件失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/visualization/<event_name>')
def visualization(event_name):
    """可视化页面"""
    try:
        event = db.get_event_by_name(event_name)
        if not event:
            return render_template('error.html', error="事件不存在")
        
        # 获取可用探测器
        available_detectors = data_processor.get_available_detectors(event_name)
        
        return render_template('visualization.html', 
                             event=event, 
                             available_detectors=available_detectors)
    except Exception as e:
        logger.error(f"可视化页面加载失败: {e}")
        return render_template('error.html', error=str(e))

@app.route('/api/plot/<event_name>/<plot_type>')
def api_plot(event_name, plot_type):
    """API: 生成图表数据"""
    try:
        # 获取请求的探测器
        detectors = request.args.get('detectors')
        if detectors:
            detectors = detectors.split(',')
        logger.info(f"API /api/plot/{event_name}/{plot_type} 请求参数: detectors={detectors}")
        
        # 分析事件数据
        analysis_results = data_processor.analyze_event_data(event_name, detectors)
        if not analysis_results:
            logger.error(f"没有找到数据文件: event={event_name}, detectors={detectors}")
            return jsonify({'success': False, 'error': '没有找到数据文件'})
        
        # 创建可视化数据
        viz_data = data_processor.create_visualization_data(analysis_results)
        if not viz_data:
            logger.error(f"无法创建可视化数据: event={event_name}, detectors={detectors}")
            return jsonify({'success': False, 'error': '无法创建可视化数据'})
        
        logger.info(f"viz_data: {json.dumps(viz_data)[:500]}")
        
        # 根据图表类型生成数据
        plot_data = None
        if plot_type == 'time_series':
            plot_data = generate_time_series_plot(viz_data)
        elif plot_type == 'fft':
            plot_data = generate_fft_plot(viz_data)
        elif plot_type == 'psd':
            plot_data = generate_psd_plot(viz_data)
        else:
            logger.error(f"不支持的图表类型: {plot_type}")
            return jsonify({'success': False, 'error': '不支持的图表类型'})
        
        if not plot_data:
            logger.error(f"生成图表数据失败: event={event_name}, plot_type={plot_type}")
            return jsonify({'success': False, 'error': '生成图表数据失败'})
        
        # 确保返回的是有效的JSON数据
        try:
            # 如果plot_data已经是字符串，尝试解析它
            if isinstance(plot_data, str):
                plot_data = json.loads(plot_data)
            # 如果plot_data是字典，直接使用
            elif isinstance(plot_data, dict):
                pass
            # 其他情况，尝试序列化
            else:
                plot_data = json.loads(json.dumps(plot_data))
            
            logger.info(f"plot_data: {json.dumps(plot_data)[:500]}")
            return jsonify({'success': True, 'plot_data': plot_data})
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return jsonify({'success': False, 'error': '图表数据格式错误'})
            
    except Exception as e:
        logger.error(f"API生成图表失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})

def generate_time_series_plot(viz_data):
    """生成时间序列图表数据"""
    try:
        traces = []
        if 'detectors' in viz_data:
            for detector, det_data in viz_data['detectors'].items():
                ts = det_data.get('time_series', {})
                logger.info(f"{detector} time_series: time({len(ts.get('time', []))}), processed_data({len(ts.get('processed_data', []))})")
                if ts and 'time' in ts and 'processed_data' in ts and len(ts['time']) > 0 and len(ts['processed_data']) > 0:
                    trace = go.Scatter(
                        x=ts['time'],
                        y=ts['processed_data'],
                        mode='lines',
                        name=f'{detector} 应变数据',
                        line=dict(width=1)
                    )
                    traces.append(trace)
        if not traces:
            logger.error("No valid traces for time series plot.")
            return None
            
        layout = go.Layout(
            title='引力波应变数据时间序列',
            xaxis=dict(
                title='时间 (秒)',
                gridcolor='lightgray',
                showgrid=True
            ),
            yaxis=dict(
                title='应变',
                gridcolor='lightgray',
                showgrid=True
            ),
            plot_bgcolor='white',
            hovermode='closest',
            showlegend=True,
            legend=dict(
                x=0.01,
                y=0.99,
                bgcolor='rgba(255, 255, 255, 0.8)'
            )
        )
        
        fig = go.Figure(data=traces, layout=layout)
        plot_data = json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
        
        # 添加图表配置
        plot_data['config'] = {
            'displayModeBar': True,
            'modeBarButtonsToRemove': [
                'select2d',
                'lasso2d',
                'toggleSpikelines'
            ],
            'displaylogo': False,
            'scrollZoom': True
        }
        
        logger.info(f"plot_data: {json.dumps(plot_data)[:500]}")
        return plot_data
    except Exception as e:
        logger.error(f"生成时间序列图表失败: {e}", exc_info=True)
        return None

def generate_fft_plot(viz_data):
    """生成FFT图表数据"""
    try:
        traces = []
        if 'detectors' in viz_data:
            for detector, det_data in viz_data['detectors'].items():
                fft = det_data.get('fft', {})
                if fft and 'frequencies' in fft and 'magnitude' in fft:
                    logger.info(f"{detector} fft: frequencies({len(fft['frequencies'])}), magnitude({len(fft['magnitude'])})")
                    # 只显示 10Hz 以上的频率
                    mask = np.array(fft['frequencies']) >= 10
                    frequencies = np.array(fft['frequencies'])[mask]
                    magnitude = np.array(fft['magnitude'])[mask]
                    
                    trace = go.Scatter(
                        x=frequencies,
                        y=magnitude,
                        mode='lines',
                        name=f'{detector} FFT',
                        line=dict(width=1)
                    )
                    traces.append(trace)
        
        if not traces:
            logger.error("No valid traces for FFT plot.")
            return None
            
        layout = go.Layout(
            title='快速傅里叶变换 (FFT)',
            xaxis=dict(
                title='频率 (Hz)',
                type='log',
                range=[np.log10(10), np.log10(2000)],
                gridcolor='lightgray',
                showgrid=True
            ),
            yaxis=dict(
                title='幅度',
                type='log',
                gridcolor='lightgray',
                showgrid=True
            ),
            plot_bgcolor='white',
            hovermode='closest',
            showlegend=True,
            legend=dict(
                x=0.01,
                y=0.99,
                bgcolor='rgba(255, 255, 255, 0.8)'
            )
        )
        
        fig = go.Figure(data=traces, layout=layout)
        plot_data = json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
        
        # 添加图表配置
        plot_data['config'] = {
            'displayModeBar': True,
            'modeBarButtonsToRemove': [
                'select2d',
                'lasso2d',
                'toggleSpikelines'
            ],
            'displaylogo': False,
            'scrollZoom': True
        }
        
        return plot_data
    except Exception as e:
        logger.error(f"生成FFT图表失败: {e}", exc_info=True)
        return None

def generate_psd_plot(viz_data):
    """生成功率谱密度图表数据"""
    try:
        traces = []
        if 'detectors' in viz_data:
            for detector, det_data in viz_data['detectors'].items():
                psd = det_data.get('psd', {})
                if psd and 'frequencies' in psd and 'power' in psd:
                    logger.info(f"{detector} psd: frequencies({len(psd['frequencies'])}), power({len(psd['power'])})")
                    # 只显示 10Hz 以上的频率
                    mask = np.array(psd['frequencies']) >= 10
                    frequencies = np.array(psd['frequencies'])[mask]
                    power = np.array(psd['power'])[mask]
                    
                    trace = go.Scatter(
                        x=frequencies,
                        y=power,
                        mode='lines',
                        name=f'{detector} PSD',
                        line=dict(width=1)
                    )
                    traces.append(trace)
        
        if not traces:
            logger.error("No valid traces for PSD plot.")
            return None
            
        layout = go.Layout(
            title='功率谱密度 (PSD)',
            xaxis=dict(
                title='频率 (Hz)',
                type='log',
                range=[np.log10(10), np.log10(2000)],
                gridcolor='lightgray',
                showgrid=True
            ),
            yaxis=dict(
                title='功率谱密度 (1/Hz)',
                type='log',
                gridcolor='lightgray',
                showgrid=True
            ),
            plot_bgcolor='white',
            hovermode='closest',
            showlegend=True,
            legend=dict(
                x=0.01,
                y=0.99,
                bgcolor='rgba(255, 255, 255, 0.8)'
            )
        )
        
        fig = go.Figure(data=traces, layout=layout)
        plot_data = json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
        
        # 添加图表配置
        plot_data['config'] = {
            'displayModeBar': True,
            'modeBarButtonsToRemove': [
                'select2d',
                'lasso2d',
                'toggleSpikelines'
            ],
            'displaylogo': False,
            'scrollZoom': True
        }
        
        return plot_data
    except Exception as e:
        logger.error(f"生成PSD图表失败: {e}", exc_info=True)
        return None

@app.route('/download/<event_name>/<filename>')
def download_file(event_name, filename):
    """下载文件"""
    try:
        filepath = os.path.join(DATA_DIR, event_name, filename)
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': '文件不存在'})
        
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        logger.error(f"文件下载失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/event/<event_name>/analyze')
def api_analyze_event(event_name):
    """API: 分析事件数据"""
    try:
        # 获取请求的探测器
        detectors = request.args.get('detectors')
        if detectors:
            detectors = detectors.split(',')
        logger.info(f"API /api/event/{event_name}/analyze 请求参数: detectors={detectors}")
        
        # 分析事件数据
        analysis_results = data_processor.analyze_event_data(event_name, detectors)
        if not analysis_results:
            logger.error(f"没有找到数据文件: event={event_name}, detectors={detectors}")
            return jsonify({'success': False, 'error': '没有找到数据文件'})
        
        # 创建可视化数据
        viz_data = data_processor.create_visualization_data(analysis_results)
        if not viz_data:
            logger.error(f"无法创建可视化数据: event={event_name}, detectors={detectors}")
            return jsonify({'success': False, 'error': '无法创建可视化数据'})
        
        # 生成所有类型的图表数据
        time_series_plot = generate_time_series_plot(viz_data)
        fft_plot = generate_fft_plot(viz_data)
        psd_plot = generate_psd_plot(viz_data)
        
        if not all([time_series_plot, fft_plot, psd_plot]):
            logger.error(f"生成图表数据失败: event={event_name}")
            return jsonify({'success': False, 'error': '生成图表数据失败'})
        
        # 提取统计信息
        statistics = {}
        for detector, det_data in viz_data['detectors'].items():
            if 'statistics' in det_data:
                stats = det_data['statistics']
                # 确保所有数值都是可序列化的
                statistics[detector] = {
                    'time_domain': {
                        k: float(v) if isinstance(v, (np.floating, float)) else v
                        for k, v in stats['time_domain'].items()
                    },
                    'frequency_domain': {
                        k: [float(x) if isinstance(x, (np.floating, float)) else x for x in v]
                        if isinstance(v, list) else float(v) if isinstance(v, (np.floating, float)) else v
                        for k, v in stats['frequency_domain'].items()
                    },
                    'psd': {
                        k: float(v) if isinstance(v, (np.floating, float)) else v
                        for k, v in stats['psd'].items()
                    }
                }
        
        return jsonify({
            'success': True,
            'statistics': statistics,
            'plots': {
                'time_series': time_series_plot,
                'fft': fft_plot,
                'psd': psd_plot
            }
        })
            
    except Exception as e:
        logger.error(f"API分析事件数据失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="页面未找到"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="服务器内部错误"), 500

if __name__ == '__main__':
    logger.info(f"启动Web应用: http://{FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
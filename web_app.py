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

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 初始化组件
db = DataManager()
data_processor = DataProcessor()

@app.route('/')
def index():
    """主页"""
    try:
        # 获取统计信息
        stats = db.get_statistics()
        
        # 获取最新事件
        events = db.get_all_events()[:10]  # 只显示最新10个
        
        return render_template('index.html', stats=stats, events=events)
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
        
        analysis_results = data_processor.analyze_event_data(event_name, detectors)
        if not analysis_results:
            return jsonify({'success': False, 'error': '没有找到数据文件'})
        
        viz_data = data_processor.create_visualization_data(analysis_results)
        if not viz_data:
            return jsonify({'success': False, 'error': '无法创建可视化数据'})
        
        if plot_type == 'time_series':
            return jsonify({'success': True, 'data': generate_time_series_plot(viz_data)})
        elif plot_type == 'fft':
            return jsonify({'success': True, 'data': generate_fft_plot(viz_data)})
        elif plot_type == 'psd':
            return jsonify({'success': True, 'data': generate_psd_plot(viz_data)})
        else:
            return jsonify({'success': False, 'error': '不支持的图表类型'})
            
    except Exception as e:
        logger.error(f"生成图表失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

def generate_time_series_plot(viz_data):
    """生成时间序列图"""
    try:
        fig = go.Figure()
        
        for detector, data in viz_data['detectors'].items():
            # 原始数据
            fig.add_trace(go.Scatter(
                x=data['time_series']['time'],
                y=data['time_series']['raw_data'],
                mode='lines',
                name=f'{detector} 原始数据',
                line=dict(width=1, color='lightblue'),
                opacity=0.7
            ))
            
            # 处理后数据
            if data['time_series']['processed_data']:
                fig.add_trace(go.Scatter(
                    x=data['time_series']['time'],
                    y=data['time_series']['processed_data'],
                    mode='lines',
                    name=f'{detector} 处理后数据',
                    line=dict(width=2, color='red')
                ))
            
            # 峰值标记
            if data['peaks']['times']:
                fig.add_trace(go.Scatter(
                    x=data['peaks']['times'],
                    y=data['peaks']['amplitudes'],
                    mode='markers',
                    name=f'{detector} 峰值',
                    marker=dict(size=8, color='orange', symbol='diamond')
                ))
        
        fig.update_layout(
            title='引力波时间序列数据',
            xaxis_title='时间 (秒)',
            yaxis_title='振幅',
            template='plotly_white',
            height=600,
            showlegend=True
        )
        
        return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
    except Exception as e:
        logger.error(f"生成时间序列图失败: {e}")
        return None

def generate_fft_plot(viz_data):
    """生成FFT图"""
    try:
        fig = go.Figure()
        
        for detector, data in viz_data['detectors'].items():
            if data['fft']['frequencies'] and data['fft']['magnitude']:
                fig.add_trace(go.Scatter(
                    x=data['fft']['frequencies'],
                    y=data['fft']['magnitude'],
                    mode='lines',
                    name=f'{detector} 探测器',
                    line=dict(width=2)
                ))
        
        fig.update_layout(
            title='快速傅里叶变换 (FFT)',
            xaxis_title='频率 (Hz)',
            yaxis_title='幅度',
            template='plotly_white',
            height=500,
            xaxis_type='log',
            yaxis_type='log'
        )
        
        return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
    except Exception as e:
        logger.error(f"生成FFT图失败: {e}")
        return None

def generate_psd_plot(viz_data):
    """生成功率谱密度图"""
    try:
        fig = go.Figure()
        
        for detector, data in viz_data['detectors'].items():
            if data['psd']['frequencies'] and data['psd']['power']:
                fig.add_trace(go.Scatter(
                    x=data['psd']['frequencies'],
                    y=data['psd']['power'],
                    mode='lines',
                    name=f'{detector} 探测器',
                    line=dict(width=2)
                ))
        
        fig.update_layout(
            title='功率谱密度 (PSD)',
            xaxis_title='频率 (Hz)',
            yaxis_title='功率谱密度',
            template='plotly_white',
            height=500,
            xaxis_type='log',
            yaxis_type='log'
        )
        
        return json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig))
    except Exception as e:
        logger.error(f"生成PSD图失败: {e}")
        return None

@app.route('/download/<event_name>/<filename>')
def download_file(event_name, filename):
    """下载文件"""
    try:
        file_path = os.path.join(DATA_DIR, event_name, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'success': False, 'error': '文件不存在'})
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="页面不存在"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="服务器内部错误"), 500

if __name__ == '__main__':
    logger.info(f"启动Web应用: http://{FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
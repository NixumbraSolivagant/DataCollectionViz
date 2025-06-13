// 全局变量
let currentEvent = null;
let currentDetectors = [];

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 初始化应用
function initializeApp() {
    // 绑定事件监听器
    bindEventListeners();
    
    // 如果是事件详情页面，加载事件数据
    if (window.location.pathname.includes('/event/')) {
        const eventName = getEventNameFromUrl();
        if (eventName) {
            loadEventData(eventName);
        }
    }
    
    // 如果是可视化页面，初始化图表
    if (window.location.pathname.includes('/visualization/')) {
        const eventName = getEventNameFromUrl();
        if (eventName) {
            initializeVisualization(eventName);
        }
    }
}

// 绑定事件监听器
function bindEventListeners() {
    // 搜索表单
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearch);
    }
    
    // 探测器选择
    const detectorSelects = document.querySelectorAll('.detector-select');
    detectorSelects.forEach(select => {
        select.addEventListener('change', handleDetectorChange);
    });
    
    // 图表类型切换
    const chartTypeSelects = document.querySelectorAll('.chart-type-select');
    chartTypeSelects.forEach(select => {
        select.addEventListener('change', handleChartTypeChange);
    });
}

// 从URL获取事件名称
function getEventNameFromUrl() {
    const pathParts = window.location.pathname.split('/');
    const eventIndex = pathParts.indexOf('event') + 1;
    return eventIndex < pathParts.length ? pathParts[eventIndex] : null;
}

// 处理搜索
function handleSearch(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const searchParams = new URLSearchParams();
    
    for (let [key, value] of formData.entries()) {
        if (value) {
            searchParams.append(key, value);
        }
    }
    
    // 发送搜索请求
    fetch(`/api/search?${searchParams.toString()}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displaySearchResults(data.results);
            } else {
                showError('搜索失败: ' + data.error);
            }
        })
        .catch(error => {
            showError('搜索请求失败: ' + error.message);
        });
}

// 显示搜索结果
function displaySearchResults(results) {
    const resultsContainer = document.getElementById('searchResults');
    if (!resultsContainer) return;
    
    if (results.length === 0) {
        resultsContainer.innerHTML = '<p>没有找到匹配的事件</p>';
        return;
    }
    
    let html = '<div class="table-responsive"><table class="table">';
    html += '<thead><tr><th>事件名称</th><th>GPS时间</th><th>质量1</th><th>质量2</th><th>距离</th><th>操作</th></tr></thead><tbody>';
    
    results.forEach(event => {
        html += `<tr>
            <td>${event.name}</td>
            <td>${event.gps_time || 'N/A'}</td>
            <td>${event.mass1 || 'N/A'}</td>
            <td>${event.mass2 || 'N/A'}</td>
            <td>${event.distance || 'N/A'}</td>
            <td>
                <a href="/event/${event.name}" class="btn btn-primary btn-sm">详情</a>
                <a href="/visualization/${event.name}" class="btn btn-info btn-sm">可视化</a>
            </td>
        </tr>`;
    });
    
    html += '</tbody></table></div>';
    resultsContainer.innerHTML = html;
}

// 加载事件数据
function loadEventData(eventName) {
    showLoading('正在加载事件数据...');
    
    fetch(`/api/event/${eventName}`)
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                displayEventData(data);
            } else {
                showError('加载事件数据失败: ' + data.error);
            }
        })
        .catch(error => {
            hideLoading();
            showError('请求失败: ' + error.message);
        });
}

// 显示事件数据
function displayEventData(data) {
    currentEvent = data.event;
    
    // 更新事件信息
    updateEventInfo(data.event);
    
    // 更新探测器信息
    updateDetectorInfo(data.available_detectors);
    
    // 更新应变数据信息
    updateStrainInfo(data.strain_info);
}

// 更新事件信息
function updateEventInfo(event) {
    const eventInfoContainer = document.getElementById('eventInfo');
    if (!eventInfoContainer) return;
    
    eventInfoContainer.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">事件信息</h3>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <p><strong>事件名称:</strong> ${event.name}</p>
                    <p><strong>GPS时间:</strong> ${event.gps_time || 'N/A'}</p>
                    <p><strong>质量1:</strong> ${event.mass1 || 'N/A'}</p>
                    <p><strong>质量2:</strong> ${event.mass2 || 'N/A'}</p>
                </div>
                <div class="col-md-6">
                    <p><strong>距离:</strong> ${event.distance || 'N/A'}</p>
                    <p><strong>置信度:</strong> ${event.confidence || 'N/A'}</p>
                    <p><strong>类型:</strong> ${event.event_type || 'N/A'}</p>
                </div>
            </div>
        </div>
    `;
}

// 更新探测器信息
function updateDetectorInfo(detectors) {
    const detectorContainer = document.getElementById('detectorInfo');
    if (!detectorContainer) return;
    
    if (!detectors || detectors.length === 0) {
        detectorContainer.innerHTML = '<p>没有可用的探测器数据</p>';
        return;
    }
    
    let html = '<div class="card"><div class="card-header"><h4 class="card-title">可用探测器</h4></div>';
    html += '<div class="row">';
    
    detectors.forEach(detector => {
        html += `
            <div class="col-md-4 mb-3">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">${detector.name}</h5>
                        <p><strong>采样率:</strong> ${detector.sample_rate} Hz</p>
                        <p><strong>数据点:</strong> ${detector.data_points}</p>
                        <p><strong>文件大小:</strong> ${formatFileSize(detector.file_size)}</p>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div></div>';
    detectorContainer.innerHTML = html;
}

// 更新应变数据信息
function updateStrainInfo(strainInfo) {
    const strainContainer = document.getElementById('strainInfo');
    if (!strainContainer) return;
    
    if (!strainInfo || Object.keys(strainInfo).length === 0) {
        strainContainer.innerHTML = '<p>没有应变数据信息</p>';
        return;
    }
    
    let html = '<div class="card"><div class="card-header"><h4 class="card-title">应变数据统计</h4></div>';
    html += '<div class="table-responsive"><table class="table">';
    html += '<thead><tr><th>探测器</th><th>均值</th><th>标准差</th><th>最小值</th><th>最大值</th><th>RMS</th></tr></thead><tbody>';
    
    Object.entries(strainInfo).forEach(([detector, stats]) => {
        html += `<tr>
            <td>${detector}</td>
            <td>${formatNumber(stats.mean)}</td>
            <td>${formatNumber(stats.std)}</td>
            <td>${formatNumber(stats.min)}</td>
            <td>${formatNumber(stats.max)}</td>
            <td>${formatNumber(stats.rms)}</td>
        </tr>`;
    });
    
    html += '</tbody></table></div></div>';
    strainContainer.innerHTML = html;
}

// 初始化可视化
function initializeVisualization(eventName) {
    currentEvent = eventName;
    
    // 加载可用探测器
    loadAvailableDetectors(eventName);
    
    // 初始化图表
    initializeCharts();
}

// 加载可用探测器
function loadAvailableDetectors(eventName) {
    fetch(`/api/event/${eventName}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.available_detectors) {
                updateDetectorSelect(data.available_detectors);
            }
        })
        .catch(error => {
            showError('加载探测器信息失败: ' + error.message);
        });
}

// 更新探测器选择
function updateDetectorSelect(detectors) {
    const select = document.getElementById('detectorSelect');
    if (!select) return;
    
    select.innerHTML = '<option value="">选择探测器</option>';
    detectors.forEach(detector => {
        select.innerHTML += `<option value="${detector.name}">${detector.name}</option>`;
    });
}

// 初始化图表
function initializeCharts() {
    // 这里可以初始化各种图表
    // 例如：时间序列图、FFT图、功率谱密度图等
}

// 处理探测器变化
function handleDetectorChange(event) {
    const detector = event.target.value;
    if (detector && currentEvent) {
        loadChartData(currentEvent, detector);
    }
}

// 加载图表数据
function loadChartData(eventName, detector) {
    showLoading('正在加载图表数据...');
    
    fetch(`/api/event/${eventName}/data?detectors=${detector}`)
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                renderCharts(data.data);
            } else {
                showError('加载图表数据失败: ' + data.error);
            }
        })
        .catch(error => {
            hideLoading();
            showError('请求失败: ' + error.message);
        });
}

// 渲染图表
function renderCharts(data) {
    // 渲染时间序列图
    if (data.time_series) {
        renderTimeSeriesChart(data.time_series);
    }
    
    // 渲染FFT图
    if (data.fft) {
        renderFFTChart(data.fft);
    }
    
    // 渲染功率谱密度图
    if (data.psd) {
        renderPSDChart(data.psd);
    }
}

// 渲染时间序列图
function renderTimeSeriesChart(data) {
    const container = document.getElementById('timeSeriesChart');
    if (!container) return;
    
    const trace = {
        x: data.time,
        y: data.strain,
        type: 'scatter',
        mode: 'lines',
        name: '应变数据',
        line: {color: '#007bff'}
    };
    
    const layout = {
        title: '时间序列图',
        xaxis: {title: '时间 (s)'},
        yaxis: {title: '应变'},
        height: 400
    };
    
    Plotly.newPlot(container, [trace], layout);
}

// 渲染FFT图
function renderFFTChart(data) {
    const container = document.getElementById('fftChart');
    if (!container) return;
    
    const trace = {
        x: data.frequency,
        y: data.magnitude,
        type: 'scatter',
        mode: 'lines',
        name: 'FFT幅度',
        line: {color: '#28a745'}
    };
    
    const layout = {
        title: '快速傅里叶变换',
        xaxis: {title: '频率 (Hz)'},
        yaxis: {title: '幅度'},
        height: 400
    };
    
    Plotly.newPlot(container, [trace], layout);
}

// 渲染功率谱密度图
function renderPSDChart(data) {
    const container = document.getElementById('psdChart');
    if (!container) return;
    
    const trace = {
        x: data.frequency,
        y: data.psd,
        type: 'scatter',
        mode: 'lines',
        name: '功率谱密度',
        line: {color: '#dc3545'}
    };
    
    const layout = {
        title: '功率谱密度',
        xaxis: {title: '频率 (Hz)'},
        yaxis: {title: 'PSD (1/Hz)'},
        height: 400
    };
    
    Plotly.newPlot(container, [trace], layout);
}

// 显示加载状态
function showLoading(message = '加载中...') {
    const loadingDiv = document.getElementById('loading');
    if (loadingDiv) {
        loadingDiv.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>${message}</p>
            </div>
        `;
        loadingDiv.style.display = 'block';
    }
}

// 隐藏加载状态
function hideLoading() {
    const loadingDiv = document.getElementById('loading');
    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }
}

// 显示错误信息
function showError(message) {
    const errorDiv = document.getElementById('error');
    if (errorDiv) {
        errorDiv.innerHTML = `
            <div class="alert alert-danger">
                <strong>错误:</strong> ${message}
            </div>
        `;
        errorDiv.style.display = 'block';
    } else {
        alert('错误: ' + message);
    }
}

// 格式化数字
function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    return Number(num).toExponential(3);
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
} 
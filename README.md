# 引力波数据爬虫与可视化系统

一个完整的引力波数据爬虫和可视化系统，用于爬取GWOSC（引力波开放科学中心）的引力波事件数据，并提供强大的数据分析和可视化功能。

## 功能特性

### 🕷️ 网页爬虫
- 自动爬取GWOSC事件列表
- 下载32秒16KHz的txt数据文件
- 支持多探测器数据（H1, L1, V1, K1）
- 智能重试机制和错误处理

### 🗄️ 数据存储
- 本地文件存储事件信息
- JSON格式数据文件
- 文件下载记录和状态跟踪
- 完整的日志记录系统

### 📊 数据分析
- 数据预处理（去均值、窗函数、滤波）
- 快速傅里叶变换（FFT）
- 功率谱密度（PSD）分析
- 峰值检测和统计信息

### 🌐 Web可视化
- Flask Web应用
- 交互式Plotly图表
- 响应式Bootstrap界面
- RESTful API接口

### 🖥️ 桌面GUI
- Tkinter图形界面
- 实时数据可视化
- 多线程操作支持
- 进度显示和状态更新

### 🛡️ 异常处理
- 完善的错误处理机制
- 详细的日志记录
- 优雅的异常恢复

## 系统要求

- Python 3.8+
- 操作系统：Windows, macOS, Linux

## 安装依赖

```bash
# 安装Python依赖包
pip install -r requirements.txt
```

## 快速开始

### 1. 设置环境

```bash
python main.py --setup
```

### 2. 爬取事件列表

```bash
python main.py --crawl
```

### 3. 启动Web应用

```bash
python main.py --web
```

然后在浏览器中访问：http://127.0.0.1:5000

### 4. 启动桌面GUI

```bash
python main.py --gui
```

## 详细使用说明

### 命令行选项

```bash
# 显示帮助信息
python main.py --help

# 爬取事件列表
python main.py --crawl

# 下载指定事件数据
python main.py --download GW150914

# 分析指定事件数据
python main.py --analyze GW150914

# 启动Web应用
python main.py --web

# 启动GUI应用
python main.py --gui

# 设置运行环境
python main.py --setup
```

### Web应用功能

1. **首页** - 系统概览和统计信息
2. **事件列表** - 所有引力波事件列表
3. **事件详情** - 单个事件的详细信息
4. **数据可视化** - 交互式图表展示
   - 时间序列图
   - FFT频谱图
   - 功率谱密度图

### GUI应用功能

1. **控制面板** - 数据爬取和分析控制
2. **事件列表** - 事件搜索和选择
3. **事件详情** - 事件信息显示
4. **数据可视化** - 实时图表展示

## 项目结构

```
python_web/
├── main.py              # 主程序入口
├── config.py            # 配置文件
├── requirements.txt     # 依赖包列表
├── README.md           # 项目文档
├── database.py         # 数据管理模块
├── crawler.py          # 网页爬虫模块
├── data_processor.py   # 数据处理模块
├── web_app.py          # Flask Web应用
├── gui_app.py          # Tkinter GUI应用
├── templates/          # HTML模板
│   ├── base.html
│   ├── index.html
│   └── visualization.html
├── static/             # 静态文件
│   ├── css/
│   └── js/
├── data/               # 数据存储目录
│   ├── events.json     # 事件数据文件
│   ├── files/          # 下载的数据文件
│   └── download_log.json # 下载日志
├── cache/              # 缓存目录
└── logs/               # 日志目录
```

## 数据格式

### 事件数据
- 事件名称（如：GW150914）
- GPS时间
- 质量参数（M☉）
- 距离（Mpc）
- 网络信噪比
- 其他物理参数

### 数据文件
- 格式：32秒16KHz的txt文件
- 采样率：16,384 Hz
- 数据长度：524,288个数据点
- 探测器：H1, L1, V1, K1

## API接口

### 获取事件列表
```
GET /api/events
```

### 获取事件数据
```
GET /api/event/{event_name}/data
```

### 获取统计信息
```
GET /api/statistics
```

### 生成图表
```
GET /api/plot/{event_name}/{plot_type}
```

## 技术栈

- **后端框架**: Flask
- **数据存储**: 本地文件 (JSON)
- **数据处理**: NumPy, SciPy, Pandas
- **可视化**: Plotly, Matplotlib
- **GUI框架**: Tkinter
- **Web框架**: Bootstrap
- **爬虫**: Requests, BeautifulSoup

## 开发说明

### 添加新功能

1. 在相应模块中添加功能代码
2. 更新配置文件（如需要）
3. 添加相应的API接口（Web应用）
4. 更新GUI界面（桌面应用）
5. 添加测试用例

### 调试模式

```bash
# 启用详细日志
export PYTHONPATH=.
python main.py --web --debug
```

## 故障排除

### 常见问题

1. **依赖包安装失败**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **数据文件权限错误**
   - 检查data目录权限
   - 确保有写入权限

3. **网络连接问题**
   - 检查网络连接
   - 配置代理设置（如需要）

4. **内存不足**
   - 减少同时处理的数据量
   - 增加系统内存

### 日志查看

```bash
# 查看系统日志
tail -f logs/gwosc_system.log
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交Issue
- 发送邮件
- 参与讨论

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 基本爬虫功能
- Web和GUI界面
- 数据分析和可视化

---

**注意**: 本项目仅用于教育和研究目的。请遵守GWOSC的数据使用政策。 
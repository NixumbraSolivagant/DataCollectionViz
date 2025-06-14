# 引力波数据爬虫与可视化系统

本项目为课程结课作业，旨在实现一个自动化的引力波数据与主题图片爬取、分析和可视化平台。
系统集成了数据采集、处理、Web展示和桌面GUI，适合教学、科研和兴趣探索。


## 主要功能

### 网页爬虫
- 自动爬取GWOSC事件列表
- 下载32秒16KHz的txt数据文件
- 支持多探测器数据（H1, L1, V1, K1）
- 智能重试机制和错误处理

### 数据存储
- 本地文件存储事件信息
- JSON格式数据文件
- 文件下载记录和状态跟踪
- 完整的日志记录系统

### 数据分析
- 数据预处理（去均值、窗函数、滤波）
- 快速傅里叶变换（FFT）
- 功率谱密度（PSD）分析
- 峰值检测和统计信息

### 图片处理
- 通过Pexels API批量下载主题图片
- 自动图片预处理（缩放、增强、格式转换）
- 支持多种图片格式（JPG、PNG、WebP）
- 图片元数据提取和管理
- 图片分类与标签管理
- 图片缓存与本地存储

### Web可视化
- Flask Web应用
- 交互式Plotly图表
- 响应式Bootstrap界面
- RESTful API接口

### 桌面GUI
- Tkinter图形界面
- 实时数据可视化
- 多线程操作支持
- 进度显示和状态更新

### 异常处理
- 完善的错误处理机制
- 详细的日志记录
- 优雅的异常恢复

---

## 系统要求

- Python 3.8+
- 操作系统：Windows, macOS, Linux

## 快速开始

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置参数**
   - 编辑 `config.py`，填写API KEY、关键词等参数

3. **命令行选项**
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

## 技术栈

- **后端框架**: Flask
- **数据存储**: 本地文件 (JSON)
- **数据处理**: NumPy, SciPy, Pandas
- **可视化**: Plotly, Matplotlib
- **GUI框架**: Tkinter
- **Web框架**: Bootstrap
- **爬虫**: Requests, BeautifulSoup

## 致谢
感谢GWOSC、Pexels等开放平台提供的数据与API支持。


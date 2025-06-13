# 系统配置文件
import os

# 基础配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# 创建必要的目录
for directory in [DATA_DIR, CACHE_DIR, LOGS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# GWOSC API配置
GWOSC_BASE_URL = "https://gwosc.org/eventapi/html/allevents/"
GWOSC_DATA_URL = "https://gwosc.org/eventapi/json/allevents/"
GWOSC_DOWNLOAD_BASE = "https://gwosc.org/eventapi/json/"

# 数据文件配置
EVENTS_FILE = os.path.join(DATA_DIR, 'events.json')
DATA_FILES_DIR = os.path.join(DATA_DIR, 'files')
DOWNLOAD_LOG_FILE = os.path.join(DATA_DIR, 'download_log.json')

# Flask配置
FLASK_HOST = '127.0.0.1'
FLASK_PORT = 5000
FLASK_DEBUG = True

# 爬虫配置
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
CHUNK_SIZE = 8192

# 数据配置
SAMPLE_RATE = 16384  # 16KHz
DURATION = 32  # 32秒

# 日志配置
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = os.path.join(LOGS_DIR, 'gwosc_system.log')

# 界面配置
GUI_TITLE = "引力波数据爬虫与可视化系统"
GUI_WIDTH = 1200
GUI_HEIGHT = 800

# 可视化配置
PLOT_THEME = 'plotly_white'
PLOT_HEIGHT = 600
PLOT_WIDTH = 800 
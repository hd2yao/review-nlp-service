import os

# 服务配置
SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 8000))

# 模型配置
MODEL_PATH = os.getenv("MODEL_PATH", "models")

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
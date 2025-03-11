# Review NLP Service

基于 FastAPI 的评论文本分析服务，提供情感分析和内容审核功能。

## 功能特性

- 情感分析：分析评论文本的情感倾向（积极、中性、消极）
- 内容审核：检测不当内容和敏感词
- 支持单条和批量评论处理
- 缓存机制提升性能
- RESTful API 接口
- 健康检查和维护接口
- Docker 支持

## 技术栈

- Python 3.9
- FastAPI
- jieba 中文分词
- Docker

## 项目结构

```bash
review-nlp-service/
├── app.py              # 主应用入口
├── config.py           # 配置文件
├── models/
│   ├── sentiment_model.py    # 情感分析模型
│   └── content_filter.py     # 内容过滤模型
├── utils/
│   └── text_processor.py     # 文本处理工具
├── Dockerfile          # Docker 配置文件
└── requirements.txt    # 项目依赖
```

## 安装说明

### 使用 Docker

1.构建 Docker 镜像：

```bash
docker build -t review-nlp-service .
```

2.运行容器：

```bash
docker run -d -p 8000:8000 review-nlp-service
```

### 本地安装

1.克隆项目：

```bash
git clone https://github.com/hd2yao/review-nlp-service.git
cd review-nlp-service
```

2.安装依赖：

```bash
pip install -r requirements.txt
```

3.运行服务：

```bash
python app.py
```

或者直接使用 uvicorn：

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

4.访问服务：

服务启动后，可以通过浏览器访问 http://localhost:8000/docs 查看 API 文档界面

## 环境变量配置

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| SERVICE_HOST | 服务监听地址 | 0.0.0.0 |
| SERVICE_PORT | 服务端口 | 8000 |
| MODEL_PATH | 模型文件路径 | models |
| LOG_LEVEL | 日志级别 | INFO |

## API 接口

### 1. 单条评论分析

```bash
POST /analyze
```

请求体：

```json
{
    "review_id": 1,
    "content": "这个产品非常好用，我很喜欢！"
}
```

响应：

```json
{
    "review_id": 1,
    "sentiment": "positive",
    "sentiment_score": 0.9711370468139648,
    "is_appropriate": true,
    "inappropriate_reasons": []
}
```

### 2. 批量评论分析

```bash
POST /analyze/batch
```

请求体：

```json
{
    "reviews": [
        {
            "review_id": 1,
            "content": "这个产品非常好用，我很喜欢！"
        },
        {
            "review_id": 2,
            "content": "质量一般，不太满意。"
        },
        {
            "review_id": 3, 
            "content": "太糟糕了，完全是垃圾。"
        }
    ]
}
```

响应：

```json
{
    "results": [
        {
            "review_id": 1,
            "sentiment": "positive",
            "sentiment_score": 0.9711370468139648,
            "is_appropriate": true,
            "inappropriate_reasons": []
        },
        {
            "review_id": 2,
            "sentiment": "negative",
            "sentiment_score": 0.8718591928482056,
            "is_appropriate": true,
            "inappropriate_reasons": []
        },
        {
            "review_id": 3,
            "sentiment": "negative",
            "sentiment_score": 0.9845377206802368,
            "is_appropriate": true,
            "inappropriate_reasons": []
        }
    ],
    "total": 3,
    "inappropriate_count": 0
}
```

测试后的评论会存在 cache 中，可在下面的接口中体现

### 3. 健康检查

```bash
GET /health
```

响应：

```json
{
    "status": "healthy",
    "models": {
        "sentiment_analyzer": {
            "threshold": 0.75,
            "cache_size": 3
        },
        "content_filter": {
            "sensitive_words_count": 6,
            "patterns_count": 5,
            "cache_size": 3
        }
    }
}
```

### 4. 清除缓存

```bash
POST /maintenance/clear-cache
```

响应：

```json
{
    "status": "success",
    "message": "所有缓存已清除"
}
```

## 注意事项

1. 首次运行时，系统会自动下载预训练的情感分析模型（`uer/roberta-base-finetuned-jd-binary-chinese`），这可能需要一些时间
2. 需要在 `models` 目录下配置 `sensitive_words.json` 文件用于敏感词过滤
3. 情感分析模型的阈值可以在初始化时调整（默认为 0.75）
4. 批量处理接口最多支持同时处理 100 条评论

## 性能优化

1. 使用词语缓存机制提升分词和分析性能
2. 支持批量处理减少接口调用次数
3. 异步处理提升并发性能

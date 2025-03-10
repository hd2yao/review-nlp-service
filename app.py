from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from models.sentiment_model import SentimentAnalyzer
from models.content_filter import ContentFilter
from utils.text_processor import preprocess_text
import uvicorn
import logging
import os
from config import SERVICE_HOST, SERVICE_PORT, LOG_LEVEL, MODEL_PATH

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("review-nlp-service")

# 创建应用
app = FastAPI(
    title="Review NLP Service", 
    description="API for review text analysis and sentiment analysis",
    version="1.0.0"
)

# 初始化模型
# 使用配置文件中的设置初始化模型
sensitive_words_path = os.path.join(MODEL_PATH, "sensitive_words.json")
sentiment_analyzer = SentimentAnalyzer(threshold=0.75)  # 可以根据需要调整阈值
content_filter = ContentFilter(
    sensitive_words_file=sensitive_words_path if os.path.exists(sensitive_words_path) else None,
    log_level=getattr(logging, LOG_LEVEL)
)

class ReviewRequest(BaseModel):
    review_id: int
    content: str = Field(..., min_length=1, description="评论内容")

class BatchReviewRequest(BaseModel):
    reviews: List[ReviewRequest] = Field(..., min_items=1, max_items=100, description="评论列表")

class ReviewResponse(BaseModel):
    review_id: int
    sentiment: str  # "positive", "neutral", "negative"
    sentiment_score: float
    is_appropriate: bool
    inappropriate_reasons: List[str] = []

class BatchReviewResponse(BaseModel):
    results: List[ReviewResponse]
    total: int
    inappropriate_count: int

class HealthResponse(BaseModel):
    status: str
    models: dict

@app.post("/analyze", response_model=ReviewResponse)
async def analyze_review(review: ReviewRequest):
    """
    分析单条评论内容，返回情感分析结果和内容审核结果
    """
    logger.info(f"收到评论分析请求: ID={review.review_id}")
    
    try:
        # 情感分析
        sentiment, score = sentiment_analyzer.analyze(review.content)
        
        # 内容过滤
        is_appropriate, reasons = content_filter.check_content(review.content)
        
        response = {
            "review_id": review.review_id,
            "sentiment": sentiment,
            "sentiment_score": score,
            "is_appropriate": is_appropriate,
            "inappropriate_reasons": reasons
        }
        
        logger.info(f"评论 ID={review.review_id} 分析完成: sentiment={sentiment}, appropriate={is_appropriate}")
        return response
    except Exception as e:
        logger.error(f"处理评论时出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理评论时出错: {str(e)}")

@app.post("/analyze/batch", response_model=BatchReviewResponse)
async def analyze_reviews_batch(request: BatchReviewRequest):
    """
    批量分析多条评论内容，返回情感分析结果和内容审核结果
    """
    logger.info(f"收到批量评论分析请求: {len(request.reviews)} 条评论")
    
    try:
        results = []
        review_contents = [review.content for review in request.reviews]
        review_ids = [review.review_id for review in request.reviews]
        
        # 批量情感分析
        sentiment_results = sentiment_analyzer.analyze_batch(review_contents)
        
        # 批量内容过滤
        filter_results = content_filter.check_batch(review_contents)
        
        # 组合结果
        for i, (review_id, (sentiment, score), (is_appropriate, reasons)) in enumerate(
            zip(review_ids, sentiment_results, filter_results)
        ):
            results.append({
                "review_id": review_id,
                "sentiment": sentiment,
                "sentiment_score": score,
                "is_appropriate": is_appropriate,
                "inappropriate_reasons": reasons
            })
        
        # 统计不适当内容数量
        inappropriate_count = sum(1 for result in results if not result["is_appropriate"])
        
        response = {
            "results": results,
            "total": len(results),
            "inappropriate_count": inappropriate_count
        }
        
        logger.info(f"批量分析完成: 共 {len(results)} 条评论，{inappropriate_count} 条不适当")
        return response
    except Exception as e:
        logger.error(f"批量处理评论时出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量处理评论时出错: {str(e)}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查接口，返回服务状态和模型信息
    """
    return {
        "status": "healthy",
        "models": {
            "sentiment_analyzer": {
                "threshold": sentiment_analyzer.threshold,
                "cache_size": len(sentiment_analyzer.word_cache)
            },
            "content_filter": {
                "sensitive_words_count": len(content_filter.sensitive_words),
                "patterns_count": len(content_filter.patterns),
                "cache_size": len(content_filter.word_cache)
            }
        }
    }

@app.post("/maintenance/clear-cache")
async def clear_cache():
    """
    清除所有缓存
    """
    try:
        sentiment_analyzer.clear_cache()
        content_filter.clear_cache()
        logger.info("已清除所有缓存")
        return {"status": "success", "message": "所有缓存已清除"}
    except Exception as e:
        logger.error(f"清除缓存时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info(f"启动服务: host={SERVICE_HOST}, port={SERVICE_PORT}")
    uvicorn.run("app:app", host=SERVICE_HOST, port=SERVICE_PORT, reload=True)
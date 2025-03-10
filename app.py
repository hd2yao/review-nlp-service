from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from models.sentiment_model import SentimentAnalyzer
from models.content_filter import ContentFilter
import uvicorn

app = FastAPI(title="Review NLP Service", description="API for review text analysis and sentiment analysis")

# 初始化模型
sentiment_analyzer = SentimentAnalyzer()
content_filter = ContentFilter()

class ReviewRequest(BaseModel):
    review_id: int
    content: str

class ReviewResponse(BaseModel):
    review_id: int
    sentiment: str  # "positive", "neutral", "negative"
    sentiment_score: float
    is_appropriate: bool
    inappropriate_reasons: list = []

@app.post("/analyze", response_model=ReviewResponse)
async def analyze_review(review: ReviewRequest):
    """
    分析评论内容，返回情感分析结果和内容审核结果
    """
    try:
        # 情感分析
        sentiment, score = sentiment_analyzer.analyze(review.content)
        
        # 内容过滤
        is_appropriate, reasons = content_filter.check_content(review.content)
        
        return {
            "review_id": review.review_id,
            "sentiment": sentiment,
            "sentiment_score": score,
            "is_appropriate": is_appropriate,
            "inappropriate_reasons": reasons
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
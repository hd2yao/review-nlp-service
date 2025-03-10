from transformers import pipeline
import jieba
import numpy as np
from typing import Union, List, Tuple, Dict, Any
import logging

class SentimentAnalyzer:
    def __init__(self, threshold: float = 0.8, model_name: str = "uer/roberta-base-finetuned-jd-binary-chinese"):
        """
        初始化情感分析器
        
        Args:
            threshold: 情感判断的阈值,默认为0.8
            model_name: 使用的预训练模型名称
        """
        # 使用预训练的中文情感分析模型
        # 将这个管道保存为类的实例变量，以便在 analyze 方法中使用
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=model_name
        )
        self.threshold = threshold
        # 用于缓存已分词的文本
        # 使用字典来缓存已分词的文本，提高效率
        self.word_cache = {}  
        self.logger = logging.getLogger(__name__)
        
    def _preprocess_text(self, text: str) -> str:
        """
        对文本进行预处理，包括分词
        
        Args:
            text: 输入文本
            
        Returns:
            处理后的文本
        """
        if text in self.word_cache:
            return self.word_cache[text]
            
        words = jieba.cut(text)
        processed_text = " ".join(words)
        self.word_cache[text] = processed_text
        return processed_text
        
    def analyze(self, text: str) -> Tuple[str, float]:
        """
        分析单个文本的情感，返回情感标签和分数
        
        Args:
            text: 输入文本
            
        Returns:
            (情感标签, 置信度分数)
        """
        # 错误处理
        # 输入验证：确保输入是字符串，防止是空值或者非字符串
        if not text or not isinstance(text, str):
            self.logger.warning(f"无效输入: {text}")
            return "neutral", 0.0
            
        try:
            # 预处理文本
            processed_text = self._preprocess_text(text)
            
            # 使用模型进行情感分析
            result = self.sentiment_pipeline(processed_text)[0]
            
            # 添加日志输出模型的原始输出
            self.logger.info(f"模型原始输出: {result}")
            
            # 将模型输出映射到正面、中性、负面
            label = result["label"]
            score = result["score"]
            
            # 修改标签判断逻辑，匹配模型实际返回的标签格式
            if "positive" in label.lower() and score > self.threshold:
                return "positive", score
            elif "negative" in label.lower() and score > self.threshold:
                return "negative", score
            else:
                return "neutral", score
        except Exception as e:
            self.logger.error(f"分析文本时出错: {str(e)}")
            return "neutral", 0.0
            
    def analyze_batch(self, texts: List[str]) -> List[Tuple[str, float]]:
        """
        批量分析多个文本的情感
        
        Args:
            texts: 文本列表
            
        Returns:
            情感分析结果列表，每项为(情感标签, 置信度分数)
        """
        if not texts:
            return []
            
        # 过滤无效输入
        valid_texts = [t for t in texts if t and isinstance(t, str)]
        if not valid_texts:
            return [("neutral", 0.0)] * len(texts)
            
        try:
            # 预处理所有文本
            processed_texts = [self._preprocess_text(text) for text in valid_texts]
            
            # 批量分析
            results = self.sentiment_pipeline(processed_texts)
            
            # 添加日志输出
            for i, result in enumerate(results):
                self.logger.info(f"文本 {i+1} 模型原始输出: {result}")
            
            # 处理结果
            final_results = []
            for i, result in enumerate(results):
                label = result["label"]
                score = result["score"]
                
                # 修改标签判断逻辑，匹配模型实际返回的标签格式
                if "positive" in label.lower() and score > self.threshold:
                    final_results.append(("positive", score))
                elif "negative" in label.lower() and score > self.threshold:
                    final_results.append(("negative", score))
                else:
                    final_results.append(("neutral", score))
                    
            return final_results
        except Exception as e:
            self.logger.error(f"批量分析文本时出错: {str(e)}")
            return [("neutral", 0.0)] * len(valid_texts)
            
    def clear_cache(self):
        """
        清除分词缓存
        """
        self.word_cache.clear()
        
    def set_threshold(self, threshold: float):
        """
        设置情感判断阈值
        
        Args:
            threshold: 新的阈值值(0.0-1.0)
        """
        if 0.0 <= threshold <= 1.0:
            self.threshold = threshold
        else:
            self.logger.warning(f"无效的阈值: {threshold},阈值应在0.0到1.0之间")
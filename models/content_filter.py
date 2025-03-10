import re
import jieba
import json
import os

class ContentFilter:
    def __init__(self):
        # 加载敏感词库
        self.sensitive_words = self._load_sensitive_words()
        
        # 正则表达式模式
        self.patterns = {
            "personal_info": r'(1[3-9]\d{9}|身份证|\d{18}|\d{17}X)',  # 手机号、身份证号
            "url": r'https?://\S+|www\.\S+',  # URL
            "email": r'\S+@\S+\.\S+',  # 邮箱
        }
        
    def _load_sensitive_words(self):
        """
        加载敏感词库
        """
        # 这里可以从文件加载敏感词库，或者使用预定义的列表
        # 示例敏感词库
        return [
            "脏话", "骂人", "违禁品", "色情", "赌博", "诈骗",
            # 添加更多敏感词...
        ]
        
    def check_content(self, text):
        """
        检查文本是否包含不当内容
        返回：(是否适当, 不适当原因列表)
        """
        reasons = []
        
        # 检查敏感词
        words = jieba.cut(text)
        for word in words:
            if word in self.sensitive_words:
                reasons.append(f"包含敏感词: {word}")
        
        # 检查正则表达式模式
        for pattern_name, pattern in self.patterns.items():
            if re.search(pattern, text):
                reasons.append(f"包含{pattern_name}")
        
        # 检查文本长度
        if len(text) < 5:
            reasons.append("评论内容过短")
        
        return len(reasons) == 0, reasons
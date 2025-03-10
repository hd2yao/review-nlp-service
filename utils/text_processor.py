import re
import jieba

def preprocess_text(text):
    """
    文本预处理：去除特殊字符、分词等
    """
    # 去除HTML标签
    text = re.sub(r'<.*?>', '', text)
    
    # 去除URL
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # 去除多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 中文分词
    words = jieba.cut(text)
    
    return " ".join(words)
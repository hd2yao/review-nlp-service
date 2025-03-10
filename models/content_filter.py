import re
import jieba
import json
import os
import logging
from typing import List, Tuple, Dict, Set, Optional, Union

class ContentFilter:
    def __init__(self, sensitive_words_file: str = None, log_level: int = logging.INFO):
        """
        初始化内容过滤器
        
        Args:
            sensitive_words_file: 敏感词库文件路径,支持JSON格式
            log_level: 日志级别
        """
        # 设置日志
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # 加载敏感词库
        self.sensitive_words_file = sensitive_words_file
        self.sensitive_words = self._load_sensitive_words()
        self.logger.info(f"已加载 {len(self.sensitive_words)} 个敏感词")
        
        # 分词缓存
        self.word_cache = {}
        
        # 正则表达式模式 - 更精细的匹配
        self.patterns = {
            "手机号": r'(?<!\d)1[3-9]\d{9}(?!\d)',  # 手机号，确保前后不是数字
            "身份证": r'(?<!\d)(\d{17}[\dXx]|\d{15})(?!\d)',  # 身份证号
            "URL": r'(https?://[^\s<>"\']+|www\.[^\s<>"\']+\.[^\s<>"\']+)',  # 更精确的URL匹配
            "邮箱": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # 更精确的邮箱匹配
            "银行卡": r'(?<!\d)(62\d{14,17}|4\d{15}|5[1-5]\d{14}|3[47]\d{13})(?!\d)',  # 常见银行卡格式
        }
        
    def _load_sensitive_words(self) -> Set[str]:
        """
        从文件加载敏感词库，如果文件不存在则使用默认敏感词库
        
        Returns:
            敏感词集合
        """
        default_words = {
            "脏话", "骂人", "违禁品", "色情", "赌博", "诈骗",
            # 添加更多默认敏感词...
        }
        
        if not self.sensitive_words_file:
            self.logger.warning("未指定敏感词库文件，使用默认敏感词库")
            return default_words
            
        try:
            if not os.path.exists(self.sensitive_words_file):
                self.logger.warning(f"敏感词库文件 {self.sensitive_words_file} 不存在，使用默认敏感词库")
                return default_words
                
            with open(self.sensitive_words_file, 'r', encoding='utf-8') as f:
                if self.sensitive_words_file.endswith('.json'):
                    words_data = json.load(f)
                    # 支持多种JSON格式：列表或字典
                    if isinstance(words_data, list):
                        return set(words_data)
                    elif isinstance(words_data, dict) and 'words' in words_data:
                        return set(words_data['words'])
                    else:
                        self.logger.error("JSON格式不支持,使用默认敏感词库")
                        return default_words
                else:
                    # 假设是文本文件，每行一个敏感词
                    return {line.strip() for line in f if line.strip()}
        except Exception as e:
            self.logger.error(f"加载敏感词库出错: {str(e)}，使用默认敏感词库")
            return default_words
            
    def _preprocess_text(self, text: str) -> List[str]:
        """
        对文本进行预处理，包括分词
        
        Args:
            text: 输入文本
            
        Returns:
            分词结果列表
        """
        if text in self.word_cache:
            return self.word_cache[text]
            
        words = list(jieba.cut(text))
        self.word_cache[text] = words
        return words
        
    def check_content(self, text: str) -> Tuple[bool, List[str]]:
        """
        检查单个文本是否包含不当内容
        
        Args:
            text: 输入文本
            
        Returns:
            (是否适当, 不适当原因列表)
        """
        if not text or not isinstance(text, str):
            self.logger.warning(f"无效输入: {text}")
            return False, ["输入无效"]
            
        try:
            reasons = []
            
            # 检查敏感词
            words = self._preprocess_text(text)
            for word in words:
                if word in self.sensitive_words:
                    reason = f"包含敏感词: {word}"
                    reasons.append(reason)
                    self.logger.info(f"文本 '{text[:20]}...' {reason}")
            
            # 检查正则表达式模式
            for pattern_name, pattern in self.patterns.items():
                matches = re.findall(pattern, text)
                if matches:
                    # 记录具体匹配到的内容
                    for match in matches:
                        match_text = match if isinstance(match, str) else match[0]
                        reason = f"包含{pattern_name}: {match_text}"
                        reasons.append(reason)
                        self.logger.info(f"文本 '{text[:20]}...' {reason}")
            
            # 检查文本长度
            if len(text) < 5:
                reason = "内容过短"
                reasons.append(reason)
                self.logger.info(f"文本 '{text}' {reason}")
            
            is_appropriate = len(reasons) == 0
            return is_appropriate, reasons
            
        except Exception as e:
            self.logger.error(f"检查内容时出错: {str(e)}")
            return False, [f"检查过程出错: {str(e)}"]
            
    def check_batch(self, texts: List[str]) -> List[Tuple[bool, List[str]]]:
        """
        批量检查多个文本是否包含不当内容
        
        Args:
            texts: 文本列表
            
        Returns:
            检查结果列表，每项为(是否适当, 不适当原因列表)
        """
        if not texts:
            return []
            
        results = []
        for text in texts:
            result = self.check_content(text)
            results.append(result)
            
        # 记录统计信息
        inappropriate_count = sum(1 for is_appropriate, _ in results if not is_appropriate)
        self.logger.info(f"批量检查完成: 共 {len(texts)} 条文本，{inappropriate_count} 条不适当")
        
        return results
        
    def add_sensitive_words(self, words: List[str]) -> None:
        """
        添加新的敏感词
        
        Args:
            words: 要添加的敏感词列表
        """
        original_count = len(self.sensitive_words)
        self.sensitive_words.update(words)
        new_count = len(self.sensitive_words)
        self.logger.info(f"添加了 {new_count - original_count} 个新敏感词")
        
    def remove_sensitive_words(self, words: List[str]) -> None:
        """
        移除敏感词
        
        Args:
            words: 要移除的敏感词列表
        """
        original_count = len(self.sensitive_words)
        self.sensitive_words.difference_update(words)
        new_count = len(self.sensitive_words)
        self.logger.info(f"移除了 {original_count - new_count} 个敏感词")
        
    def save_sensitive_words(self, file_path: str) -> bool:
        """
        将当前敏感词库保存到文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否保存成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    json.dump(list(self.sensitive_words), f, ensure_ascii=False, indent=2)
                else:
                    f.write('\n'.join(self.sensitive_words))
            self.logger.info(f"敏感词库已保存到 {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存敏感词库失败: {str(e)}")
            return False
            
    def clear_cache(self) -> None:
        """
        清除分词缓存
        """
        cache_size = len(self.word_cache)
        self.word_cache.clear()
        self.logger.info(f"已清除 {cache_size} 条分词缓存")
        
    def add_pattern(self, name: str, pattern: str) -> None:
        """
        添加新的正则表达式模式
        
        Args:
            name: 模式名称
            pattern: 正则表达式模式
        """
        try:
            # 测试正则表达式是否有效
            re.compile(pattern)
            self.patterns[name] = pattern
            self.logger.info(f"添加了新的正则模式: {name}")
        except re.error as e:
            self.logger.error(f"添加正则模式失败，无效的正则表达式: {str(e)}")
            
    def remove_pattern(self, name: str) -> bool:
        """
        移除正则表达式模式
        
        Args:
            name: 模式名称
            
        Returns:
            是否移除成功
        """
        if name in self.patterns:
            del self.patterns[name]
            self.logger.info(f"移除了正则模式: {name}")
            return True
        else:
            self.logger.warning(f"正则模式不存在: {name}")
            return False
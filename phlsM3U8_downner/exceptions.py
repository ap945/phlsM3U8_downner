"""报错类型"""
class HLSFailed(Exception):
     """
    本库所有异常的基类。

    设计意图：调用方可以写 `except HLSDownloaderError` 一网打尽，
    也可以精确捕获某个子类做针对性处理。
    """

class FailedParseM3u8Error(HLSFailed):
    """解析m3u8失败"""
    def __init__(self, url : str ='', reason : str =''):
        self.url=url
        self.reason=reason
        super().__init__(f"M3U8 Error Parser {self.url} Failed Reason: {self.reason}")

class FailedSegmentError(HLSFailed):   #A segment download failed
    """多次尝试下载失败"""
    def __init__( self, reason : str =''):
        self.reason=reason
        super().__init__(f"Error down  Failed Reason: {self.reason}")

class KEYisNoneError(HLSFailed):
    """KEY为None"""
    def __init__(self, url : str ='', reason : str =''):
        self.url=url
        self.reason=reason
        super().__init__(f"Key is None{self.url} Failed Reason: {self.reason}")

class GetMethodError(HLSFailed):
    """Wrong Method for getting data"""
    def __init__(self, method : str ='', reason : str =''):
        self.method=method
        self.reason=reason
        super().__init__(f"Key is None{self.method} Failed Reason: {self.reason}")

class Down_BadError(HLSFailed):
    """Down Bad from Down or Decode(downing key)"""
    def __init__(self, url : str =''):
            self.url=url
            super().__init__(f"Error down {self.url} Failed Reason: Bad_down")

class FailedDecodeSegmentError(HLSFailed):   #A segment Decode failed
    """下载成功但解密失败"""
    def __init__(self, key_url : str ='', reason : str =''):
        self.url=key_url
        self.reason=reason
        super().__init__(f"Error Download Succeeded But Decoding Failed {self.url} Failed Reason: {self.reason}")

class FailedConverterError(HLSFailed):   
    """合并失败,原因来自于ffpeg"""
    def __init__(self, out_path : str ='', reason : str =''):    
        self.out_path=out_path
        self.reason=reason
        super().__init__(f"Error Converter {self.out_path} Failed Reason: {self.reason[:200]} from ffmpeg")

class FailedMethodError(HLSFailed):   
    """解密失败,解密类型当前不支持"""
    def __init__(self, method : str ='', reason : str =''):    
        self.method=method
        self.reason=reason
        super().__init__(f"Error Decryption type not supported {self.method} Failed Reason: {self.reason} ")

class FailedNoMethodError(HLSFailed):   
    """没找到解密方式"""
    def __init__(self):    
        super().__init__(f"Error Decryption No Method ")
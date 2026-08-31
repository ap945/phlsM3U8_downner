from enum import Enum
from dataclasses import dataclass,field
from typing import Optional
from pathlib import Path

class EncryptMethod(str, Enum):
    "Encrypt Mthod加密方式"
    NONE = 'NONE'
    AES_128='AES-128'

@dataclass
class key:
    method:Optional[EncryptMethod]=EncryptMethod.NONE
    key_uri : Optional[str] = None
    iv : Optional[bytes]= None
@dataclass
class Segment:
    """单个切片的信息"""
    key : Optional[key]
    uri : Optional[str]
    Duration : Optional[float]#时长
    num : Optional[int]
    map_uri : Optional[str] #如果不为None说明是map的下一个切片

@dataclass(frozen=True)
class KeyErrorInfo:
    """一个解密失败的切片(下载成功了但解密失败,对应Bad_ts)"""
    segment: Segment            # 哪个切片
    reason: str                 # 解密失败的原因（如 "填充错误，密钥不对"）
    exception :Optional[Exception]=None

@dataclass(frozen=True)
class FailedM3U8Data:
    """一个解析失败的m3u8文件(下载成功了但解密失败,对应Bad_response)"""
    m3u8_uri: str             # 哪个切片
    reason: str                 # 解密失败的原因（如 "填充错误，密钥不对"）

@dataclass(frozen=True)
class FailedSegment:
    """
    一个下载失败的切片(含失败原因和重试次数)

    对照你原来的 Bad_Requests = {ts_url: [key_dict, "path_str"]}:
      - 你用列表存两个不同含义的东西，调用方必须读源码才知道 [0] 是什么
      - 这里每个信息都有名字，且带类型
    """
    segment: Segment            # 哪个切片失败了（Segment 对象，能拿到 uri、时长等全部信息）
    reason: str                 # 人话版原因："timeout" / "HTTP 404" / "连接被重置"
    attempts: int               # 试了几次都失败了
    exception: Optional[Exception] = None  # 原始异常对象，调用方想深挖时用

@dataclass(frozen=True)
class FailedKey:
    """
    一个下载失败的key(含失败原因和重试次数)。

    对照你原来的 Bad_Requests = {ts_url: [key_dict, "path_str"]}:
      - 你用列表存两个不同含义的东西，调用方必须读源码才知道 [0] 是什么
      - 这里每个信息都有名字，且带类型
    """
    segment: Segment            # 哪个切片失败了（Segment 对象，能拿到 uri、时长等全部信息）
    reason: str                 # 人话版原因："timeout" / "HTTP 404" / "连接被重置"
    attempts: int               # 试了几次都失败了
    exception: Optional[Exception] = None  # 原始异常对象，调用方想深挖时用


@dataclass
class StreamM3U8Data:
    """存储流的m3u8信息"""
    INF : Optional[dict]    #这里有他的信息
    uri : Optional[str]     #这里是他的uri
@dataclass
class MapSegment:
    """为_Download_Manage的Map切片准备的,其他地方不能用"""
    after_uri: Segment
    num : int
@dataclass
class DownloadResult:
    """
    下载结束后返回给调用方的"完整报告单"。

    赋值过程（回答你之前的问题——它不是被外部赋值的，是内部构建的）：
      1. download() 一开始创建空的收集器(succeeded=0, failed=[] ...)
      2. 解析 m3u8 后得到 total
      3. 下载循环里逐个累计 succeeded / 往 failed 里 append
      4. 合并成功后得到 output_path,stat() 拿文件大小
      5. 最后 return DownloadResult(...) —— 这一步才是"诞生"
    """
    output_path: Optional[str|Path]         # 合并后的视频路径；有失败没合并时为 None
    segments_total: int                 # 总切片数
    segments_succeeded: int             # 成功数
    failed_segments: list[FailedSegment]    # 下载失败清单（对应你的 Bad_Requests）
    key_errors: list[KeyErrorInfo]          # 解密失败清单（对应你的 Bad_ts）
    duration_seconds: float             # 整个下载（含合并）花了多少秒
    file_size_bytes: int                # 输出文件大小（没合并则 0）
    list_path : Optional[str|Path]=None

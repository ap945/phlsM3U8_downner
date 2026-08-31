from dataclasses import dataclass
from pathlib import Path
@dataclass
class config:
    """Global download settings
    ————————————————                    ————————————————————————————
    concurrency: int = 20               # Number of segments to download simultaneously
    limit: int = 20                     # Maximum number of requests
    timeout: float = 30.0               # Per-segment timeout in seconds
    retries: int = 3                    # Retry attempts per segment on failure
    retry_backoff: float = 1.5          # Retry interval multiplier: 1s → 1.5s → 2.25s (exponential backoff)
    stop_after_delay: float | int = 15  # Maximum total time allowed for the entire retry process
    verify_ssl: bool = False            # Whether to verify SSL (download sites often have certificate issues, disabled by default)
    keep_segments: bool = False         # Whether to keep .ts files after a successful merge (False = clean up)
    breakpoint_request: bool = False    # Load and re-download previously unfinished files (True = re-download)
    quiet: bool = False                 # Quiet mode
    method: str = 'get'                 # HTTP method for requests
    key_method: str = 'get'             # HTTP method for key requests
    data_path: str | Path = str(Path.cwd() / 'hls_downloads')  # Location of user_data  (Store ts/m4s/mp4 media files and data.json)
    Wait_Merge: bool = False            # Wait for all downloads to succeed before merging (False = don't wait)
    Rich: bool = True                   # Show progress bar (enabled by default)
    ————————————————                    ————————————————————————————"""

    concurrency: int = 20               # 同时下载几个切片
    limit : int = 20                    #最大请求数量
    timeout: float = 30.0               # 单个切片的超时秒数
    retries: int = 3                    # 单个切片失败重试次数
    retry_backoff: float = 1.5          # 重试间隔倍数：1s → 1.5s → 2.25s（指数退避）
    stop_after_delay : float | int =15  #设置整个重试过程的最大耗时
    verify_ssl: bool = False            # 是否校验 SSL（下载站证书经常有问题，默认关）
    keep_segments: bool = False         # 合并成功后是否保留 ts 文件（False=清理）
    breakpoint_request : bool =False    #加载上次下载未完成的文件重下(True为重下)
    quiet : bool=False                  #安静模式
    method : str = 'get'                #请求方式
    key_method : str = 'get'           #请求方式
    data_path : str|Path = str(Path.cwd() /'hls_downloads') #user_data的位置
    Wait_Merge : bool =True          #等下载全部成功再合并(false是不等)
    Rich : bool =True                   #显示进度条默认是

##PYPI:https://pypi.org/project/phlsM3U8-downner/

# phlsM3U8_downner

Async HLS/m3u8 downloader with AES-128 decryption and ffmpeg merging.
支持主播放列表选择清晰度、切片并发下载、AES-128 解密、ffmpeg 无损合并.

## Install

    pip install phlsM3U8_downner

Requires **ffmpeg** on system PATH:
Windows `winget install ffmpeg` · macOS `brew install ffmpeg` · Linux `sudo apt install ffmpeg`

## Usage

##import phlsM3U8_downner #import 
#Or
# from phlsM3U8_downner import * #import all functions
#Now I use 'import phlsM3U8_downner' #import  
url1='http://127.0.0.1/hls/e/m.m3u8'
url1_name = '1.mp4'

dic={url1:url1_name}

headers={'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36 Edg/152.0.0.0'}
result = phlsM3U8_downner.DownAndMerge(UrlAndName=dic,headers=headers)
#you can see down a video success
<video src="./docs/demo.mp4" controls width="600"></video>
#This is a very simple example

## More Usage
    - Config:
        in config_set 它含有很多配置项,见下:
    ————————————————                    ————————————————————————————
    concurrency: int = 20               # 同时下载几个切片
    limit : int = 20                    #最大请求数量
    timeout: float = 30.0               # 单个切片的超时秒数
    retries: int = 3                    # 单个切片失败重试次数
    retry_backoff: float = 1.5          # 重试间隔倍数:1s → 1.5s → 2.25s(指数退避）
    stop_after_delay : float | int =15  #设置整个重试过程的最大耗时
    verify_ssl: bool = False            # 是否校验 SSL(下载站证书经常有问题,默认关)
    keep_segments: bool = False         # 合并成功后是否保留 ts 文件(False=清理）
    breakpoint_request : bool =False    #加载上次下载未完成的文件重下(True为重下)
    quiet : bool=False                  #安静模式
    method : str = 'get'                #请求方式
    key_method : str = 'get'           #请求方式
    data_path : str|Path = str(Path.cwd() /'hls_downloads') #user_data的位置(存放ts/m4s/mp4媒体文件和data.json)
    Wait_Merge : bool =True          #等下载全部成功再合并(false是不等)
    Rich : bool =True                   #显示进度条(默认是)
    ——————————————————                      ————————————————————————
    -config_set注意事项:
        -如果你想使用breakpoint_request,这需要data,json中失败的片段(failed_segments/key_errors)不为[],否则什么都不会发生
        -等你下载了一个文件后会自动刷新,需要注意的是,**phlsM3U8_downner会覆盖原有内容**
        -quiet 这个设置如果为True,那么将会少很多打印,甚至连进度条都不会输出
        -key_method method,method是为普通切片(segment)文件请求的模式,而key_method是专门为key请求的模式,在某一些场景中他很有用,你可以使他们全部为**'get'**
        -Wait_Merge 如果你设置了True,那么他不会去管data.json中失败的片段反而会去将成功的片段合并,这可能会使合并后的视频缺斤少两

    - resolver:
        -defined_decode中 **defined_method**是自定义加密模式但是可能phlsM3U8_downner不支持(目前只支持AES-128加密,但是这够了)

        -你可以使用**defined_func**参数来存放你的函数**{key_url:函数名称}**,phlsM3U8_downner会用你的函数来解密

        -如果获取的key有加密,你可以使用encrypto_key**{key_url:函数名称}**来解密你的key

        -如果phlsM3U8_downner获取不到key,例如DRM中,你可以使用**defined_key**来放你获取到的key(bytes),如果你放了**defined_key**,那请你务必需将**defined_iv**也补充上去**{key_url:函数名称}**,虽然phlsM3U8_downner内置了采用序列号的方式来替换iv但是这是一个保险

        (resolver.defined_method Method resolver.defined_func func resolver.encrypto_key encrypto_key resolver.defined_iv iv resolver.defined_key key)
## Notes
- 不要同时对多个下载使用同一个输出文件名（后者会覆盖前者）
- 多个主播放列表同时下载时需手动选清晰度，建议逐个下载
- 配置项见 `config_set.config`（IDE 悬浮即可查看全部字段）

## 0.1.2 None

## 0.1.1 Chinese logging -> English logging

## 0.1.0 first release

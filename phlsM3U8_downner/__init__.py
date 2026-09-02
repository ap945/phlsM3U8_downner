"""Async HLS/m3u8 downloader with AES-128 decryption and ffmpeg merging."""
import asyncio,shutil
from typing import Any
from . import main,exceptions,models,config,parser,resolver,_Converter
from .config import config as Config
from .models import(
    Segment,
    key,
    DownloadResult,
    EncryptMethod,
    StreamM3U8Data,
    FailedKey,
    FailedM3U8Data,
    FailedSegment,
    KeyErrorInfo,
    
)

from .exceptions import(
    HLSFailed,
    Down_BadError,
    FailedConverterError,
    FailedDecodeSegmentError,
    GetMethodError,
    KEYisNoneError,
    FailedMethodError,
    FailedParseM3u8Error,
    FailedSegmentError,
    FailedNoMethodError,
    
    
)
from .resolver import(
    defined_decode
)
__all__=[
    'DownAndMergeAsync',
    'DownAndMerge',
    'Config',
    'Segment',
    'key',
    'DownloadResult',
    'EncryptMethod',
    'StreamM3U8Data','HLSFailed',
    'Down_BadError',
    'FailedConverterError',
    'FailedDecodeSegmentError',
    'GetMethodError',
    'KEYisNoneError',
    'FailedMethodError',
    'FailedParseM3u8Error',
    'FailedSegmentError',
    'FailedNoMethodError',
    'FailedKey',
    'FailedM3U8Data',
    'FailedSegment',
    'KeyErrorInfo',
    'defined_decode'
]
__version__ = "0.1.0"



def DownAndMerge(UrlAndName : dict, headers : dict=None ,config : Config|None=None,
                            request_method : str='get',lph : int =25,defined_key : defined_decode=None,
                            request_data : Any=None,request_json :Any=None
                            ,keep_segments :bool =False):
    """This is a synchronous function, intended to be called outside async functions,
                do not call this inside async code — use DownAndMergeAsync instead
                UrlAndName takes a {URL: FILE_NAME} dictionary — multiple entries allowed. Required!
                headers is the request headers; if not passed, defaults to None (no headers).
                config is the configuration for the entire DownAndName function. There are many
                important settings; if omitted, default values will be used. See the config_set
                module for details.
                lph is the maximum number of concurrent requests.
                defined_key is for customizing the key / iv / segment-decryption function /
                key-decryption functions (e.g. base64-style decoders — you can also define
                your own). Pass the function name. See the defined_decode module for details.
                request_data and request_json are the form parameters sent with POST requests.
                keep_segments (typo in original: keep_segmrnts) chooses whether to delete the
                downloaded ts/m4s/mp4 media files after merging. Default False, i.e. delete them.
                After execution this function returns a dictionary holding the results, keyed by
                the file name you chose, with an object as the value that you can query via
                its attributes.
                For example:
                        url='http://127.0.0.1/hls/ma.m3u8'
                        dic={url:'1.mp4'}
                        result=DownAndMerge(UrlAndName=dic)
                        result[your_file_name].output_path          # Output path
                        result[your_file_name].segments_total       # Total number of segments
                        result[your_file_name].segments_succeeded   # Number of segments downloaded successfully
                        result[your_file_name].failed_segments      # List of failed segments
                        result[your_file_name].key_errors           # List of decryption failures
                        result[your_file_name].duration_seconds     # Time elapsed
                        result[your_file_name].file_size_bytes      # Size in bytes after merging
                        result[your_file_name].list_path            # Path to the merged list.txt (intended for ffmpeg;
                                                    # avoid modifying it unless necessary)
                        __________Like this, you can retrieve its info
            If you get an error like:
                https:/xxxxx...
                XXX.XXX.XX:number ssl:default [getaddrinfo failed]
                the URL may have expired — try a different URL.
                If you see that all fields of a Segment object are 0, None, or other non-existent/placeholder values, it means the file crashed during download.
                Finally: NEVER, ever use the same file name for two or more downloads at once!!!
                Multiple master playlists must be downloaded one by one.
                Otherwise the merged file will be overwritten by the next download with the
                same name.
                """
    def _ensure_ffmpeg():
        if shutil.which('ffmpeg') is None:
            raise HLSFailed(
                "ffmpeg executable not found on PATH.\n"
                "Install it first:\n"
                "  Windows : winget install ffmpeg\n"
                "  macOS   : brew install ffmpeg\n"
                "  Linux   : sudo apt install ffmpeg"
            )
    
    if config is None:
        config = Config()
    _ensure_ffmpeg()
    return asyncio.run(main.main(url_dic=UrlAndName, headers=headers, method=request_method,
                           sem=lph, config=config, defined_key=defined_key,
                           request_data=request_data, request_json=request_json, keep_segments=keep_segments))


async def DownAndMergeAsync(UrlAndName : dict, headers : dict=None ,config : Config|None=None,
                            request_method : str='get',lph : int =25,defined_key : defined_decode=None,
                            request_data : dict|Any=None,request_json :dict|Any=None
                            ,keep_segments :bool =False):
    """This is an asynchronous function, intended to be called inside async functions.
            UrlAndName takes a {URL: FILE_NAME} dictionary — multiple entries allowed. Required!
            headers is the request headers; if not passed, defaults to None (no headers).
            config is the configuration for the entire DownAndName function. There are many
            important settings; if omitted, default values will be used. See the config_set
            module for details.
            lph is the maximum number of concurrent requests.
            defined_key is for customizing the key / iv / segment-decryption function /
            key-decryption function (e.g. base64-style decoders — you can also define your
            own). Pass the function name. See the defined_decode module for details.
            request_data and request_json are the form parameters sent with POST requests.
            keep_segments (typo in original: keep_segmrnts) chooses whether to delete the
            downloaded ts/m4s/mp4 media files after merging. Default False, i.e. delete them.
            After execution this function returns a dictionary holding the results, keyed by
            the file name you chose, with an object as the value that you can query via
            its attributes.
            For example:
                    url='http://127.0.0.1/hls/ma.m3u8'
                    dic={url:'1.mp4'}
                    result=await DownAndMergeAsync(UrlAndName=dic)
                    result[your_file_name].output_path          # Output contens
                    result[your_file_name].segments_total       # Total number of segments
                    result[your_file_name].segments_succeeded   # Number of segments downloaded successfully
                    result[your_file_name].failed_segments      # List of failed segments
                    result[your_file_name].key_errors           # List of decryption failures
                    result[your_file_name].duration_seconds     # Time elapsed
                    result[your_file_name].file_size_bytes      # Size in bytes after merging
                    result[your_file_name].list_path            # Path to the merged list.txt (for ffmpeg's use;
                                                # avoid modifying it unless necessary)
                    __________Like this, you can retrieve its info
            
    
            If you get an error like:
            https:/xxxxx...
            XXX.XXX.XX:number ssl:default [getaddrinfo failed]
            the URL may have expired — try a different URL.
            If you see that all fields of a Segment object are 0, None, or other non-existent/placeholder values, it means the file crashed during download.
            Finally: NEVER, ever use the same file name for two or more downloads at once!!!
            Multiple master playlists must be downloaded one by one.
            Otherwise the merged file will be overwritten by the next download with the
            same name.
            """
    def _ensure_ffmpeg():
            if shutil.which('ffmpeg') is None:
                raise HLSFailed(
                    "ffmpeg executable not found on PATH.\n"
                    "Install it first:\n"
                    "  Windows : winget install ffmpeg\n"
                    "  macOS   : brew install ffmpeg\n"
                    "  Linux   : sudo apt install ffmpeg"
                )
        
    if config is None:
        config = Config()
    _ensure_ffmpeg()
    return await main.main(url_dic=UrlAndName, headers=headers, method=request_method,
                           sem=lph, config=config, defined_key=defined_key,
                           request_data=request_data, request_json=request_json, keep_segments=keep_segments)

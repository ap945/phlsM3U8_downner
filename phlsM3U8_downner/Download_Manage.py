from pathlib import Path
from typing import Optional,Any
from urllib.parse import urljoin
from Cryptodome.Cipher import AES
from rich.progress import Progress
from dataclasses import dataclass, field
from Cryptodome.Util.Padding import unpad
import asyncio, aiohttp, aiofiles , time, logging
from tenacity import retry, stop_after_attempt, stop_after_delay,wait_exponential, retry_if_exception_type, AsyncRetrying
from . import config as config, resolver, exceptions,models



"""这个是用来控制经过"main.py"处理后的url进行下载, 合并管理的(主要是控制多线程数量和请求数量, 控制一下子下载多少个m3u8文件)"""
@dataclass
class downloader:
    _request : aiohttp.client.ClientSession 
    outname : str 
    segment_lists : list =field(default_factory=list)
    config : Optional[config.config] =None
    defined_key : Optional[resolver.defined_decode] = None
    headers : dict =None
    json : Any =None
    data : Any =None
    task : int =None
    progress : Progress =field(default_factory=Progress)
    def __post_init__(self):
        if self.defined_key is None:
             self.defined_key=resolver.defined_decode()
        if self.config is None:
             self.config=config.config()
        self.logger=logging.getLogger(__name__)
        self._segment_list=[]
        self.start_time=time.time()
        self.lock=asyncio.Lock()
        self.semaphore = asyncio.Semaphore(self.config.concurrency)
        self.ts_list=[]
        self.path = Path(self.config.data_path)
        self.key_session=getattr(self._request,self.config.key_method.lower()) 
        self.Session=getattr(self._request,self.config.method.lower())
        self.key_dic={}
        self.map_list=[]
        self.FailedSegments=[]
        self.FailedKey=[]#key下载失败
        self.Bad_key=[]#解密失败
        self.attempts=self.config.retries
        self.retryer = AsyncRetrying(
            stop=(stop_after_attempt(self.attempts) | stop_after_delay(self.config.stop_after_delay)),
            wait=wait_exponential(multiplier=1, exp_base=self.config.retry_backoff, min=1, max=10),
            retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
            reraise=True,               # 抛原始异常
            before_sleep=self._on_retry, # 重试前的钩子
        )
    def _on_retry(self, retry_state):
        if self.config.quiet:
            return
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        url = retry_state.args[0] if retry_state.args else '?'
        if self.config.Detailed_Infomaition:
            self.logger.error(f"⚠ {str(url)[:80]} NO. {retry_state.attempt_number} failure,Ready to try again: {exc!r}")
        else:
            self.logger.error(f"⚠ {str(url)[:80]} NO. {retry_state.attempt_number} failure,Ready to try again: {exc}")
    

    
    async def _down(self, url : str, headers : dict =None)->tuple:    #下载内容
            if self.config.method.lower()=='get':
                async with self.Session(url, headers=headers) as response:
                    response.raise_for_status()
                    data = await response.read()
                    return data, True
            elif self.config.method.lower()=='post':
                async with self.Session(url, headers=headers, data=self.data, json=self.json) as response:
                        response.raise_for_status()
                        data = await response.read()
                        return data,True
            else: raise exceptions.GetMethodError(method=self.config.method.lower(),reason='Wrong Method for getting data')

    async def key_down(self, url : str, headers : dict =None):    #下载内容
        if self.config.key_method.lower()=='get':
            async with self.key_session(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.read()
                return data
        elif self.config.key_method.lower()=='post':
            async with self.key_session(url, headers=headers, data=self.data, json=self.json) as response:
                    response.raise_for_status()
                    data = await response.read()
                    return data
        else: raise exceptions.GetMethodError(method=self.config.method.lower(),reason='Wrong Method for getting data')

    async def _down_with_retry(self, url : str,  headers : dict =None)->tuple:
            data, b=await self.retryer(self._down,url,headers)
            return data ,b

    async def _key_down_with_retry(self, url : str, segment : Optional[models.Segment], headers : dict =None):
            try:
                return await self.retryer(self.key_down,url,headers)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                FailedKey=models.FailedKey(
                    segment=segment, reason='Down Failed',
                    attempts=self.attempts, exception=e)
                
                self.FailedKey.append(FailedKey)
                return None
        
    async def Writefile(self, data : Any  ,file_path : str | Path):
        async with aiofiles.open(file_path ,'w+b') as f:
            await f.write(data)

    async def async_Writefile(self, file_path : str | Path, response : aiohttp.client_reqrep.ClientResponse):
        async with aiofiles.open(file_path ,'w+b') as f:
            async for chunk in response.content.iter_chunked(1024):
                await f.write(chunk)

    async def give_DECODE(self, data : bytes, segment : Optional[models.Segment])->bytes:
        ok_data =None
        if segment.key and segment.key.key_uri:
            key_uri=segment.key.key_uri
        else:
            raise exceptions.KEYisNoneError(reason='No Have Key URI')    #解密
        if self.defined_key.defined_func:
                if self.defined_key.defined_func.get(key_uri,None):
                    ok= self.defined_key.defined_func[key_uri](data, self.defined_key.defined_key.get(key_uri), self.defined_key.defined_iv.get(key_uri))
                    if asyncio.iscoroutine(ok):
                        ok = await ok
                    ok_data = ok
        elif self.defined_key.defined_key.get(key_uri,None):    #提前设置好的key
            ok_data = await self.DECODE(data=data, key=self.defined_key.defined_key.get(key_uri), iv=self.defined_key.defined_iv.get(key_uri,None), method=self.defined_key.defined_method, seq=segment.num,key_uri=key_uri)
        else: 
            ok_data = await self.DECODE(data, self.key_dic.get(key_uri), segment.key.iv, segment.key.method, segment.num,key_uri=key_uri)
        return ok_data
    
    async def DECODE(self, data, key, iv, method, seq : int,key_uri:str)->bytes:
        if key is None:
            raise exceptions.KEYisNoneError( reason='Key Not Cached')
        if iv is None and seq is None:
            raise exceptions.FailedDecodeSegmentError('see FailedSegment', reason='IV Missing')
        if method :
                if method==models.EncryptMethod.AES_128:
                    if iv is None and seq is not None:
                         iv=seq.to_bytes(16, byteorder='big')
                    if len(key)==16 and len(iv)==16:
                        cipher = AES.new(key, AES.MODE_CBC,iv)
                        try:
                            return unpad(cipher.decrypt(data), 16)
                        except ValueError as e:raise exceptions.FailedDecodeSegmentError(key_uri, reason=f'bad padding: {e}') from e
                    else:raise ValueError('Key Or iv len no 16 bytes')
                else:
                     raise exceptions.FailedDecodeSegmentError('see FailedSegment',reason='Decoding Failed')
        else:
            raise exceptions.FailedNoMethodError()

    async def Add_KEY(self, segment : Optional[models.Segment])->bool:
        async with self.lock:
            if segment.key and segment.key.key_uri:
                key_uri=segment.key.key_uri
                if key_uri not in self.key_dic and not self.defined_key.defined_key.get(key_uri,None):
                    key_data=await self._key_down_with_retry(url=key_uri.strip('\"\''), segment=segment, headers=self.headers)
                    if key_data is not None and len(key_data) == 16:
                        self.key_dic[key_uri]=key_data
                        if self.defined_key.encrypto_key.get(key_uri,None):#如有解密方式就解密key(要先有key的内容)
                            ok=self.defined_key.encrypto_key[key_uri](self.key_dic[key_uri])
                            if asyncio.iscoroutine(ok):
                                ok = await ok
                            self.key_dic[key_uri] = ok
            return True
            
    async def Add_MAP(self, filepath, segment : models.Segment)->bool:
        map_data=None
        map_uri=segment.map_uri
        if map_uri and map_uri not in self.map_list:
            file_name = map_uri.rsplit('/',1)[1].rsplit('?',1)[0]
            segment_tmp=[models.MapSegment(after_uri=segment,num=segment.num),file_name]
            if self.config.Wait_Merge:
                self._segment_list.append(segment_tmp)

            map_data,b= await self._down_with_retry(url=map_uri.lstrip('\"\''),headers=self.headers)

               #解密
            if b:
                if segment.key and segment.key.key_uri:
                    map_data=await self.give_DECODE(data=map_data, segment=segment)
                await self.Writefile(map_data, str(filepath / file_name))
            if segment_tmp not in self._segment_list:
                self._segment_list.append(segment_tmp)
                self.map_list.append(map_uri)
            #self._down_with_retry已经抛过并添加金FailedSegment里了不用判断b
            else:
                return False
        return True
        
    async def DownAndDecode(self, segment :Optional[models.Segment], file_path : Optional[Path],progress : Progress=None)->bool:  #只负责将切片(密钥由Add_KEY负责)下载和解密和写入，其他都不负责
        _uri =segment.uri        #正常切片url
        file_name = _uri.rsplit('/',1)[1].rsplit('?',1)[0]
        segment_tmp=[segment, file_name]
        if self.config.Wait_Merge:
            self._segment_list.append(segment_tmp)

        ok_data, b= await self._down_with_retry(_uri, headers=self.headers)      #下载
       
        if b:   #是否正常获取
            if segment.key and segment.key.key_uri:
                ok_data=await self.give_DECODE(data=ok_data,segment=segment)
            _file_path = str(file_path / file_name )    #写入
            await self.Writefile(ok_data, _file_path)
            progress.update(self.task, advance=1)
            if segment_tmp not in self._segment_list:
                self._segment_list.append(segment_tmp)
        else:
            raise exceptions.Down_BadError(url=segment.uri)
        return True
        
    async def downner(self)->dict:
        progress=self.progress
        _file_path=self.path / 'ts_file' / self.outname
        _file_path.mkdir(parents=True,exist_ok=True)
        async def task(segment):
            async with self.semaphore:
                try:
                    if segment.key:
                        await self.Add_KEY(segment)     #记录key
                    await self.Add_MAP(segment=segment, filepath=_file_path)
                    await self.DownAndDecode(segment, _file_path,progress=progress)
                except exceptions.FailedNoMethodError as e:
                    self.Bad_key.append(models.KeyErrorInfo(segment=segment,reason=str(e),exception=exceptions.FailedNoMethodError()))

                except exceptions.FailedMethodError as e:
                    self.Bad_key.append(models.KeyErrorInfo(segment=segment,reason='The encryption type is not supported right now',exception=str(e)))

                except exceptions.FailedDecodeSegmentError as e:
                    self.Bad_key.append(models.KeyErrorInfo(segment=segment,reason='Decoding Bad',exception=str(e)))

                except exceptions.KEYisNoneError as e:
                    self.FailedSegments.append(models.FailedSegment(segment=segment,reason='Key is None',attempts=self.attempts,exception=str(e)))

                except exceptions.Down_BadError as e:
                      self.Bad_key.append(models.FailedSegment(segment=segment,reason='Bad URI',attempts=self.attempts,exception=str(e)))

                except exceptions.FailedSegmentError as e:
                    self.FailedSegments.append(models.FailedSegment(segment=segment,reason='Down or Decode FailedSegmentError',attempts=self.attempts,exception=str(e)))

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    self.FailedSegments.append(models.FailedSegment(segment=segment, reason='Down Failed',attempts=self.attempts, exception=str(e)))

                except Exception as e:
                    self.logger.exception(e)
                    self.FailedSegments.append(models.FailedSegment(segment=segment, reason='Down Failed',attempts=self.attempts, exception=str(e)))
                
        #记录key和下载解密

        await asyncio.gather(*[task(segment) for segment in self.segment_lists])
        self.ts_list=  [fn for seg, fn in sorted(self._segment_list,key=lambda x: (x[0].num, 0 if isinstance(x[0], models.MapSegment) else 1))]
        LIST_PATH = str(_file_path / f'{self.outname}_list.txt')
        async with aiofiles.open(LIST_PATH, 'w', encoding='utf-8') as f:
            for i in self.ts_list:
                a=f'file {i}\n'
                await f.write(a)      
        return {'failed_key':self.FailedKey,
                'failed_segments':self.FailedSegments,
                'key_Error':self.Bad_key,
                'segments_total':len(self.segment_lists),
                'OutputPath':_file_path,
                'list_path':LIST_PATH,
                'key_dic':self.key_dic,
                'map_list':self.map_list,
                'semaphore':self.config.concurrency,
                'time':time.time()-self.start_time
                    }

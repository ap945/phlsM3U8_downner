import asyncio , aiohttp, json, logging, os
logger=logging.getLogger(__name__)
from rich.progress import Progress as rich_progress,SpinnerColumn,TextColumn,BarColumn,MofNCompleteColumn,TimeElapsedColumn,TimeRemainingColumn
from pathlib import Path
from typing import Optional,Any
from dataclasses import dataclass,asdict, is_dataclass
from enum import Enum
from . import parser,models
from . import Download_Manage as _DM
from . import _Converter as _CV
from . import config as Config, resolver, exceptions
"""Bad_Requests是下载失败,Bad_ts是解密失败,Bad_Response是请求m3u8文件内容时失败"""



def json_default(o):
    if is_dataclass(o) and not isinstance(o, type):
        return asdict(o)
    if isinstance(o, Exception):
        return f'{type(o).__name__}: {o}'
    if isinstance(o, Enum):
        return o.value
    if isinstance(o, bytes):
        return o.hex()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(f'{type(o).__name__} not serializable')

def load_records(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text('utf-8'))
    except json.JSONDecodeError:          
        return {}

def rebuild_segment(d)->models.Segment:                                # d 是存储的 segment dict
    k = d.get('key')
    key = None
    if k:
        key = models.key(
            method=models.EncryptMethod(k['method']) if k.get('method') else models.EncryptMethod.NONE,
            
            key_uri=k.get('key_uri'),
            iv=bytes.fromhex(k['iv']) if k.get('iv') else None)   
    return models.Segment(key=key, uri=d['uri'], Duration=d.get('Duration'),
                          num=d['num'], map_uri=d.get('map_uri'))

def save_records(path: Path, records: dict):
    tmp = path.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(records, default=json_default,
        indent=4, ensure_ascii=False), 'utf-8')
    os.replace(tmp, path)

async def main(url_dic : dict, 
            headers= None,
            method : str ='get',
            sem : int = 35 ,
            config : Optional[Config.config] = Config.config(), 
            defined_key : Optional[resolver.defined_decode] =None,
            request_data : Any = None,
            request_json : Any| None =None,
            keep_segments : bool =False)->dict:
    """这个函数控制URL处理、输出路径、进度、状态、失败列表"""
    Result={}
    cfg = config or Config.config()
    M3U8_dic={}
    OutputFileName = {}
    base_path=Path(cfg.data_path)
    DATA_PATH=Path(base_path) / 'data.json'
    Bad_Response=[]
    CSTimeout = aiohttp.ClientTimeout(total=cfg.timeout)
    connector = aiohttp.TCPConnector(
                limit=cfg.limit,
                limit_per_host=sem,
                enable_cleanup_closed=True,
                ssl=cfg.verify_ssl,
            )
    
    async def run(url, session, task ,progress, outname):
        nonlocal Result
        child = None
        try:
            try:
                async with session(url,headers=headers) as response:
                    m3u8_html = await response.text()
                    a=parser._deal_m3u8(url=url, m3u8_html=m3u8_html)#{url : _deal_m3u8(m3u8_html).dic} #这个M3U8_dic是一个数组，数组里面是字典,里面有很多属性,比如ts文件列表,ts文件总数,ts文件总大小等
                    M3U8_dic[url],value=a.parser()
                    if value=='segment':
                        pass
                    elif value=='stream':
                        variants=M3U8_dic[url]
                        progress.console.print(f'[bold]可选清晰度:[/]')
                        for i, s in enumerate(variants):
                            inf = s.INF or {}
                            progress.console.print(f'  {i}: {inf.get("RESOLUTION","?")} BW={inf.get("BANDWIDTH","?")}')
                            
                        while True:
                            try:
                                n = int(await asyncio.to_thread(input, 'Choose a Number: '))  # 函数名，不加括号
                                if 0 <= n < len(variants): break
                            except EOFError: return 0
                            except ValueError: pass
                            progress.console.print('[red]invalid, try again[/]')
                        child = variants[n].uri  
                        OutputFileName[child] = OutputFileName[url]
            except Exception as e:
                Bad_Response.append(models.FailedM3U8Data(url, reason=str(e)))
                return 0
            if child is not None:                               
                return await run(child, session=session,progress=progress,task=task)
            progress.start_task(task_id=task)
            progress.update(task,total=len(M3U8_dic[url]))
            a=_DM.downloader(segment_lists=M3U8_dic[url],
                            headers=headers, 
                            _request=_session, 
                            outname=OutputFileName[url], 
                            defined_key=defined_key,
                            config=cfg,
                            json=request_json,
                            data=request_data,
                            task=task,
                            progress=progress
                            )
            DownnerResult= await a.downner()
            DownloadResult=models.DownloadResult(output_path=DownnerResult['OutputPath'], 
                                                segments_total=DownnerResult['segments_total'], 
                                                segments_succeeded=DownnerResult['segments_total']-len(DownnerResult['failed_segments']),
                                                failed_segments=DownnerResult['failed_segments'],
                                                key_errors=DownnerResult['key_Error'],
                                                duration_seconds=DownnerResult['time'],
                                                file_size_bytes=None,
                                                list_path=DownnerResult['list_path'])
            if not DownnerResult['failed_segments'] and not DownnerResult['key_Error']:
                a = _CV.converter(DownnerResult['list_path'], OutputFileName[url],config.quiet,config.keep_segments)
                try:
                    DownloadResult.file_size_bytes = await a.converter()
                except exceptions.FailedConverterError as e:
                    logger.error('from ffmpeg %s', e)
            else:
                logger.warning('Number segments not enough Plese Down All')
            records[OutputFileName[url]] =DownloadResult
            save_records(DATA_PATH, records)
            Result[OutputFileName[url]]=DownloadResult
        except Exception as e:
            logger.error('%s 崩溃: %r', outname, e, exc_info=e)
            Result[OutputFileName[url]]=models.DownloadResult(
                output_path=outname,
                segments_total=0, segments_succeeded=0,
                failed_segments=[], key_errors=[],
                duration_seconds=0.0, file_size_bytes=0
            )
    async with aiohttp.ClientSession(headers=headers,timeout=CSTimeout, connector=connector, raise_for_status=True) as _session:
        Progress=rich_progress(
                SpinnerColumn("moon", style="cyan"),            # 转圈动画
                TextColumn("[bold blue]{task.description}"),    # 文件名
                BarColumn(
                    bar_width=None,
                    style="dim",                                # 未完成部分
                    complete_style="deep_sky_blue1",            # 已完成
                    finished_style="bold green",                # 完成后整条变绿
                    pulse_style="",                       # total 未知时的呼吸灯
                ),
                MofNCompleteColumn(),                           # "43/87"，正对你 advance=1 的场景
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),                            # 已用时间
                TimeRemainingColumn(),                          # 预计剩余
                transient=False,
                expand=True,                                    # 撑满终端宽度
                disable=not config.Rich
            )
        with Progress as progress:
            aiohttp.ClientSession.raise_for_status
            session = getattr(_session,method.lower())               
            if not cfg.breakpoint_request:#判断断点续传是否为False
                records = load_records(DATA_PATH)   
                tasks=[]
                for url in url_dic:
                    #如果config.Rich是真就挂一个进度条1显示加载中
                    OutputFileName[url]=url_dic[url]
                    task1=progress.add_task(f'{OutputFileName[url][:100]}...', total=None,start=False)
                    task =asyncio.create_task(run(url=url, session=session, task=task1, progress=progress,outname=OutputFileName[url]),name=OutputFileName[url])
                    tasks.append(task)
                results=await asyncio.gather(*tasks,return_exceptions=True,)
                for i in Bad_Response:
                    logger.error('%s Error Failed: %s', i.m3u8_uri, i.reason)
                for t, r in zip(tasks, results):
                    if isinstance(r, Exception):
                        logger.error('%s 崩溃: %r', t.get_name(), r, exc_info=r)
            else:
                
                records = load_records(DATA_PATH)
                if not records:
                    logger.error('No any Info')
                    return 0

                for outname, rec in records.items():#每一个rec都是一个视频
                    failed = rec.get('failed_segments') or []
                    if not failed:
                        continue                                      # 空记录跳过

                    list_path = Path(rec['output_path']) / f'{outname}_list.txt'
                    old_lines = (list_path.read_text('utf-8').splitlines()
                                if list_path.exists() else [])

                    segs = [rebuild_segment(fs['segment']) for fs in failed]#返回一个models.segment对象列表
                    task1=progress.add_task(f'{outname}...', total=None,start=False)
                    dl = _DM.downloader(segment_lists=segs,           
                                        headers=headers, _request=_session,
                                        outname=outname, defined_key=defined_key,
                                        config=cfg, json=request_json, data=request_data,task=task1,progress=progress)
                    progress.start_task(task_id=task1)                    
                    progress.update(task1,total=len(segs))
                    DownnerResult = await dl.downner()

                    #重写list.txt
                    if old_lines:
                        list_path.write_text('\n'.join(old_lines) + '\n', 'utf-8')

                    new_failed = DownnerResult['failed_segments']
                    size = None
                    if not new_failed and old_lines and \
                            len(list(list_path.parent.glob('*'))) - 1 >= len(old_lines):#没有新的失败切片且切片已经够了
                        cv = _CV.converter(str(list_path), str(outname), quiet=cfg.quiet, keep_segments=keep_segments)
                        size = await cv.converter()
                    elif not new_failed and not old_lines:#读list.txt为空
                        logger.error(f'{outname}: list.txt 丢失,已跳过合并\n')

                    records[outname] = models.DownloadResult(         
                        output_path=DownnerResult['OutputPath'],
                        segments_total=rec.get('segments_total') or 0,
                        segments_succeeded=(rec.get('segments_total') or 0) - len(new_failed),
                        failed_segments=new_failed,
                        key_errors=DownnerResult['key_Error'],
                        duration_seconds=DownnerResult['time'],
                        file_size_bytes=size,
                        list_path=DownnerResult['list_path'])                         
                    save_records(DATA_PATH, records)
    return Result
                            





                 
        


if __name__ == "__main__":
    headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'cache-control': 'no-cache',
    'dnt': '1',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'sec-gpc': '1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
}

    # url='https://hls.dscxru.cn/videos5/f4f9aab7beee763bb4b45b9ce2bd246f/f4f9aab7beee763bb4b45b9ce2bd246f.m3u8?auth_key=1788152545-6a950ae1c48e7-0-b7c6ae73970cfe1b6d35a1304a6d06c2&v=3&time=0'
    # url1='https://hls.dscxru.cn/videos5/b954db55fdd0dd747914b7627f5b546e/b954db55fdd0dd747914b7627f5b546e.m3u8?auth_key=1788153308-6a950ddc7f54f-0-84457ac185ae10cde88bd9def9e99ea3&v=3&time=0'
    # url2='https://hls.dscxru.cn/videos5/6009b9239bce806c7f8b967dad6619c3/6009b9239bce806c7f8b967dad6619c3.m3u8?auth_key=1788153208-6a950d78b88d8-0-edead096d4f178adcc66b2839ed7dfe7&v=3&time=0'
    # url3='https://hls.dscxru.cn/videos5/ab573f93d55eb6d544af243e45b1134e/ab573f93d55eb6d544af243e45b1134e.m3u8?auth_key=1788153208-6a950d78b7c42-0-2b16aa6ab2ab2e885ce6c16c1d8f7c8c&v=3&time=0'
    url5='http://127.0.0.1/hls/ma.m3u8'
    
    
    # url='http://127.0.0.1/hls/e/m.m3u8'
    
    # dic={url:'1.mp4',url1:'2.mp4',url2:'3.mp4',url3:'4.mp4',#,'https://hls.dscxru.cn/videos5/b954db55fdd0dd747914b7627f5b546e/b954db55fdd0dd747914b7627f5b546e.m3u8?auth_key=1788065964-6a93b8aca8d66-0-0d59bdf9f86943810b6dd2e8f39d9b06&v=3&time=0':'2.mp4'}
    dic={url5:'6.mp4'}
    # config=Config.config(breakpoint_request=False,Wait_Merge=True,quiet=False)
    a=asyncio.run(main(url_dic=dic, headers=headers))#,config=config))
    print(a)
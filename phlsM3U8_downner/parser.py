import re,logging
from . import models, exceptions
from urllib.parse import urljoin
from dataclasses import dataclass
from typing import Optional

@dataclass
class _deal_m3u8:
    url : Optional[str]
    m3u8_html : Optional[str]

    def __post_init__(self):
        self.base_url=self.url.rsplit('/',1)[0]+'/'
        self.logger=logging.getLogger(__name__)

    def parser(self)->list:  #处理m3u8文件内容
        SEQUENCE=0
        ATTR_RE = re.compile(r'([A-Z0-9-]+)=("[^"]*"|[^,]*)')
        def parse_attrs(s: str) -> dict:
            return {k: v.strip('"') for k, v in ATTR_RE.findall(s)}
        segment_list: Optional[list] =[]
        STREAM_INF=attr_key=MAP_uri=EXTINF=None
        if not self.m3u8_html or not self.m3u8_html.lstrip('\ufeff').startswith('#EXTM3U'):
            raise exceptions.FailedParseM3u8Error(url=self.url, reason='头部没有#EXTM3U标签')
        for line in self.m3u8_html.splitlines():
            line=line.strip()
            if not line:
                continue
            # if line.startswith('#EXT-X-VERSION'):   #匹配版本号
                # m3u8Data.VERSION = line.split(':',1)[1]

            elif line.startswith('#EXT-X-MEDIA-SEQUENCE'):  #匹配序号,直播流的
                SEQUENCE=int(line.split(':',1)[1].strip('\'\",'))
                self.logger.debug('Get SEQUENCE %s',SEQUENCE)
                        
            # elif line.startswith('#EXT-X-TARGETDURATION'):  
                # m3u8_data.TARGETDURATION = line.split(':',1)[1]
                        
            elif line.startswith('#EXT-X-MAP'):  #EXT-X-MAP:URI='video_init.mp4'
                MAP_uri = urljoin(self.base_url,parse_attrs(line.split(':', 1)[1]).get('URI'))
                self.logger.debug('Get-MAP %s',MAP_uri)
                        
            elif line.startswith('#EXT-X-KEY'): #匹配KEY
                attrs = parse_attrs(line.split(':', 1)[1])
                attr_key = models.key(
                    key_uri=urljoin(self.base_url,attrs.get('URI')) if attrs.get('URI') else None ,
                    method=models.EncryptMethod(attrs.get('METHOD', 'NONE')),
                    iv=None
                )
                iv=attrs.get('IV',None)
                if iv:
                    iv=bytes.fromhex(iv.removeprefix('0x')).rjust(16, b'\0')
                    attr_key.iv=iv
                self.logger.debug('Get-Key %s',attr_key)
                
            elif line.startswith('#EXT-X-STREAM-INF'):
                STREAM_INF = parse_attrs(line.split(':', 1)[1])                          #720p/playlist.m3u8
                self.logger.debug('Get-INF %s',attr_key)

                

                        
            elif line.startswith('#EXTINF'):
                EXTINF = float(line.split(':',1)[1].split(',')[0])
                self.logger.debug('Get-EXTINF %s',attr_key)
            elif line.startswith('#EXT-X-DISCONTINUITY'):
                self.logger.debug('Get-DISCONTINUITY %s',attr_key)
                EXTINF=None
                        
            elif not line.startswith('#'):  #到切片了
                if STREAM_INF:
                    segment_list.append(models.StreamM3U8Data(INF=STREAM_INF,uri=urljoin(self.base_url,line)))
                else:
                    segment_list.append(models.Segment(
                    uri=urljoin(self.base_url,line),
                    Duration=EXTINF if EXTINF else None,
                    key=attr_key,
                    map_uri=MAP_uri if MAP_uri else None,
                    num=SEQUENCE+len(segment_list)))
                self.logger.debug('Get-A Segment %s',attr_key)
        if STREAM_INF is not None and STREAM_INF !=[]:
            return segment_list,'stream'

        elif segment_list is not None and segment_list !=[]:
            return segment_list,'segment'
        else:
            self.logger.error('Error %s',exceptions.FailedParseM3u8Error(url=self.url,reason='Check Your URL'))
            raise exceptions.FailedParseM3u8Error(url=self.url,reason='Check Your URL')
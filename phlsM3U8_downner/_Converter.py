from dataclasses import dataclass
from pathlib import Path
import ffmpeg,asyncio,logging
from . import exceptions

"""这个是用来合并文件的"""
@dataclass
class converter:
    def __post_init__(self):
        self.logger = logging.getLogger(__name__)
    LIST_TXT_PATH : str
    OUT_NAME : str
    quiet : bool =False
    keep_segments : bool =False #是否清理分片默认否
    async def converter(self):
        self.logger.debug('Get ready Converter -> %s',self.OUT_NAME)
        self.list_path = Path(self.LIST_TXT_PATH)
        self.out_path=self.list_path.parent / self.OUT_NAME
        self._list_path=self.list_path.read_text()[5:]
        try:
            stream = (
                    ffmpeg.input(str(self.list_path), format='concat', safe=0)
                        .output(str(self.out_path), c='copy').global_args('-nostdin', '-nostats', '-hide_banner', '-loglevel', 'error')
                        )
                
            self.logger.info('Start Converter -> %s',self.OUT_NAME)
            self.logger.debug('ffpeg Order: %s',' '.join(stream.compile()))
            process = stream.run_async(
                pipe_stdin=True, pipe_stdout=True, pipe_stderr=True,
                overwrite_output=True,          # 无条件 -y
            )
            _, stderr = await asyncio.to_thread(process.communicate)

            if process.returncode != 0:
                raise exceptions.FailedConverterError(
                    out_path=str(self.out_path),
                    reason=(stderr or b'').decode('utf-8', 'ignore') or 'no stderr captured',
                )

            delete_list = [
            line.strip().split(' ', 1)[1].strip().strip('\'"')
            for line in self.list_path.read_text(encoding='utf-8').splitlines()
            if line.strip()
            ]
            self.logger.info('Converter Success %s Start delete [ts/m4s/mp4...]file',self.OUT_NAME)
            if not self.keep_segments:
                parent = self.list_path.parent
                for f in delete_list:
                    (parent / f).unlink(missing_ok=True)
                self.list_path.unlink()
            self.logger.info('Converter Success %s',self.OUT_NAME)

            return (self.out_path.stat().st_size)
        except ffmpeg.Error as e:
            self.logger.error('ffmpeg: %s', e)
            raise exceptions.FailedConverterError(str(self.out_path),(e.stderr.decode('utf-8', 'ignore') if getattr(e, 'stderr', None) else str(e)))

        # finally:
        
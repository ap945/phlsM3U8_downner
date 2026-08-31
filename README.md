\# phlsM3U8\_downner



Async HLS/m3u8 downloader with AES-128 decryption and ffmpeg merging.

Supports choosing quality in the main playlist, concurrent slice downloads, AES-128 decryption, and lossless merging with ffmpeg.



\## Install



&#x20;   pip install phlsM3U8\_downner



Requires \*\*ffmpeg\*\* on system PATH:

Windows `winget install ffmpeg` · macOS `brew install ffmpeg` · Linux `sudo apt install ffmpeg`



\## Usage



&#x20;   from phlsM3U8\_down import DownAndMerge



&#x20;   results = DownAndMerge(UrlAndName={"https://example.com/v.m3u8" : "1.mp4"})

&#x20;   r = results\["1.mp4"]

&#x20;   print(r.segments\_succeeded, "/", r.segments\_total)

&#x20;   print(r.output\_path, r.file\_size\_bytes)



\## More Usage

&#x20;   - Config:

&#x20;       in config\_set  It has a lot of settings, see below:

&#x20;   ————————————————                    ————————————————————————————

&#x20;   concurrency: int = 20               # Download several slices at the same time

&#x20;   limit : int = 20                    #Maximum number of requests

&#x20;   timeout: float = 30.0               # Timeout in seconds for a single segment

retries: int = 3                    # Number of retries for a failed segment

retry\_backoff: float = 1.5          # Retry interval multiplier: 1s → 1.5s → 2.25s (exponential backoff)

stop\_after\_delay: float | int = 15  # Maximum total duration of the entire retry process

verify\_ssl: bool = False            # Whether to verify SSL (download-site certificates are often broken; off by default)

keep\_segments: bool = False         # Whether to keep .ts files after a successful merge (False = clean up)

breakpoint\_request: bool = False    # Load previously unfinished files and re-download them (True = re-download)

quiet: bool = False                 # Quiet mode

method: str = 'get'                 # HTTP method for requests

key\_method: str = 'get'             # HTTP method for key requests

data\_path: str | Path = str(Path.cwd() / 'hls\_downloads')  # Location of user\_data (stores .ts/.m4s/.mp4 media files and data.json)

Wait\_Merge: bool = True             # Wait for all downloads to succeed before merging (False = don't wait)

Rich: bool = True                   # Show a progress bar (enabled by default)

&#x20;   ——————————————————                      ————————————————————————

&#x20;              -Notes on `config\_set`:

&#x20;           -If you want to use breakpoint\_request, the failed segments in data.json (failed\_segments/key\_errors) must not be \[], otherwise nothing will happen

&#x20;           -data.json refreshes automatically after a file is downloaded; note that \*\*phlsM3U8\_downner will overwrite existing content\*\*

&#x20;           -If quiet is set to True, most printing will be reduced — even the progress bar will not be output

&#x20;           -key\_method / method: method is the mode for regular segment (segment) file requests, while key\_method is the mode used specifically for key requests; this is useful in some scenarios. You can set them all to \*\*'get'\*\*

&#x20;           -Wait\_Merge: if set to True, it will ignore the failed segments in data.json and instead merge the successful segments, which may result in a merged video that is missing some parts

\- resolver:

&#x20;       -In defined\_decode, \*\*defined\_method\*\* is for custom encryption schemes, but phlsM3U8\_downner may not support them (currently only AES-128 encryption is supported, but that is enough)



&#x20;       -You can use the \*\*defined\_func\*\* parameter to store your functions as \*\*{key\_url: function\_name}\*\*, and phlsM3U8\_downner will use your function to decrypt



&#x20;       -If the retrieved key is itself encrypted, you can use encrypto\_key \*\*{key\_url: function\_name}\*\* to decrypt your key



&#x20;       -If phlsM3U8\_downner cannot obtain the key (e.g., in DRM scenarios), you can use \*\*defined\_key\*\* to supply the key you have obtained (bytes). If you provide \*\*defined\_key\*\*, please make sure to also add \*\*defined\_iv\*\* as \*\*{key\_url: iv}\*\*. Although phlsM3U8\_downner has a built-in fallback that replaces the iv using the sequence number, this is an extra safeguard

&#x20;       (resolver.defined\_method Method resolver.defined\_func func resolver.encrypto\_key encrypto\_key resolver.defined\_iv iv resolver.defined\_key key)

\## Notes

\- Do not use the same output filename for multiple downloads at the same time (the later one will overwrite the earlier one)

\- When downloading multiple master playlists simultaneously, quality must be selected manually — it is recommended to download them one by one

\- For configuration options, see `config\_set.config` (hover in your IDE to view all fields)





\## 0.1.0 first release


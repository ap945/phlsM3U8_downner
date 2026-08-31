## phlsM3U8_downner



Async HLS/m3u8 downloader with AES-128 decryption and ffmpeg merging.

Supports choosing quality in the main playlist, concurrent slice downloads, AES-128 decryption, and lossless merging with ffmpeg.



## Install



##   pip install phlsM3U8_downner



Requires **ffmpeg** on system PATH:

Windows `winget install ffmpeg` · macOS `brew install ffmpeg` · Linux `sudo apt install ffmpeg`



## Usage



##   from phlsM3U8_down import DownAndMerge



##   results = DownAndMerge(UrlAndName={"https://example.com/v.m3u8" : "1.mp4"})

##   r = results["1.mp4"]

##   print(r.segments_succeeded, "/", r.segments_total)

##   print(r.output_path, r.file_size_bytes)



## More Usage

  - Config:

      in config_set  It has a lot of settings, see below:

   ————————————————                    ————————————————————————————

   concurrency: int = 20               # Download several slices at the same time

   limit : int = 20                    #Maximum number of requests

   timeout: float = 30.0               # Timeout in seconds for a single segment

   retries: int = 3                    # Number of retries for a failed segment

   retry_backoff: float = 1.5          # Retry interval multiplier: 1s → 1.5s → 2.25s (exponential backoff)

   stop_after_delay: float | int = 15  # Maximum total duration of the entire retry process

   verify_ssl: bool = False            # Whether to verify SSL (download-site certificates are often broken; off by default)

   keep_segments: bool = False         # Whether to keep .ts files after a successful merge (False = clean up)

   breakpoint_request: bool = False    # Load previously unfinished files and re-download them (True = re-download)

   quiet: bool = False                 # Quiet mode

   method: str = 'get'                 # HTTP method for requests

   key_method: str = 'get'             # HTTP method for key requests

   data_path: str | Path = str(Path.cwd() / 'hls_downloads')  # Location of user_data (stores .ts/.m4s/.mp4 media files and data.json)

   Wait_Merge: bool = True             # Wait for all downloads to succeed before merging (False = don't wait)

   Rich: bool = True                   # Show a progress bar (enabled by default)

   ——————————————————                      ————————————————————————

         -Notes on `config_set`:

         -If you want to use breakpoint_request, the failed segments in data.json (failed_segments/key_errors) must not be [], otherwise nothing will happen

         -data.json refreshes automatically after a file is downloaded; note that **phlsM3U8_downner will overwrite existing content**

         -If quiet is set to True, most printing will be reduced — even the progress bar will not be output

         -key_method / method: method is the mode for regular segment (segment) file requests, while key_method is the mode used specifically for key requests; this is useful in some scenarios. You can set them all to **'get'**

         -Wait_Merge: if set to True, it will ignore the failed segments in data.json and instead merge the successful segments, which may result in a merged video that is missing some parts

- resolver:

      -In defined_decode, **defined_method** is for custom encryption schemes, but phlsM3U8_downner may not support them (currently only AES-128 encryption is     supported, but that is enough)



       -You can use the **defined_func** parameter to store your functions as **{key_url: function_name}**, and phlsM3U8_downner will use your function to decrypt



       -If the retrieved key is itself encrypted, you can use encrypto_key **{key_url: function_name}** to decrypt your key



       -If phlsM3U8_downner cannot obtain the key (e.g., in DRM scenarios), you can use **defined_key** to supply the key you have obtained (bytes). If you provide **defined_key**, please make sure to also add **defined_iv** as **{key_url: iv}**. Although phlsM3U8_downner has a built-in fallback that replaces the iv using the sequence number, this is an extra safeguard

       (resolver.defined_method Method resolver.defined_func func resolver.encrypto_key encrypto_key resolver.defined_iv iv resolver.defined_key key)

## Notes

- Do not use the same output filename for multiple downloads at the same time (the later one will overwrite the earlier one)

- When downloading multiple master playlists simultaneously, quality must be selected manually — it is recommended to download them one by one

- For configuration options, see `config_set.config` (hover in your IDE to view all fields)


## 0.1.1 Chinese logging -> English logging 


## 0.1.0 first release


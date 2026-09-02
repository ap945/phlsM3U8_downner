



## phlsM3U8_downner



Async HLS/m3u8 downloader with AES-128 decryption and ffmpeg merging.

Supports choosing quality in the main playlist, concurrent slice downloads, AES-128 decryption, and lossless merging with ffmpeg.



## Install
    pip install phlsM3U8_downner


## Update pack
    pip install --upgrade phlsM3U8_downner
————————————————————————————————————————————————

Requires **ffmpeg** on system PATH:

Windows `winget install ffmpeg` · macOS `brew install ffmpeg` · Linux `sudo apt install ffmpeg`



## Usage


# import phlsM3U8_downner 

**Or**

# from phlsM3U8_downner import * #import all functions
#Here I use 'import phlsM3U8_downner' 

![eazy](./docs/image/config_use.png)

#you can see down a video success:

![example](./docs/video/down.gif)

#This is a very simple example



## More Usage

  - Config:

      in Config  It has a lot of settings, see below:
    ![config](./docs/image/config.png)

-How use Condig?
  ![config_use](./docs/image/config_use.png)

#Notes on `Config`:

         - If you want to use breakpoint_request, the failed segments in data.json (failed_segments and key_errors) must not be [], otherwise nothing will happen

         - data.json refreshes automatically after a file is downloaded; note that **phlsM3U8_downner will overwrite existing content**

         - If quiet is set to True, most printing will be reduced — even the progress bar will not be output

         - key_method / method: method is the mode for regular segment (segment) file requests, while key_method is the mode used specifically for key requests; this is useful in some scenarios. You can set them all to **'get'**

         - Wait_Merge: if set to True, it will ignore the failed segments in data.json and instead merge the successful segments, which may result in a merged video that is missing some parts

- resolver:

      -In defined_decode, **defined_method** is for custom encryption schemes, but phlsM3U8_downner may not support them (currently only AES-128 encryption is     supported, but that is enough)



       -You can use the **defined_func** parameter to store your functions as **{key_url: function_name}**, and phlsM3U8_downner will use your function to decrypt



       -If the retrieved key is itself encrypted, you can use encrypto_key **{key_url: function_name}** to decrypt your key



       -If phlsM3U8_downner cannot obtain the key (e.g., in DRM scenarios), you can use **defined_key** to supply the key you have obtained (bytes). If you provide **defined_key**, please make sure to also add **defined_iv** as **{key_url: iv}**. Although phlsM3U8_downner has a built-in fallback that replaces the iv using the sequence number, this is an extra safeguard

       (resolver.defined_method Method resolver.defined_func func resolver.encrypto_key encrypto_key resolver.defined_iv iv resolver.defined_key key)

- how use? example of resolver:
   ![resolver](./docs/image/resolver1.png)
- Each key_uri corresponds to a value, pass it with a dictionary, and once passed, just run the program. The program will use key_uri as the key to prioritise finding the value in the resolver

## Notes

- Do not use the same output filename for multiple downloads at the same time (the later one will overwrite the earlier one)

- When downloading multiple master playlists simultaneously, quality must be selected manually — it is recommended to download them one by one

- For configuration options, see `Config` (hover in your IDE to view all fields)
##data.json
  -data.json By default will be at hls_downloads\data.json
  -If you want to change the directory, for example in cases where the directory is duplicated, you just need to change the value of data_path in the config
![data_path](./docs/image/data_path1.png)
  -After starting, data.json will be created in the example folder, note that the original data.json data will not be copied into the new data.json file

  
  ![data_path1](./docs/image/user_data1.png)

  
##breadkpoint_requese of config
  -Sometimes you see download failures like this
![Failed1](./docs/image/Failed1.png)
![Failed1gif](./docs/video/Failed1show.gif)
  -At this point, you'll see the data.json file show the following content
![data.jsonFailed_show](./docs/image/data.jsonFailed_show.png)
  -This means either key_error or FailedSegments is not None
  -You can set breakpoint_request is True
![breakpoint1](./docs/image/breakpoint1.png)
  -Then when you run it, it will automatically read the failed files in data.json and download and merge them
![breakpoint2](docs/video/breakpoint1show.gif)
  -Meanwhile, the corresponding data in data.json will be cleared

## Changelog
    ## 0.1.5 fix bug

    ## 0.1.4 Update the Detailed_Information property in the config to show detailed retry report info

    ## 0.1.3 optimise
      
    ## 0.1.2 None
      
    ## 0.1.1 Chinese logging -> English logging 
    
    ## 0.1.0 first release


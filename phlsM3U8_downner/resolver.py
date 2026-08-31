from dataclasses import dataclass, field
from typing import Optional         
from . import models

@dataclass
class defined_decode:
    defined_method: Optional[models.EncryptMethod] = models.EncryptMethod.NONE   #key Unify
    defined_key: dict = field(default_factory=dict)   
    defined_iv: dict = field(default_factory=dict)    
    defined_func: Optional[dict] = field(default_factory=dict)            # 自定义解密 f(data, key, iv)
    encrypto_key: Optional[dict] = field(default_factory=dict)           # key 二次处理 f(key_bytes)

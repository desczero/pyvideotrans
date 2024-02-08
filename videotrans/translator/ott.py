# -*- coding: utf-8 -*-
import re

import requests
import json
from videotrans.configure import config
from videotrans.util import tools


def trans(text_list, target_language="en", *, set_p=True):
    """
    text_list:
        可能是多行字符串，也可能是格式化后的字幕对象数组
    target_language:
        目标语言
    set_p:
        是否实时输出日志，主界面中需要
    """

    # 翻译后的文本
    target_text = []
    # 整理待翻译的文字为 List[str]
    if isinstance(text_list, str):
        source_text = text_list.strip().split("\n")
    else:
        source_text = [t['text'] for t in text_list]

    # 切割为每次翻译多少行，值在 set.ini中设定，默认10
    split_size = int(config.settings['trans_thread'])
    split_source_text = [source_text[i:i + split_size] for i in range(0, len(source_text), split_size)]

    for it in split_source_text:
        try:
            source_length = len(it)
            print(f'{source_length=}')
            data = {
                "q": "\n".join(it),
                "source": "auto",
                "target": target_language
            }

            url=config.params['ott_address'].strip().rstrip('/').replace('/translate','')+'/translate'
            url=url.replace('//translate','/translate')
            if not url.startswith('http'):
                url=f"http://{url}"
            try:
                response = requests.post(url=url,json=data,proxies={"http":"","https":""})
                result = response.json()
            except Exception as e:
                msg = f"[error]OTT出错了，请检查部署和地址: {str(e)}"
                config.logger.info(f'OTT {msg}')
                raise Exception(msg)

            if response.status_code != 200:
                msg=f"[error]OTT出错了，请检查部署和地址:{response=}"
                config.logger.error(msg)
                raise Exception(msg)
            if "error" in result:
                raise Exception(result['error'])
            result=result['translatedText'].strip().replace('&#39;','"').split("\n")
            if set_p:
                tools.set_process("\n\n".join(result), 'subtitle')
            else:
                tools.set_process("\n\n".join(result), func_name="set_fanyi")
            result_length = len(result)
            while result_length < source_length:
                result.append("")
                result_length += 1
            result = result[:source_length]
            target_text.extend(result)
        except Exception as e:
            error = str(e)
            raise Exception(f'[error]OTT出错了，请检查部署和地址:{str(error)}')

    if isinstance(text_list, str):
        return "\n".join(target_text)

    max_i = len(target_text)
    for i, it in enumerate(text_list):
        if i < max_i:
            text_list[i]['text'] = target_text[i]
    return text_list
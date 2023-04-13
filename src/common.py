import argparse
import os
import sys
import time
import pyperclip
import tiktoken

from revChatGPT.V1 import Chatbot, configure

TRUNCK_TOKEN_SIZE = 2800
TRUNCK_STR_SIZE = 11500

def get_next_trunk_str(encoder: tiktoken.Encoding, tockens: list[int], tocken_index: int) -> tuple[str, int]:
    chunk_tocken_size = TRUNCK_TOKEN_SIZE
    chunk_str = ''
    while True:
        chunk_tockens = tockens[tocken_index : tocken_index + chunk_tocken_size]
        chunk_str = encoder.decode(chunk_tockens)
        if len(chunk_str) > TRUNCK_STR_SIZE:
            chunk_tocken_size = int(chunk_tocken_size * 0.9)
        else:
            return chunk_str, tocken_index + chunk_tocken_size

def split_code(gpt_mode: str, code: str) -> tuple[list[str], int]:
    encoder = tiktoken.encoding_for_model(gpt_mode)
    tockens = encoder.encode(code)
    result = []
    tocken_index = 0
    while True:
        chunk_str, next_tocken_index = get_next_trunk_str(encoder, tockens, tocken_index)
        result.append(chunk_str)
        # print(f'Chunk str length: {len(chunk_str)} token_count: {next_tocken_index - tocken_index}')
        if next_tocken_index >= len(tockens):
            break
        tocken_index = next_tocken_index
    
    return result, len(tockens)

def ask_trunk_impl(bot: Chatbot, prompt_prefix: str, trunk: str, log_prefix = '') -> str:
    print(f'${log_prefix}Ask: {prompt_prefix} length: {len(trunk)}\n')
    prev_text = ''
    for data in bot.ask(prompt_prefix + trunk):
        message = data["message"][len(prev_text) :]
        print(message, end="", flush=True)
        prev_text = data["message"]
    
    print('\n-----------------------------------------------------------------')
    return prev_text

def ask(bot: Chatbot, prompt_prefix: str, code: str, log_prefix = '') -> str:
    max_retry_count = 10
    for i in range(0, max_retry_count):
        try:
            return ask_trunk_impl(bot, prompt_prefix, code, log_prefix)
        except Exception as e:
            print(f'错误:{e}')
            print(f'\n[{i+1}/{max_retry_count}]3秒后重试')
            time.sleep(3)
    raise Exception(f'重试次数超过上限{max_retry_count}')

class Prompt:
    def __init__(self, trunk_first, trunk_next, sumarize_muti, sumarize_single) -> None:
        self.trunk_first = trunk_first
        self.trunk_next = trunk_next
        self.sumarize_muti = sumarize_muti
        self.sumarize_single = sumarize_single

def do_code_explain(bot: Chatbot, content: str, prompt: Prompt ) -> str:
    trunks, token_count = split_code(bot.config['model'], content)
    print(f'Code length: {len(content)} token_count: {token_count} trunks: {len(trunks)}')
    if len(trunks) > 1:
        texts = []
        i = 0
        for trunk in trunks:
            i += 1
            prompt = prompt.trunk_first if i == 1 else prompt.trunk_next
            texts.append(ask(bot, prompt, trunk, f'[{i}/{len(trunks)}] '))
        return ask(bot, prompt.sumarize_muti, '\n'.join(texts))
    else:
        return ask(bot, prompt.sumarize_single, content)

def do_code_explain_cmd(path: str, prompt: Prompt) -> str:
    if not os.path.exists(path):
        print(f'路径不存在:{path}')
        return

    print(f'代码路径: {path}')
    
    with open(path, 'r') as f:
        code = f.read()
        conf = configure()
        # print(conf)
        bot = Chatbot(conf)
        result = do_code_explain(bot, code, prompt)

        max_retry_delete = 10
        for i in range(0, max_retry_delete):
            try:
                bot.delete_conversation(bot.conversation_id)
                break
            except Exception as e:
                print(f'错误:{e}')
                print(f'\n[{i+1}/{max_retry_delete}]删除会话失败，3秒后重试')
                time.sleep(3)
        
        return result

def create_args_parser(prog_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=prog_name)
    parser.add_argument('-t', '--test', action='store_true', help='是否为测试模式')
    parser.add_argument('-c', '--cache', action='store_true', help='是否使用缓存')
    parser.add_argument('-f', '--file', help='是否检查错误')

    return parser

def to_cache_path(name:str, path: str) -> str:
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    formated_path = path.replace('/', '_').replace('\\', '_').replace(':', '_')
    home = os.getenv('HOME')
    if not home:
        home = os.getenv('USERPROFILE')
    return os.path.normpath(os.path.join(home, '.code_explainer/cache', name, formated_path))

def read_cache(name: str, path: str) -> str:
    cache_path = to_cache_path(name, path)
    if not os.path.exists(cache_path):
        return ''
    
    if os.path.getmtime(path) > os.path.getmtime(cache_path):
        return ''

    with open(cache_path, 'r') as f:
        print(f'读取缓存: {cache_path}')
        return f.read()

def write_cache(name: str, path: str, content: str) -> None:
    cache_path = to_cache_path(name, path)
    if not os.path.exists(cache_path):
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    with open(cache_path, 'w') as f:
        print(f'写入缓存: {cache_path}')
        f.write(content)

def test_split_code():
    path = 'D:\\Aki\\Source\\Client\\TypeScript\\Src\\Core\\Net\\Net.ts'
    with open(path, 'r') as f:
        code = f.read()
        trunks, token_count = split_code('gpt-3.5-turbo', code)
        print(f'Code length: {len(code)} token_count: {token_count} trunks: {len(trunks)}')

def test_get_cache_path():
    print(to_cache_path('revChatGPT/typings.py'))
    print(to_cache_path('f:\\revChatGPT\\typings.py'))

def test():
    test_split_code()

def run_by_prompt(prompt: Prompt, prog_name: str, test_fun = None, args = None) -> None:
    parser = create_args_parser(prog_name)
    args = parser.parse_args(args)

    print(sys.argv)

    if args.test:
        test_fun() if test_fun else test()
        exit(0)

    if not args.file:
        print(parser.format_help())
        exit(0)

    if args.cache:
        result = read_cache(prog_name, args.file)
        if result:
            print(result)
            print(f'\n已复制到剪贴板')
            pyperclip.copy(result)
            exit(0)
    
    if args.file:
        result = do_code_explain_cmd(args.file, prompt)
        if not result:
            exit(1)

        if args.cache:
            write_cache(prog_name, args.file, result)
        
        pyperclip.copy(result)
        print(f'\n已复制到剪贴板')
        exit(0)

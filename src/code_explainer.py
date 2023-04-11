import os
import sys
import time
from revChatGPT.V1 import Chatbot, configure
import tiktoken
import pyperclip

GPT_MODE = 'gpt-3.5-turbo'

TRUNCK_SIZE = 1024
CODE_PROMPT = 'You are professinal programmer, explain the code, reply in chinese:'
SUMARIZE_PROMPT = '''Summarize the following text with the most unique and helpful points, into a numbered list of key points and takeaways, reply in chinese:'''

def split_code(gpt_mode: str, code: str) -> tuple[list[str], int]:
    encoder = tiktoken.encoding_for_model(gpt_mode)
    tockens = encoder.encode(code)
    result = []
    for i in range(0, len(tockens), TRUNCK_SIZE):
        result.append(encoder.decode(tockens[i : i + TRUNCK_SIZE]))
    return result, len(tockens)

def ask_trunk(bot: Chatbot, prompt_prefix: str, trunk: str, log_prefix = '') -> str:
    print(f'${log_prefix}Ask: {prompt_prefix} length: {len(trunk)}')
    prev_text = ''
    for data in bot.ask(prompt_prefix + trunk):
        message = data["message"][len(prev_text) :]
        print(message, end="", flush=True)
        prev_text = data["message"]
    
    print('\n-----------------------------------------------------------------')
    return prev_text

def do_code_explain(bot: Chatbot, content: str) -> str:
    trunks, token_count = split_code(bot.config['model'], content)
    print(f'Code length: {len(content)} token_count: {token_count} trunks: {len(trunks)}')
    if len(trunks) > 1:
        texts = []
        i = 0
        for trunk in trunks:
            i += 1
            texts.append(ask_trunk(bot, CODE_PROMPT, trunk, f'[{i}/{len(trunks)}] '))
        return ask_trunk(bot, SUMARIZE_PROMPT, '\n'.join(texts))
    else:
        return ask_trunk(bot, SUMARIZE_PROMPT, content)

def do_code_explain_cmd(path: str):
    if not os.path.exists(path):
        print(f'路径不存在:{path}')
        return

    print(f'代码路径: {path}')
    with open(path, 'r') as f:
        code = f.read()
        bot = Chatbot(configure())
        result = do_code_explain(bot, code)
        pyperclip.copy(result)
        print('已复制到剪贴板')

        bot.delete_conversation(bot.conversation_id)


def test():
    path = 'revChatGPT/typings.py'
    with open(path, 'r') as f:
        code = f.read()
        trunks, token_count = split_code(GPT_MODE, code)
        print(f'Code length: {len(code)} token_count: {token_count} trunks: {len(trunks)}')
        for trunk in trunks:
            print('-----------------------------------------------------------------')
            print(trunk)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == '-t':
            test()
        else:
            for i in range(1, 3):
                try:
                    do_code_explain_cmd(sys.argv[1])
                    break
                except Exception as e:
                    print(f'错误:{e}')
                    print('\n3秒后重试')
                    time.sleep(3)
            
    else:
        print('请提供需要解析的文件路径')

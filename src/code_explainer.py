from common import Prompt, run_by_prompt

TRUNK_PROMPT_FIRST = '''The code I sent you is a part of a code file.
Please help me generate a summary.
After all the summaries are generated, I will send them to you together for the final summary.
Please make sure the summaries you generate are easy for you to perform the final summary:'''

TRUNK_PROMPT_NEXT = '''The following code is a follow-up to the code I sent you before,
and all of them come from the same file.
Please continue to generate summary:'''

SUMARIZE_MUTI_PROMPT = '''The following content is a summary of different parts of the same code file.
Please summarize them with the most unique and helpful points, into a list of key points and takeaways.
Please reply in chinese:'''

SUMARIZE_SINGLE_PROMPT = '''The texts I send to you are all come form the same code file,
Summarize them with the most unique and helpful points,
into a list of key points and takeaways. Reply in chinese:'''

def create_prompt() -> Prompt:
    return Prompt(
        TRUNK_PROMPT_FIRST,
        TRUNK_PROMPT_NEXT,
        SUMARIZE_MUTI_PROMPT,
        SUMARIZE_SINGLE_PROMPT
    )

if __name__ == '__main__':
    run_by_prompt(create_prompt(), 'code_explainer')

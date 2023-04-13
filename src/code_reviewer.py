import os
import tempfile
from common import Prompt, run_by_prompt

TRUNK_PROMPT_FIRST = '''The content I sent you is a part of a code patch.
please help me do a brief code review. If any bug risk and improvement suggestion are welcome.
After all the code review are generated, I will send them to you together for the final summary.
Please make sure the reviews you generate are easy for you to perform the final review.
Reply in chinese:'''

TRUNK_PROMPT_NEXT = '''The following code patch is a follow-up to the code patch I sent you before,
and all of them come from the same code patch. If any bug risk and improvement suggestion are welcome.
Please continue to do code view. Reply in chinese:'''

SUMARIZE_MUTI_PROMPT = '''The following content is code reviews of different parts of the same code patch.
Please summarize them with the most unique and helpful points, into a list of key points and takeaways.
Reply in chinese:'''

SUMARIZE_SINGLE_PROMPT = '''Bellow is the code patch, please help me do a brief code review.
If any bug risk and improvement suggestion are welcome. Reply in chinese:'''

def create_prompt() -> Prompt:
    return Prompt(
        TRUNK_PROMPT_FIRST,
        TRUNK_PROMPT_NEXT,
        SUMARIZE_MUTI_PROMPT,
        SUMARIZE_SINGLE_PROMPT
    )

if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, 'patch.txt')
        os.system(f'git format-patch -1 --stdout > {temp_path}')
        run_by_prompt(create_prompt(), 'code_reviewer', args=['-f', temp_path])

import os, sys
import git
from common import Prompt, get_save_path, run_app_by_prompt

TRUNK_PROMPT_FIRST = '''The content I sent you is a part of a code patch.
please help me do a brief code review. If any bug risk and improvement suggestion are welcome.
After all the code review are generated, I will send them to you together for the final summary.
Please make sure the reviews you generate are easy for you to perform the final review.
Reply in chinese:'''

TRUNK_PROMPT_NEXT = '''Please continue to do code view.
If any bug risk and improvement suggestion are welcome. Reply in chinese:'''

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
    file = sys.argv[1]
    if not os.path.exists(file):
        print(f'文件{file}不存在')
        exit(1)

    repo = git.Repo(os.path.dirname(file), search_parent_directories=True)
    if not repo:
        print(f'文件[{file}]所在目录不是git仓库')
        exit(1)
    
    repo_name = os.path.basename(repo.working_dir)
    patch_path = os.path.join(get_save_path(), f'{repo_name}.patch')
    if repo.is_dirty():
        repo.git.add(A=True)
        repo.index.commit('code_reviewer自动提交')
        os.system(f'cd {os.path.dirname(file)} && git format-patch -1 --stdout > {patch_path}')
        repo.git.reset('HEAD~1')
    else:
        os.system(f'cd {os.path.dirname(file)} && git format-patch -1 --stdout > {patch_path}')

    if not os.path.exists(patch_path):
        print(f'无法生成patch文件, 请检查文件[{file}]所在目录是否为git仓库')
        exit(1)

    print(f'生成patch文件[{patch_path}]')
    run_app_by_prompt(create_prompt(), 'code_reviewer', args=['-f', patch_path])

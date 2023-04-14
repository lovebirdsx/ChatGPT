import argparse
import os
import git
from app import get_save_path
from asker import Prompt, do_ask_for_large_file_cmd
from common import open_file, write_file

TRUNK_PROMPT_FIRST = '''The content I sent you is a part of a code patch.
please help me do a brief code review. If any bug risk and improvement suggestion are welcome.
Reply in chinese:'''

TRUNK_PROMPT_NEXT = '''Please continue to do code view.
If any bug risk and improvement suggestion are welcome. Reply in chinese:'''

SUMARIZE_MUTI_PROMPT = '''The following content is code reviews of different parts of the same code patch.
Please summarize them with the most unique and helpful points, into a list of key points and takeaways.
Reply in chinese:'''

SUMARIZE_SINGLE_PROMPT = '''Bellow is the code patch, please help me do a brief code review.
If any bug risk and improvement suggestion are welcome. Reply in chinese:'''

PROG_NAME = 'code_reviewer'

def create_prompt() -> Prompt:
    return Prompt(
        TRUNK_PROMPT_FIRST,
        TRUNK_PROMPT_NEXT,
        SUMARIZE_MUTI_PROMPT,
        SUMARIZE_SINGLE_PROMPT
    )

def create_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=PROG_NAME)
    parser.add_argument('-t', '--test', action='store_true', help='是否为测试模式')
    parser.add_argument('-f', '--file', help='文件路径，将以此文件所在目录为git仓库根目录')

    return parser

def gen_patch(repo: git.Repo, file) -> str:
    if not repo:
        raise Exception(f'文件[{file}]所在目录不是git仓库')
    
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
        raise Exception(f'无法生成patch文件, 请检查文件[{file}]所在目录是否为git仓库')
    return patch_path

def gen_review_header(repo: git.Repo) -> str:
    repo_name = os.path.basename(repo.working_dir)
    branch_name = repo.active_branch.name
    commit_id = repo.head.commit.hexsha
    commit_message = repo.head.commit.message

    if not repo.is_dirty():
        lines = [
            f'# 版本库：{repo_name} 分支：{branch_name} 提交：{commit_id}',
            '',
            f'提交信息 {commit_message} by {repo.head.commit.author}',
            '',
        ]
    else:
        lines = [
            f'# 版本库：{repo_name} 分支：{branch_name} (未提交)',
            '',
        ]
    return '\r\n'.join(lines)
    

def test() -> None:
    repo = git.Repo(os.path.dirname(__file__), search_parent_directories=True)
    print(gen_review_header(repo))


if __name__ == '__main__':
    parser = create_args_parser()
    args = parser.parse_args()

    if args.test:
        test()
        exit(0)

    file = args.file
    if not file:
        print(parser.format_help())
        exit(0)

    repo = git.Repo(os.path.dirname(file), search_parent_directories=True)
    patch_path = gen_patch(repo, file)
    print(f'生成patch文件[{patch_path}]')

    prompt = create_prompt()
    result = do_ask_for_large_file_cmd(patch_path, prompt)
    
    review_header = gen_review_header(repo)
    repo_name = os.path.basename(repo.working_dir)
    result_path = os.path.normpath(os.path.join(get_save_path(), f'code_reviewer/{repo_name}.md'))
    write_file(result_path, review_header + result)
    print(f'结果保存在：{result_path}')
    open_file(result_path)
        
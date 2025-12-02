# # https://github.com/microsoft/autogen/blob/19de99e3f6e46f6040d54c4a55785d02158dec28/autogen/code_utils.py

# import os
# import pathlib
# import subprocess
# import sys
# from concurrent.futures import ThreadPoolExecutor
# from hashlib import md5
# from typing import Optional

# # I think I should patch this for Linux

# WORKING_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "extensions")
# TIMEOUT_MSG = "Code execution timeout"
# DEFAULT_TIMEOUT = 600
# WIN32 = sys.platform == "win32"
# PATH_SEPARATOR = WIN32 and "\\" or "/"
# PYTHON_VARIANTS = ["python", "Python", "py"]

# import nbformat
# from nbclient import NotebookClient
# from nbclient.exceptions import CellExecutionError
# from io import StringIO
# import sys

# def _execute_code(code: str) -> str:
#     """使用Jupyter notebook客户端执行代码

#     Args:
#         code (str): 要执行的Python代码字符串

#     Returns:
#         str: 执行结果或错误信息
#     """
#     # 创建一个新的 Jupyter 笔记本对象
#     nb = nbformat.v4.new_notebook()
    
#     # 将代码字符串添加为一个新的代码单元
#     code_cell = nbformat.v4.new_code_cell(code)
#     nb.cells.append(code_cell)
    
#     # 捕获标准输出和标准错误
#     stdout = StringIO()
#     stderr = StringIO()
    
#     # 保存原始的 stdout 和 stderr
#     original_stdout = sys.stdout
#     original_stderr = sys.stderr
    
#     try:
#         # 重定向 stdout 和 stderr
#         sys.stdout = stdout
#         sys.stderr = stderr
        
#         # 创建笔记本客户端并执行
#         client = NotebookClient(nb, timeout=DEFAULT_TIMEOUT)
#         client.execute(nb)
        
#         # 获取执行结果
#         if len(nb.cells[0].outputs) > 0:
#             # 收集所有输出
#             outputs = []
#             for output in nb.cells[0].outputs:
#                 if output.output_type == 'stream':
#                     outputs.append(output.text)
#                 elif output.output_type == 'execute_result':
#                     outputs.append(str(output.data.get('text/plain', '')))
#                 elif output.output_type == 'error':
#                     return '\n'.join(output.traceback)
#             return '\n'.join(outputs)
        
#         # 如果没有输出，返回stdout的内容
#         return stdout.getvalue() or "Code executed successfully with no output."
        
#     except CellExecutionError as e:
#         return f"Execution error: {str(e)}"
#     except Exception as e:
#         return f"Error: {str(e)}"
#     finally:
#         # 恢复原始的 stdout 和 stderr
#         sys.stdout = original_stdout
#         sys.stderr = original_stderr




# def get_powershell_command():
#     try:
#         result = subprocess.run(
#             ["powershell", "$PSVersionTable.PSVersion.Major"],
#             capture_output=True,
#             text=True,
#         )
#         if result.returncode == 0:
#             return "powershell"
#     except (FileNotFoundError, NotADirectoryError):
#         # This means that 'powershell' command is not found so now we try looking for 'pwsh'
#         try:
#             result = subprocess.run(
#                 ["pwsh", "-Command", "$PSVersionTable.PSVersion.Major"],
#                 capture_output=True,
#                 text=True,
#             )
#             if result.returncode == 0:
#                 return "pwsh"
#         except FileExistsError as e:
#             raise FileNotFoundError(
#                 "Neither powershell.exe nor pwsh.exe is present in the system. "
#                 "Please install PowerShell and try again. "
#             ) from e
#         except NotADirectoryError as e:
#             raise NotADirectoryError(
#                 "PowerShell is either not installed or its path is not given "
#                 "properly in the environment variable PATH. Please check the "
#                 "path and try again. "
#             ) from e
#     except PermissionError as e:
#         raise PermissionError("No permission to run powershell.") from e


# def _cmd(lang: str) -> str:
#     if lang in PYTHON_VARIANTS:
#         return "python"
#     if lang.startswith("python") or lang in ["bash", "sh"]:
#         return lang
#     if lang in ["shell"]:
#         return "sh"
#     if lang == "javascript":
#         return "node"
#     if lang in ["ps1", "pwsh", "powershell"]:
#         powershell_command = get_powershell_command()
#         return powershell_command

#     raise NotImplementedError(f"{lang} not recognized in code execution")


# def execute_code(
#     code: Optional[str] = None,
#     filename: Optional[str] = None,
#     work_dir: Optional[str] = None,
#     lang: Optional[str] = "python",
# ) -> str:
#     """Execute code in a docker container.
#     This function is not tested on MacOS.

#     Args:
#         code (Optional, str): The code to execute.
#             If None, the code from the file specified by filename will be executed.
#             Either code or filename must be provided.
#         filename (Optional, str): The file name to save the code or where the code is stored when `code` is None.
#             If None, a file with a randomly generated name will be created.
#             The randomly generated file will be deleted after execution.
#             The file name must be a relative path. Relative paths are relative to the working directory.
#         work_dir (Optional, str): The working directory for the code execution.
#             If None, a default working directory will be used.
#             The default working directory is the "extensions" directory
#         lang (Optional, str): The language of the code. Default is "python".

#     Returns:
#         str: The error message if the code fails to execute; the stdout otherwise.
#     """
#     if all((code is None, filename is None)):
#         error_msg = f"Either {code=} or {filename=} must be provided."
#         return error_msg

#     original_filename = filename
#     if filename is None:
#         code_hash = md5(code.encode()).hexdigest()
#         # create a file with a automatically generated name
#         filename = f"tmp_code_{code_hash}.{'py' if lang.startswith('python') else lang}"
#     if work_dir is None:
#         work_dir = WORKING_DIR

#     filepath = os.path.join(work_dir, filename)
#     file_dir = os.path.dirname(filepath)
#     os.makedirs(file_dir, exist_ok=True)

#     if code is not None:
#         with open(filepath, "w", encoding="utf-8") as fout:
#             fout.write(code)

#     cmd = [
#         sys.executable if lang.startswith("python") else _cmd(lang),
#         f".\\{filename}" if WIN32 else filename,
#     ]
#     with ThreadPoolExecutor(max_workers=1) as executor:
#         future = executor.submit(
#             subprocess.run, cmd, cwd=work_dir, capture_output=True, text=True, timeout=DEFAULT_TIMEOUT
#         )
#         try:
#             result = future.result(timeout=DEFAULT_TIMEOUT)
#         except subprocess.TimeoutExpired:
#             if original_filename is None:
#                 os.remove(filepath)
#             return TIMEOUT_MSG
#         except TimeoutError:
#             if original_filename is None:
#                 os.remove(filepath)
#             return TIMEOUT_MSG
#     if original_filename is None:
#         os.remove(filepath)
#     if result.returncode:
#         logs = result.stderr
#         if original_filename is None:
#             abs_path = str(pathlib.Path(filepath).absolute())
#             logs = logs.replace(str(abs_path), "").replace(filename, "")
#         else:
#             abs_path = str(pathlib.Path(work_dir).absolute()) + PATH_SEPARATOR
#             logs = logs.replace(str(abs_path), "")
#     else:
#         logs = result.stdout
#     return logs


import os
import pathlib
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from hashlib import md5
from typing import Optional
from io import StringIO

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

# === Linux Simplified Constants ===
WORKING_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "extensions")
TIMEOUT_MSG = "Code execution timeout"
DEFAULT_TIMEOUT = 600
PATH_SEPARATOR = "/"
PYTHON_VARIANTS = ["python", "Python", "py", "python3"]


# === Internal Jupyter-based Python executor ===
def _execute_code(code: str) -> str:
    """
    Execute Python code using Jupyter notebook client.

    Args:
        code (str): Python code as string.
    Returns:
        str: Execution output or error message.
    """
    nb = nbformat.v4.new_notebook()
    code_cell = nbformat.v4.new_code_cell(code)
    nb.cells.append(code_cell)

    stdout = StringIO()
    stderr = StringIO()
    original_stdout, original_stderr = sys.stdout, sys.stderr

    try:
        sys.stdout, sys.stderr = stdout, stderr
        client = NotebookClient(nb, timeout=DEFAULT_TIMEOUT)
        client.execute(nb)

        if len(nb.cells[0].outputs) > 0:
            outputs = []
            for output in nb.cells[0].outputs:
                if output.output_type == 'stream':
                    outputs.append(output.text)
                elif output.output_type == 'execute_result':
                    outputs.append(str(output.data.get('text/plain', '')))
                elif output.output_type == 'error':
                    return '\n'.join(output.traceback)
            return '\n'.join(outputs)

        return stdout.getvalue() or "Code executed successfully with no output."

    except CellExecutionError as e:
        return f"Execution error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        sys.stdout, sys.stderr = original_stdout, original_stderr


# === Command resolver (Linux only) ===
def _cmd(lang: str) -> str:
    """
    Return the interpreter command for a given language on Linux.
    """
    if lang in PYTHON_VARIANTS or lang.startswith("python"):
        return "python3"
    if lang in ["bash", "sh", "shell"]:
        return "bash"
    if lang == "javascript":
        return "node"

    raise NotImplementedError(f"{lang} not recognized in code execution")


# === Code execution wrapper ===
def execute_code(
    code: Optional[str] = None,
    filename: Optional[str] = None,
    work_dir: Optional[str] = None,
    lang: Optional[str] = "python",
) -> str:
    """
    Execute code locally in a subprocess (Linux only).

    Args:
        code (Optional[str]): Code to execute.
        filename (Optional[str]): File to execute (if code not provided).
        work_dir (Optional[str]): Working directory.
        lang (Optional[str]): Programming language ("python", "bash", etc.)

    Returns:
        str: Output or error message.
    """
    if all((code is None, filename is None)):
        return "Either `code` or `filename` must be provided."

    original_filename = filename
    if filename is None:
        code_hash = md5(code.encode()).hexdigest()
        ext = "py" if lang.startswith("python") else lang
        filename = f"tmp_code_{code_hash}.{ext}"

    if work_dir is None:
        work_dir = WORKING_DIR

    filepath = os.path.join(work_dir, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    if code is not None:
        with open(filepath, "w", encoding="utf-8") as fout:
            fout.write(code)

    cmd = [
        sys.executable if lang.startswith("python") else _cmd(lang),
        filename,
    ]

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            subprocess.run, cmd, cwd=work_dir, capture_output=True, text=True, timeout=DEFAULT_TIMEOUT
        )
        try:
            result = future.result(timeout=DEFAULT_TIMEOUT)
        except (subprocess.TimeoutExpired, TimeoutError):
            if original_filename is None and os.path.exists(filepath):
                os.remove(filepath)
            return TIMEOUT_MSG

    if original_filename is None and os.path.exists(filepath):
        os.remove(filepath)

    if result.returncode:
        logs = result.stderr
        abs_path = str(pathlib.Path(work_dir).absolute()) + PATH_SEPARATOR
        logs = logs.replace(abs_path, "")
    else:
        logs = result.stdout

    return logs

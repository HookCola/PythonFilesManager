"""
Python 文件管理系统 - 详细注释版

说明：
1. 本文件由原始源码 `pythonfinal.py` 复制而来，主要用于课程报告、答辩或代码讲解。
2. 原始源码保持不变；本文件在不改变程序逻辑的前提下，补充了模块说明、函数说明和关键步骤注释。
3. 程序采用命令行菜单交互方式，实现文件/目录创建、删除、重命名、复制、移动、遍历、搜索、统计和回收站管理。

整体设计思路：
- 使用 `main()` 作为主菜单调度中心。
- 使用 `safe_input()` 统一处理用户输入和导航命令。
- 使用 `BACK` 和 `MAIN_MENU` 两个哨兵对象表示“返回上一步”和“返回主菜单”。
- 使用 `current_dir` 保存当前工作目录，所有相对路径都基于它解析。
- 使用 `.recycle_bin` 文件夹和 `recycle_meta.json` 元数据文件实现回收站机制。
"""

# os：处理路径、目录、文件属性、目录遍历等底层文件系统操作。
import os

# shutil：处理复制、移动、递归删除等高级文件操作。
import shutil

# json：保存和读取回收站元数据，实现数据持久化。
import json

# datetime：生成删除时间戳，以及把文件时间戳格式化为可读时间。
import datetime

# glob：用于文件名通配符匹配，例如 *.txt、*.py。
import glob

# pathlib：当前版本中导入但未实际使用，主要保留为后续扩展面向对象路径操作的可能。
from pathlib import Path

# ==================== 导航控制 ====================

# BACK 和 MAIN_MENU 是两个“哨兵对象”。
# 使用 object() 而不是字符串，是为了避免和用户真实输入内容冲突。
# 例如用户可能真的想输入文件名 "b" 或 "0"，哨兵对象可以和普通字符串明确区分。
BACK = object()
MAIN_MENU = object()


def safe_input(prompt):
    """
    带导航功能的统一输入函数。

    参数：
        prompt：传入的输入提示文本。

    返回值：
        普通字符串：用户正常输入的内容。
        MAIN_MENU：用户输入 0，表示直接返回主菜单。
        BACK：用户输入 b，表示返回上一步。

    实现原理：
        本函数封装了 input()，让所有功能的输入界面都拥有统一导航规则。
        如果每个函数都单独写 input()，后期修改导航规则会非常麻烦；
        统一封装后，只需要维护 safe_input() 一个函数。

    特殊设计：
        输入 \\0 返回普通字符串 "0"；
        输入 \\b 返回普通字符串 "b"。
        这样可以解决导航快捷键与真实输入内容冲突的问题。
    """
    # 在原提示后统一追加导航说明，让用户知道 0 和 b 的含义。
    user_input = input(f"{prompt} (0:主菜单, b:上一步): ").strip()

    # 输入 0 表示跨层返回主菜单。
    if user_input == "0":
        return MAIN_MENU

    # 输入 b 或 B 表示返回上一步。
    if user_input.lower() == "b":
        return BACK

    # 如果用户确实想输入字面值 0，可以输入 \0。
    if user_input == "\\0":
        return "0"

    # 如果用户确实想输入字面值 b，可以输入 \b。
    if user_input == "\\b":
        return "b"

    # 其他内容按普通输入返回。
    return user_input


# 全局变量：当前工作目录
# current_dir 是所有相对路径的基准目录。
# 用户在菜单中切换工作目录后，该变量会被 main() 更新。
current_dir = os.getcwd()

# 回收站根目录
# 回收站放在用户主目录下，避免跟随当前工作目录变化。
RECYCLE_BIN = os.path.join(os.path.expanduser("~"), ".recycle_bin")

# 元数据文件用于记录：原始路径、删除时间、回收站中的文件名。
RECYCLE_META = os.path.join(RECYCLE_BIN, "recycle_meta.json")


def ensure_recycle_bin():
    """
    确保回收站目录和元数据文件存在。

    功能：
        第一次使用回收站时，如果 `.recycle_bin` 文件夹不存在，就自动创建；
        如果 `recycle_meta.json` 不存在，就初始化为空 JSON 数组。

    为什么需要这个函数：
        删除、查看、还原、清空回收站都依赖回收站目录和元数据文件。
        统一放在该函数中检查，可以避免多个函数重复写初始化代码。
    """
    # 如果回收站目录不存在，则创建目录。
    if not os.path.exists(RECYCLE_BIN):
        os.makedirs(RECYCLE_BIN)

    # 如果元数据文件不存在，则写入空列表，表示当前回收站没有记录。
    if not os.path.exists(RECYCLE_META):
        with open(RECYCLE_META, "w", encoding="utf-8") as f:
            json.dump([], f)


def load_recycle_meta():
    """
    读取回收站元数据。

    返回值：
        list：每个元素是一个字典，格式大致为：
        {
            "original_path": "原始路径",
            "deleted_at": "删除时间",
            "bin_name": "回收站中的名称"
        }

    实现原理：
        先调用 ensure_recycle_bin() 保证文件存在，再使用 json.load() 读取。
    """
    ensure_recycle_bin()
    with open(RECYCLE_META, "r", encoding="utf-8") as f:
        return json.load(f)


def save_recycle_meta(meta):
    """
    保存回收站元数据。

    参数：
        meta：回收站记录列表。

    实现原理：
        使用 json.dump() 将 Python 列表写入 JSON 文件。
        ensure_ascii=False 用于正确保存中文路径；
        indent=2 用于让 JSON 文件更易读。
    """
    ensure_recycle_bin()
    with open(RECYCLE_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def get_timestamp():
    """
    生成当前时间戳字符串。

    返回值：
        格式为 YYYYMMDD_HHMMSS 的字符串，例如 20260615_143025。

    用途：
        删除文件或目录时，将时间戳拼接到回收站文件名中，
        避免多次删除同名文件时互相覆盖。
    """
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def input_multiline(prompt):
    """
    多行文本输入函数。

    参数：
        prompt：输入前显示的提示文本。

    返回值：
        str：多行内容拼接后的字符串。
        MAIN_MENU：输入 --menu 时返回主菜单。
        BACK：输入 --back 时返回上一步。

    设计原因：
        创建文件时，文件内容可能有多行，普通 input() 只能读一行。
        因此使用循环读取多行，直到用户输入空行结束。
    """
    print(prompt)
    print("(输入内容，空行结束；输入 --menu 返回主菜单；输入 --back 返回上一步)")
    lines = []
    while True:
        line = input()

        # 多行输入中的导航命令单独使用 --menu 和 --back，
        # 避免和用户正文里的 0 或 b 产生冲突。
        if line == "--menu":
            return MAIN_MENU
        if line == "--back":
            return BACK

        # 空行表示多行输入结束。
        if line == "":
            break

        # 将每一行暂存到列表中。
        lines.append(line)

    # 使用换行符重新拼接，保留用户输入的多行格式。
    return "\n".join(lines)


# ==================== 1. 创建文件 ====================
def create_file():
    """
    创建文件功能。

    功能目标：
        在当前工作目录或用户指定的绝对路径下创建一个文本文件。

    主要流程：
        1. 输入文件名或路径。
        2. 判断输入是否为空。
        3. 判断路径是相对路径还是绝对路径。
        4. 检查文件是否已经存在，避免覆盖原文件。
        5. 调用 input_multiline() 获取多行内容。
        6. 创建父目录并写入文件内容。

    涉及知识点：
        os.path.isabs()、os.path.join()、os.path.exists()、
        os.makedirs()、open()、异常处理。
    """
    while True:
        # 使用 safe_input()，所以该输入界面支持 0 返回主菜单、b 返回上一步。
        name = safe_input("请输入文件名: ")

        # 在创建文件的第一步输入 b，与返回主菜单效果一致，直接退出当前功能。
        if name == MAIN_MENU or name == BACK:
            return

        # 文件名为空没有意义，因此要求用户重新输入。
        if not name:
            print("文件名不能为空！")
            continue

        # 如果用户输入相对路径，则基于 current_dir 拼接；如果是绝对路径，则直接使用。
        path = os.path.join(current_dir, name) if not os.path.isabs(name) else name

        # 创建文件前检查是否已存在，避免覆盖用户已有文件。
        if os.path.exists(path):
            print(f"错误：文件已存在 -> {path}")
            continue

        # 获取多行文件内容。输入空行结束，输入 --back 可回到文件名输入。
        content = input_multiline("请输入文件内容（输入空行结束）: ")
        if content == MAIN_MENU:
            return
        if content == BACK:
            continue

        try:
            # 如果用户输入 docs/test.txt，父目录 docs 可能不存在；
            # 这里先创建父目录，exist_ok=True 表示目录已存在也不报错。
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

            # 使用 UTF-8 编码写入，保证中文内容正常保存。
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"文件创建成功: {path}")
        except Exception as e:
            # 捕获所有文件创建相关异常，例如权限不足、路径非法等。
            print(f"创建文件失败: {e}")
        return


# ==================== 2. 删除文件（移至回收站） ====================
def delete_file():
    """
    删除文件功能。

    功能目标：
        删除文件时不直接永久删除，而是移动到回收站，实现“软删除”。

    主要流程：
        1. 输入要删除的文件路径。
        2. 检查路径是否存在。
        3. 如果目标是目录，则提示用户使用删除目录功能。
        4. 确保回收站存在。
        5. 生成带时间戳的回收站文件名。
        6. 使用 shutil.move() 将文件移动到回收站。
        7. 将原始路径、删除时间、回收站文件名写入 JSON 元数据。

    设计意义：
        避免误删导致文件无法恢复。
    """
    while True:
        name = safe_input("请输入要删除的文件名: ")
        if name == MAIN_MENU or name == BACK:
            return

        # 将相对路径解析到当前工作目录下。
        path = os.path.join(current_dir, name) if not os.path.isabs(name) else name

        # 删除前必须确认目标存在。
        if not os.path.exists(path):
            print(f"错误：文件不存在 -> {path}")
            continue

        # 本函数只处理文件。如果输入的是目录，避免误操作，提示使用目录删除功能。
        if os.path.isdir(path):
            print("提示：目标是目录，请使用「删除目录」功能。")
            return
        try:
            ensure_recycle_bin()

            # 时间戳用于避免回收站中的同名文件互相覆盖。
            ts = get_timestamp()
            base = os.path.basename(path)
            name_part, ext = os.path.splitext(base)
            bin_name = f"{name_part}_{ts}{ext}"
            bin_path = os.path.join(RECYCLE_BIN, bin_name)

            # 将文件移动到回收站目录，这一步相当于软删除。
            shutil.move(path, bin_path)

            # 更新 JSON 元数据，记录还原时需要用到的信息。
            meta = load_recycle_meta()
            meta.append({
                "original_path": os.path.abspath(path),
                "deleted_at": ts,
                "bin_name": bin_name
            })
            save_recycle_meta(meta)
            print(f"已移至回收站: {path}")
        except Exception as e:
            # 可能失败的原因包括权限不足、文件被占用、磁盘路径异常等。
            print(f"删除失败: {e}")
        return


# ==================== 3. 重命名 ====================
def rename_file():
    """
    重命名文件或目录。

    功能目标：
        将指定文件或目录改为新名称。

    主要流程：
        1. 输入源路径。
        2. 判断源路径是否存在。
        3. 输入新文件名。
        4. 构造目标路径。
        5. 检查目标路径是否已存在。
        6. 调用 os.rename() 完成重命名。

    说明：
        新文件名只表示名称，不包含新的父目录；
        因此目标路径由“源文件所在目录 + 新文件名”组成。
    """
    while True:
        src = safe_input("请输入源文件路径: ")
        if src == MAIN_MENU:
            return
        if src == BACK:
            return

        # 源路径同样支持相对路径和绝对路径。
        src_path = os.path.join(current_dir, src) if not os.path.isabs(src) else src
        if not os.path.exists(src_path):
            print(f"错误：文件不存在 -> {src_path}")
            continue

        new_name = safe_input("请输入新文件名: ")
        if new_name == MAIN_MENU:
            return
        if new_name == BACK:
            continue
        if not new_name:
            print("新文件名不能为空！")
            continue

        # 重命名只改变名称，不改变所在目录。
        dst_path = os.path.join(os.path.dirname(src_path), new_name)

        # 避免新名称覆盖已有文件。
        if os.path.exists(dst_path):
            print(f"错误：目标文件已存在 -> {dst_path}")
            continue
        try:
            os.rename(src_path, dst_path)
            print(f"重命名成功: {src_path} -> {dst_path}")
        except Exception as e:
            print(f"重命名失败: {e}")
        return


# ==================== 4. 复制/移动 ====================
def copy_move_file():
    """
    复制或移动文件/目录。

    功能目标：
        让用户选择“复制”或“移动”，并输入源路径和目标路径。

    状态机设计：
        step = 1：选择复制或移动。
        step = 2：输入源路径。
        step = 3：输入目标路径。

    为什么使用 step：
        复制/移动是多步骤操作，用户可能在第三步想返回第二步。
        使用 step 变量可以清楚记录当前流程状态，实现“返回上一步”。

    涉及知识点：
        shutil.copy2()、shutil.copytree()、shutil.move()、os.makedirs()。
    """
    # step 表示当前处于第几步。
    step = 1

    # mode 保存用户选择：1 表示复制，2 表示移动。
    mode = None

    # src_path 用于在步骤 2 保存源路径，步骤 3 执行复制/移动时继续使用。
    src_path = None

    while True:
        if step == 1:
            print("  1. 复制")
            print("  2. 移动")
            choice = safe_input("请选择 (1/2): ")
            if choice == MAIN_MENU:
                return
            if choice == BACK:
                return
            if choice not in ("1", "2"):
                print("无效选择！")
                continue
            mode = choice

            # 选择完操作类型后进入源路径输入步骤。
            step = 2

        elif step == 2:
            src = safe_input("请输入源文件路径: ")
            if src == MAIN_MENU:
                return
            if src == BACK:
                # 返回上一步：重新选择复制或移动。
                step = 1
                continue
            src_path = os.path.join(current_dir, src) if not os.path.isabs(src) else src
            if not os.path.exists(src_path):
                print(f"错误：源文件不存在 -> {src_path}")
                continue

            # 源路径合法后进入目标路径输入步骤。
            step = 3

        elif step == 3:
            dst = safe_input("请输入目标路径: ")
            if dst == MAIN_MENU:
                return
            if dst == BACK:
                # 返回上一步：重新输入源路径。
                step = 2
                continue
            if not dst:
                print("目标路径不能为空！")
                continue
            dst_path = os.path.join(current_dir, dst) if not os.path.isabs(dst) else dst

            try:
                if mode == "1":
                    # 复制目录需要使用 copytree()，它会复制整个目录树。
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dst_path)
                    else:
                        # 复制文件前先创建目标父目录。
                        os.makedirs(os.path.dirname(dst_path) or ".", exist_ok=True)
                        # copy2() 相比 copy() 会尽量保留文件元数据。
                        shutil.copy2(src_path, dst_path)
                    print(f"复制成功: {src_path} -> {dst_path}")
                else:
                    # 移动文件或目录时，也先确保目标父目录存在。
                    os.makedirs(os.path.dirname(dst_path) or ".", exist_ok=True)
                    shutil.move(src_path, dst_path)
                    print(f"移动成功: {src_path} -> {dst_path}")
            except Exception as e:
                # 复制/移动可能因为权限、目标已存在、路径非法等原因失败。
                print(f"操作失败: {e}")
            return


# ==================== 5. 创建目录 ====================
def create_directory():
    """
    创建目录功能。

    功能目标：
        根据用户输入创建一个目录，支持多级目录。

    实现原理：
        使用 os.makedirs(path, exist_ok=True)。
        makedirs 可以递归创建多级目录；
        exist_ok=True 表示目录已存在时不抛出异常。
    """
    while True:
        name = safe_input("请输入目录名: ")
        if name == MAIN_MENU or name == BACK:
            return
        if not name:
            print("目录名不能为空！")
            continue
        path = os.path.join(current_dir, name) if not os.path.isabs(name) else name
        try:
            os.makedirs(path, exist_ok=True)
            print(f"目录创建成功: {path}")
        except Exception as e:
            print(f"创建目录失败: {e}")
        return


# ==================== 6. 删除目录（移至回收站） ====================
def delete_directory():
    """
    删除目录功能。

    功能目标：
        将目录移动到回收站，而不是直接永久删除。

    与 delete_file() 的区别：
        delete_file() 处理普通文件；
        delete_directory() 处理目录。

    实现原理：
        目录同样使用 shutil.move() 移入回收站。
        回收站目录名使用“原目录名_时间戳”的形式，避免同名冲突。
    """
    while True:
        name = safe_input("请输入要删除的目录路径: ")
        if name == MAIN_MENU or name == BACK:
            return
        path = os.path.join(current_dir, name) if not os.path.isabs(name) else name
        if not os.path.exists(path):
            print(f"错误：目录不存在 -> {path}")
            continue
        if not os.path.isdir(path):
            print("提示：目标是文件，请使用「删除文件」功能。")
            return
        try:
            ensure_recycle_bin()
            ts = get_timestamp()
            base = os.path.basename(path)
            bin_name = f"{base}_{ts}"
            bin_path = os.path.join(RECYCLE_BIN, bin_name)

            # 将整个目录移动到回收站。移动目录不需要逐个处理内部文件。
            shutil.move(path, bin_path)

            # 记录目录原始位置，方便还原。
            meta = load_recycle_meta()
            meta.append({
                "original_path": os.path.abspath(path),
                "deleted_at": ts,
                "bin_name": bin_name
            })
            save_recycle_meta(meta)
            print(f"目录已移至回收站: {path}")
        except Exception as e:
            print(f"删除目录失败: {e}")
        return


# ==================== 7. 遍历目录 ====================
def traverse_directory():
    """
    遍历目录并以树形结构显示。

    功能目标：
        类似系统中的 tree 命令，递归显示目录下的子目录和文件。

    实现原理：
        使用 os.walk(path) 递归遍历目录。
        os.walk() 每次返回 root、dirs、files：
            root：当前遍历到的目录路径；
            dirs：当前目录下的子目录列表；
            files：当前目录下的文件列表。

    层级计算：
        通过 root.replace(path, "").count(os.sep) 计算当前目录相对起始目录的层级，
        再根据层级生成缩进符号。
    """
    while True:
        name = safe_input("请输入要遍历的目录（回车使用当前目录）: ")
        if name == MAIN_MENU or name == BACK:
            return

        # 如果用户直接回车，则遍历当前工作目录。
        path = os.path.join(current_dir, name) if (name and not os.path.isabs(name)) else (name or current_dir)
        if not os.path.exists(path):
            print(f"错误：目录不存在 -> {path}")
            continue
        if not os.path.isdir(path):
            print(f"错误：不是目录 -> {path}")
            continue
        print(f"\n目录树: {path}")
        try:
            for root, dirs, files in os.walk(path):
                # 计算当前目录距离起始目录的层级。
                level = root.replace(path, "").count(os.sep)

                # 根据层级生成缩进，让输出更像树形结构。
                indent = "│   " * level + "├── " if level > 0 else ""
                print(f"{indent}{os.path.basename(root)}/")

                # 输出当前目录下的文件。
                for f in files:
                    file_indent = "│   " * (level + 1) + "├── "
                    print(f"{file_indent}{f}")
        except KeyboardInterrupt:
            # 如果目录特别大，允许用户 Ctrl+C 中断遍历。
            print("\n遍历被用户中断。")
        print()
        return


# ==================== 8. 文件搜索 ====================
def file_search():
    """
    文件搜索功能。

    功能目标：
        支持两种搜索方式：
        1. 按文件名搜索：支持 *.txt、*.py 等通配符模式。
        2. 按文件内容搜索：逐行查找包含关键词的文本文件。

    状态机流程：
        step = 1：选择搜索类型。
        step = 2：输入搜索起始目录。
        step = 3：输入文件名模式或内容关键词。

    涉及知识点：
        os.walk() 递归遍历；
        glob.fnmatch.fnmatch() 通配符匹配；
        open() 读取文件；
        enumerate() 生成行号；
        try-except 跳过无法读取的文件。
    """
    step = 1
    search_type = None
    search_dir = None

    while True:
        if step == 1:
            print("  1. 按文件名搜索（支持通配符，如 *.txt）")
            print("  2. 按文件内容搜索")
            choice = safe_input("请选择 (1/2): ")
            if choice == MAIN_MENU:
                return
            if choice == BACK:
                return
            if choice not in ("1", "2"):
                print("无效选择！")
                continue
            search_type = choice
            step = 2

        elif step == 2:
            base = safe_input("请输入搜索起始目录（回车使用当前目录）: ")
            if base == MAIN_MENU:
                return
            if base == BACK:
                step = 1
                continue

            # 回车默认从当前工作目录开始搜索。
            search_dir = os.path.join(current_dir, base) if (base and not os.path.isabs(base)) else (base or current_dir)
            if not os.path.isdir(search_dir):
                print(f"错误：目录不存在 -> {search_dir}")
                continue
            step = 3

        elif step == 3:
            if search_type == "1":
                # 按文件名搜索，例如输入 *.txt。
                pattern = safe_input("请输入文件名模式（如 *.txt）: ")
                if pattern == MAIN_MENU:
                    return
                if pattern == BACK:
                    step = 2
                    continue
                if not pattern:
                    print("搜索模式不能为空！")
                    continue
                print(f"\n搜索结果（模式: {pattern}）:")
                found = False
                try:
                    # 遍历目录下所有文件，逐个匹配文件名。
                    for root, dirs, files in os.walk(search_dir):
                        for f in files:
                            if glob.fnmatch.fnmatch(f, pattern):
                                print(f"  {os.path.join(root, f)}")
                                found = True
                except KeyboardInterrupt:
                    print("\n搜索被用户中断，显示已找到的结果。")
                if not found:
                    print("  未找到匹配的文件。")
                return
            else:
                # 按文件内容搜索，例如搜索某个关键词。
                keyword = safe_input("请输入搜索关键词: ")
                if keyword == MAIN_MENU:
                    return
                if keyword == BACK:
                    step = 2
                    continue
                if not keyword:
                    print("关键词不能为空！")
                    continue
                print(f"\n搜索结果（关键词: {keyword}）:")
                found = False
                try:
                    for root, dirs, files in os.walk(search_dir):
                        for f in files:
                            fpath = os.path.join(root, f)
                            try:
                                # errors="ignore" 可以跳过无法解码的字符，降低编码异常概率。
                                with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                                    # enumerate(fh, 1) 从第 1 行开始编号。
                                    for i, line in enumerate(fh, 1):
                                        if keyword in line:
                                            print(f"  {fpath}  第{i}行: {line.strip()[:80]}")
                                            found = True
                            except (PermissionError, OSError):
                                # 权限不足或无法打开的文件直接跳过，避免程序中断。
                                pass
                except KeyboardInterrupt:
                    print("\n搜索被用户中断，显示已找到的结果。")
                if not found:
                    print("  未找到包含关键词的文件。")
                return


# ==================== 9. 文件统计 ====================
def file_statistics():
    """
    文件/目录统计功能。

    功能目标：
        对普通文件显示大小、时间、扩展名、行数等信息；
        对目录递归统计文件数量、子目录数量和总大小。

    实现原理：
        os.stat() 获取路径元信息；
        datetime.fromtimestamp() 将系统时间戳转为可读时间；
        os.walk() 递归统计目录内部文件。
    """
    while True:
        name = safe_input("请输入文件/目录路径: ")
        if name == MAIN_MENU or name == BACK:
            return
        path = os.path.join(current_dir, name) if not os.path.isabs(name) else name
        if not os.path.exists(path):
            print(f"错误：路径不存在 -> {path}")
            continue
        try:
            # os.stat() 返回文件系统元信息，例如大小、创建时间、修改时间等。
            stat = os.stat(path)
            print(f"\n===== 文件统计 =====")
            print(f"路径:       {os.path.abspath(path)}")
            print(f"类型:       {'目录' if os.path.isdir(path) else '文件'}")
            print(f"大小:       {stat.st_size} 字节 ({stat.st_size / 1024:.2f} KB)")
            print(f"创建时间:   {datetime.datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"修改时间:   {datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"访问时间:   {datetime.datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S')}")

            if os.path.isfile(path):
                ext = os.path.splitext(path)[1] or "(无扩展名)"
                print(f"扩展名:     {ext}")

                # 只有常见文本文件才尝试统计行数，避免读取二进制文件导致异常或无意义结果。
                text_exts = {".txt", ".py", ".java", ".c", ".cpp", ".js", ".ts", ".html", ".css",
                             ".json", ".xml", ".md", ".csv", ".log", ".ini", ".cfg", ".yaml", ".yml",
                             ".sh", ".bat", ".sql", ".rb", ".go", ".rs", ".php"}
                if os.path.splitext(path)[1].lower() in text_exts:
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            line_count = sum(1 for _ in f)
                        print(f"行数:       {line_count}")
                    except Exception:
                        pass

            if os.path.isdir(path):
                # 目录统计需要递归遍历内部所有文件和子目录。
                file_count = 0
                dir_count = 0
                total_size = 0
                try:
                    for root, dirs, files in os.walk(path):
                        dir_count += len(dirs)
                        file_count += len(files)
                        for f in files:
                            try:
                                total_size += os.path.getsize(os.path.join(root, f))
                            except OSError:
                                pass
                except KeyboardInterrupt:
                    print("\n统计被用户中断，显示已统计部分数据。")
                print(f"包含文件:   {file_count} 个")
                print(f"包含子目录: {dir_count} 个")
                print(f"总大小:     {total_size} 字节 ({total_size / 1024:.2f} KB)")
            print()
        except Exception as e:
            print(f"获取统计信息失败: {e}")
        return


# ==================== 10. 回收站管理 ====================
def recycle_bin_menu():
    """
    回收站管理子菜单。

    功能目标：
        提供查看回收站、还原、清空、永久删除单项等功能。

    设计特点：
        这是主菜单下面的二级菜单。
        如果子函数返回 MAIN_MENU，说明用户希望直接回到主菜单，
        recycle_bin_menu() 会立刻 break，结束子菜单循环。
    """
    while True:
        print("\n===== 回收站管理 =====")
        print("  1. 查看回收站")
        print("  2. 还原文件/目录")
        print("  3. 清空回收站")
        print("  4. 永久删除某个文件/目录")
        print("  0. 返回主菜单")
        choice = safe_input("请选择: ")

        if choice == MAIN_MENU or choice == BACK:
            break
        elif choice == "1":
            # 只查看，不改变文件和元数据。
            list_recycle_bin()
        elif choice == "2":
            result = restore_from_recycle()
            # 深层函数返回 MAIN_MENU 时，向上穿透回主菜单。
            if result == MAIN_MENU:
                break
        elif choice == "3":
            result = empty_recycle_bin()
            if result == MAIN_MENU:
                break
        elif choice == "4":
            result = permanent_delete_from_recycle()
            if result == MAIN_MENU:
                break
        else:
            print("无效选择！")


def list_recycle_bin():
    """
    查看回收站内容。

    功能目标：
        读取 JSON 元数据，并按编号显示所有回收站项目。

    说明：
        这里显示的是元数据记录，而不是单纯扫描 .recycle_bin 目录。
        因为元数据中包含原始路径和删除时间，信息更完整。
    """
    meta = load_recycle_meta()
    if not meta:
        print("回收站为空。")
        return
    print(f"\n回收站内容 ({len(meta)} 项):")
    for i, item in enumerate(meta):
        print(f"  [{i}] {item['bin_name']}")
        print(f"      原始路径: {item['original_path']}")
        print(f"      删除时间: {item['deleted_at']}")


def restore_from_recycle():
    """
    从回收站还原文件或目录。

    功能目标：
        根据用户选择的编号，将回收站中的文件/目录恢复到原始路径。

    主要流程：
        1. 读取元数据。
        2. 显示回收站列表。
        3. 用户输入编号。
        4. 检查编号是否合法。
        5. 检查回收站中的实际文件是否存在。
        6. 检查原始路径是否已被占用。
        7. 使用 shutil.move() 移回原路径。
        8. 从元数据中删除该记录并保存。

    返回值：
        MAIN_MENU：用户输入 0，希望直接回主菜单。
        None：正常结束或返回回收站菜单。
    """
    meta = load_recycle_meta()
    if not meta:
        print("回收站为空，没有可还原的文件。")
        return None
    list_recycle_bin()

    while True:
        idx_str = safe_input("请输入要还原的编号: ")
        if idx_str == MAIN_MENU:
            return MAIN_MENU
        if idx_str == BACK:
            return None
        try:
            idx = int(idx_str)
            if idx < 0 or idx >= len(meta):
                print("无效编号！")
                continue
        except ValueError:
            print("请输入有效数字！")
            continue
        break

    # 根据编号取出对应元数据。
    item = meta[idx]

    # bin_path 是回收站中的实际路径。
    bin_path = os.path.join(RECYCLE_BIN, item["bin_name"])

    # original 是删除前的原始路径。
    original = item["original_path"]

    if not os.path.exists(bin_path):
        print(f"错误：回收站中文件不存在 -> {bin_path}")
        return None

    # 如果原始位置已经存在同名文件/目录，不能直接覆盖。
    if os.path.exists(original):
        print(f"错误：原始路径已存在文件，无法还原 -> {original}")
        return None

    try:
        # 还原前先确保原父目录存在。
        os.makedirs(os.path.dirname(original) or ".", exist_ok=True)
        shutil.move(bin_path, original)

        # 文件还原后，元数据中对应记录也要删除，保持数据一致。
        meta.pop(idx)
        save_recycle_meta(meta)
        print(f"还原成功: {original}")
    except Exception as e:
        print(f"还原失败: {e}")
    return None


def empty_recycle_bin():
    """
    清空回收站。

    功能目标：
        永久删除回收站中的所有文件和目录，并清空 JSON 元数据。

    安全设计：
        该操作不可恢复，因此要求用户输入 yes 二次确认。

    返回值：
        MAIN_MENU：用户输入 0，希望直接回主菜单。
        None：正常结束或取消操作。
    """
    meta = load_recycle_meta()
    if not meta:
        print("回收站已为空。")
        return None

    confirm = safe_input(f"确定要清空回收站吗？将永久删除 {len(meta)} 个文件/目录 (yes/no): ")
    if confirm == MAIN_MENU:
        return MAIN_MENU
    if confirm == BACK:
        return None
    if confirm.lower() != "yes":
        print("已取消。")
        return None

    try:
        # 遍历每条元数据，删除回收站中的实际文件/目录。
        for item in meta:
            bin_path = os.path.join(RECYCLE_BIN, item["bin_name"])
            if os.path.isdir(bin_path):
                # 目录永久删除使用 rmtree()。
                shutil.rmtree(bin_path)
            elif os.path.exists(bin_path):
                # 文件永久删除使用 os.remove()。
                os.remove(bin_path)

        # 实际文件删除完成后，元数据也清空。
        save_recycle_meta([])
        print("回收站已清空。")
    except Exception as e:
        print(f"清空回收站失败: {e}")
    return None


def permanent_delete_from_recycle():
    """
    永久删除回收站中的某一个项目。

    功能目标：
        与 empty_recycle_bin() 不同，本函数只删除用户选择的一项。

    状态特点：
        该函数有两个关键输入：
        1. 输入编号；
        2. 输入 yes 确认。

    导航逻辑：
        编号输入阶段输入 b：返回回收站菜单；
        确认阶段输入 b：回到编号输入阶段。
    """
    meta = load_recycle_meta()
    if not meta:
        print("回收站为空。")
        return None
    list_recycle_bin()

    while True:
        idx_str = safe_input("请输入要永久删除的编号: ")
        if idx_str == MAIN_MENU:
            return MAIN_MENU
        if idx_str == BACK:
            return None
        try:
            idx = int(idx_str)
            if idx < 0 or idx >= len(meta):
                print("无效编号！")
                continue
        except ValueError:
            print("请输入有效数字！")
            continue

        item = meta[idx]
        # 永久删除前二次确认，防止误删。
        confirm = safe_input(f"确定永久删除 '{item['bin_name']}'？此操作不可撤销 (yes/no): ")
        if confirm == MAIN_MENU:
            return MAIN_MENU
        if confirm == BACK:
            continue
        if confirm.lower() != "yes":
            print("已取消。")
            return None

        try:
            bin_path = os.path.join(RECYCLE_BIN, item["bin_name"])
            if os.path.isdir(bin_path):
                shutil.rmtree(bin_path)
            elif os.path.exists(bin_path):
                os.remove(bin_path)

            # 删除实际文件后，同步删除元数据记录。
            meta.pop(idx)
            save_recycle_meta(meta)
            print("永久删除成功。")
        except Exception as e:
            print(f"永久删除失败: {e}")
        return None


# ==================== 主菜单 ====================
def main():
    """
    程序主入口。

    功能目标：
        显示主菜单，根据用户输入分发到不同功能函数。

    主循环结构：
        while True 不断显示菜单；
        用户选择功能后调用对应函数；
        功能执行完成后返回主菜单；
        输入 0 时退出程序。

    全局变量：
        current_dir 在“切换工作目录”功能中会被修改，
        因此这里使用 global 声明。
    """
    global current_dir
    while True:
        # 每次循环都重新打印菜单，让用户清楚当前可执行的操作。
        print("\n" + "=" * 40)
        print("        文件管理系统")
        print("=" * 40)
        print(f"当前目录: {current_dir}")
        print("  1. 创建文件")
        print("  2. 删除文件（移至回收站）")
        print("  3. 重命名文件")
        print("  4. 复制/移动文件")
        print("  5. 创建目录")
        print("  6. 删除目录（移至回收站）")
        print("  7. 遍历目录")
        print("  8. 文件搜索")
        print("  9. 文件统计")
        print(" 10. 回收站管理")
        print(" 11. 切换工作目录")
        print("  0. 退出")
        print("-" * 40)
        print("提示：在任何输入界面输入 0 返回主菜单，输入 b 返回上一步，输入 \\0 或 \\b 输入字面值")
        choice = input("请选择: ").strip()

        try:
            # 主菜单使用 if/elif 分发功能。
            if choice == "1":
                create_file()
            elif choice == "2":
                delete_file()
            elif choice == "3":
                rename_file()
            elif choice == "4":
                copy_move_file()
            elif choice == "5":
                create_directory()
            elif choice == "6":
                delete_directory()
            elif choice == "7":
                traverse_directory()
            elif choice == "8":
                file_search()
            elif choice == "9":
                file_statistics()
            elif choice == "10":
                recycle_bin_menu()
            elif choice == "11":
                # 切换工作目录会修改全局 current_dir。
                new_dir = safe_input("请输入新的工作目录: ")
                if new_dir == MAIN_MENU or new_dir == BACK:
                    continue
                if os.path.isdir(new_dir):
                    current_dir = os.path.abspath(new_dir)
                    print(f"工作目录已切换到: {current_dir}")
                else:
                    print(f"错误：目录不存在 -> {new_dir}")
            elif choice == "0":
                print("再见！")
                break
            else:
                print("无效选择，请重新输入！")
        except KeyboardInterrupt:
            # 防止用户 Ctrl+C 后程序直接退出，提升交互容错性。
            print("\n操作已取消，返回主菜单。")


if __name__ == "__main__":
    main()

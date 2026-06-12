import os
import shutil
import json
import datetime
import glob
from pathlib import Path

# ==================== 导航控制 ====================
BACK = object()
MAIN_MENU = object()


def safe_input(prompt):
    """带导航提示的输入函数：输入 0 返回主菜单，输入 b 返回上一步"""
    user_input = input(f"{prompt} (0:主菜单, b:上一步): ").strip()
    if user_input == "0":
        return MAIN_MENU
    if user_input.lower() == "b":
        return BACK
    return user_input


# 全局变量：当前工作目录
current_dir = os.getcwd()

# 回收站根目录
RECYCLE_BIN = os.path.join(os.path.expanduser("~"), ".recycle_bin")
RECYCLE_META = os.path.join(RECYCLE_BIN, "recycle_meta.json")


def ensure_recycle_bin():
    if not os.path.exists(RECYCLE_BIN):
        os.makedirs(RECYCLE_BIN)
    if not os.path.exists(RECYCLE_META):
        with open(RECYCLE_META, "w", encoding="utf-8") as f:
            json.dump([], f)


def load_recycle_meta():
    ensure_recycle_bin()
    with open(RECYCLE_META, "r", encoding="utf-8") as f:
        return json.load(f)


def save_recycle_meta(meta):
    ensure_recycle_bin()
    with open(RECYCLE_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def input_multiline(prompt):
    """多行输入，空行结束；输入 --menu 返回主菜单，输入 --back 返回上一步"""
    print(prompt)
    print("(输入内容，空行结束；输入 --menu 返回主菜单；输入 --back 返回上一步)")
    lines = []
    while True:
        line = input()
        if line == "--menu":
            return MAIN_MENU
        if line == "--back":
            return BACK
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)


# ==================== 1. 创建文件 ====================
def create_file():
    while True:
        name = safe_input("请输入文件名: ")
        if name == MAIN_MENU or name == BACK:
            return
        if not name:
            print("文件名不能为空！")
            continue
        path = os.path.join(current_dir, name) if not os.path.isabs(name) else name
        if os.path.exists(path):
            print(f"错误：文件已存在 -> {path}")
            continue

        content = input_multiline("请输入文件内容（输入空行结束）: ")
        if content == MAIN_MENU:
            return
        if content == BACK:
            continue

        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"文件创建成功: {path}")
        except Exception as e:
            print(f"创建文件失败: {e}")
        return


# ==================== 2. 删除文件（移至回收站） ====================
def delete_file():
    while True:
        name = safe_input("请输入要删除的文件名: ")
        if name == MAIN_MENU or name == BACK:
            return
        path = os.path.join(current_dir, name) if not os.path.isabs(name) else name
        if not os.path.exists(path):
            print(f"错误：文件不存在 -> {path}")
            continue
        if os.path.isdir(path):
            print("提示：目标是目录，请使用「删除目录」功能。")
            return
        try:
            ensure_recycle_bin()
            ts = get_timestamp()
            base = os.path.basename(path)
            name_part, ext = os.path.splitext(base)
            bin_name = f"{name_part}_{ts}{ext}"
            bin_path = os.path.join(RECYCLE_BIN, bin_name)
            shutil.move(path, bin_path)

            meta = load_recycle_meta()
            meta.append({
                "original_path": os.path.abspath(path),
                "deleted_at": ts,
                "bin_name": bin_name
            })
            save_recycle_meta(meta)
            print(f"已移至回收站: {path}")
        except Exception as e:
            print(f"删除失败: {e}")
        return


# ==================== 3. 重命名 ====================
def rename_file():
    while True:
        src = safe_input("请输入源文件路径: ")
        if src == MAIN_MENU:
            return
        if src == BACK:
            return
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
        dst_path = os.path.join(os.path.dirname(src_path), new_name)
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
    step = 1
    mode = None
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
            step = 2

        elif step == 2:
            src = safe_input("请输入源文件路径: ")
            if src == MAIN_MENU:
                return
            if src == BACK:
                step = 1
                continue
            src_path = os.path.join(current_dir, src) if not os.path.isabs(src) else src
            if not os.path.exists(src_path):
                print(f"错误：源文件不存在 -> {src_path}")
                continue
            step = 3

        elif step == 3:
            dst = safe_input("请输入目标路径: ")
            if dst == MAIN_MENU:
                return
            if dst == BACK:
                step = 2
                continue
            if not dst:
                print("目标路径不能为空！")
                continue
            dst_path = os.path.join(current_dir, dst) if not os.path.isabs(dst) else dst

            try:
                if mode == "1":
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dst_path)
                    else:
                        os.makedirs(os.path.dirname(dst_path) or ".", exist_ok=True)
                        shutil.copy2(src_path, dst_path)
                    print(f"复制成功: {src_path} -> {dst_path}")
                else:
                    os.makedirs(os.path.dirname(dst_path) or ".", exist_ok=True)
                    shutil.move(src_path, dst_path)
                    print(f"移动成功: {src_path} -> {dst_path}")
            except Exception as e:
                print(f"操作失败: {e}")
            return


# ==================== 5. 创建目录 ====================
def create_directory():
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
            shutil.move(path, bin_path)

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
    while True:
        name = safe_input("请输入要遍历的目录（回车使用当前目录）: ")
        if name == MAIN_MENU or name == BACK:
            return
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
                level = root.replace(path, "").count(os.sep)
                indent = "│   " * level + "├── " if level > 0 else ""
                print(f"{indent}{os.path.basename(root)}/")
                for f in files:
                    file_indent = "│   " * (level + 1) + "├── "
                    print(f"{file_indent}{f}")
        except KeyboardInterrupt:
            print("\n遍历被用户中断。")
        print()
        return


# ==================== 8. 文件搜索 ====================
def file_search():
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
            search_dir = os.path.join(current_dir, base) if (base and not os.path.isabs(base)) else (base or current_dir)
            if not os.path.isdir(search_dir):
                print(f"错误：目录不存在 -> {search_dir}")
                continue
            step = 3

        elif step == 3:
            if search_type == "1":
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
                                with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                                    for i, line in enumerate(fh, 1):
                                        if keyword in line:
                                            print(f"  {fpath}  第{i}行: {line.strip()[:80]}")
                                            found = True
                            except (PermissionError, OSError):
                                pass
                except KeyboardInterrupt:
                    print("\n搜索被用户中断，显示已找到的结果。")
                if not found:
                    print("  未找到包含关键词的文件。")
                return


# ==================== 9. 文件统计 ====================
def file_statistics():
    while True:
        name = safe_input("请输入文件/目录路径: ")
        if name == MAIN_MENU or name == BACK:
            return
        path = os.path.join(current_dir, name) if not os.path.isabs(name) else name
        if not os.path.exists(path):
            print(f"错误：路径不存在 -> {path}")
            continue
        try:
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
    while True:
        print("\n===== 回收站管理 =====")
        print("  1. 查看回收站")
        print("  2. 还原文件/目录")
        print("  3. 清空回收站")
        print("  4. 永久删除某个文件/目录")
        print("  0. 返回主菜单")
        choice = safe_input("请选择: ")

        if choice == MAIN_MENU or choice == BACK or choice == "0":
            break
        elif choice == "1":
            list_recycle_bin()
        elif choice == "2":
            result = restore_from_recycle()
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

    item = meta[idx]
    bin_path = os.path.join(RECYCLE_BIN, item["bin_name"])
    original = item["original_path"]

    if not os.path.exists(bin_path):
        print(f"错误：回收站中文件不存在 -> {bin_path}")
        return None

    if os.path.exists(original):
        print(f"错误：原始路径已存在文件，无法还原 -> {original}")
        return None

    try:
        os.makedirs(os.path.dirname(original) or ".", exist_ok=True)
        shutil.move(bin_path, original)
        meta.pop(idx)
        save_recycle_meta(meta)
        print(f"还原成功: {original}")
    except Exception as e:
        print(f"还原失败: {e}")
    return None


def empty_recycle_bin():
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
        for item in meta:
            bin_path = os.path.join(RECYCLE_BIN, item["bin_name"])
            if os.path.isdir(bin_path):
                shutil.rmtree(bin_path)
            elif os.path.exists(bin_path):
                os.remove(bin_path)
        save_recycle_meta([])
        print("回收站已清空。")
    except Exception as e:
        print(f"清空回收站失败: {e}")
    return None


def permanent_delete_from_recycle():
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
            meta.pop(idx)
            save_recycle_meta(meta)
            print("永久删除成功。")
        except Exception as e:
            print(f"永久删除失败: {e}")
        return None


# ==================== 主菜单 ====================
def main():
    global current_dir
    while True:
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
        print("提示：在任何输入界面输入 0 返回主菜单，输入 b 返回上一步")
        choice = input("请选择: ").strip()

        try:
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
            print("\n操作已取消，返回主菜单。")


if __name__ == "__main__":
    main()

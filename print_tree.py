import os


def print_tree(directory, prefix=''):
    # 需要忽略的文件夹，避免干扰视线
    ignore_dirs = {'.git', '.idea', 'venv', '__pycache__', 'static', 'media', 'migrations'}

    files = []
    dirs = []

    try:
        for item in os.listdir(directory):
            if item in ignore_dirs:
                continue
            path = os.path.join(directory, item)
            if os.path.isdir(path):
                dirs.append(item)
            else:
                files.append(item)
    except PermissionError:
        return

    dirs.sort()
    files.sort()
    entries = dirs + files

    for i, entry in enumerate(entries):
        is_last = (i == len(entries) - 1)
        connector = '└── ' if is_last else '├── '
        print(prefix + connector + entry)

        path = os.path.join(directory, entry)
        if os.path.isdir(path):
            extension = '    ' if is_last else '│   '
            print_tree(path, prefix + extension)


if __name__ == '__main__':
    print(".")
    print_tree('.')
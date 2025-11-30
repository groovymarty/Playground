import os
import sys
import xxhash
from pathlib import Path

n_files = 0
n_dirs = 0
n_duplicates = 0

MY_BASE_DIR = "D:\\Users\\msaus\\Documents\\Jeff\\Mac G5"
#MY_BASE_DIR = "D:\\Users\\msaus\\Documents\\Jeff\\Mac G5\\Users\\jeffreysauser\\Desktop\\China Pictures\\Beijing"
MAX_DEPTH = None

inventory = {}
flows = {}


def hash_file(path, prefix_bytes=65536):
    size = os.path.getsize(path)
    hasher = xxhash.xxh64()
    with open(path, mode="rb") as f:
        chunk = f.read(prefix_bytes)
        hasher.update(chunk)

    return size, hasher.intdigest()


def dir_file_count(folder):
    return sum(1 for f in Path(folder).iterdir() if f.is_file())


def add_flow(file_path, dup_path):
    file_folder, file_name = os.path.split(file_path)
    dup_folder, dup_name = os.path.split(dup_path)
    src_folder, src_name, dest_folder, dest_name = (file_folder, file_name, dup_folder, dup_name) if len(file_folder) < len(dup_folder) else (dup_folder, dup_name, file_folder, file_name)
    flow_key = src_folder, dest_folder
    if not flow_key in flows:
        flows[flow_key] = {
            "src_names": [],
            "dest_names": [],
            "tot_src_files": dir_file_count(src_folder),
            "tot_dest_files": dir_file_count(dest_folder),
        }
    flows[flow_key]["src_names"].append(src_name)
    flows[flow_key]["dest_names"].append(dest_name)


def print_flows(out_file=sys.stdout, wide=False, with_names=False):
    for flow_key in sorted(flows):
        flow = flows[flow_key]
        src_folder, dest_folder = flow_key
        src_folder_trimmed = src_folder[len(MY_BASE_DIR):]
        dest_folder_trimmed = dest_folder[len(MY_BASE_DIR):]
        str1 = f"{src_folder_trimmed} {len(flow['src_names'])}/{flow['tot_src_files']} ->"
        str2 = f"{dest_folder_trimmed} {len(flow['src_names'])}/{flow['tot_dest_files']}"
        if wide:
            out_file.write(f"{str1}{str2}\n")
        else:
            out_file.write(f"{str1}\n")
            out_file.write(f"{str2}\n")
        if with_names:
            out_file.write(f"  {','.join(flow['src_names'])}\n")
            out_file.write(f"  {','.join(flow['dest_names'])}\n")


def delete_all_flows(ext_list=None, delete_dest=True, really_delete=False):
    for flow_key in sorted(flows):
        flow = flows[flow_key]
        src_folder, dest_folder = flow_key
        if not src_folder.startswith(os.path.join(MY_BASE_DIR, "Users\\jeffreysauser\\Desktop\\Photo bin")):
            continue
        names = flow["dest_names"] if delete_dest else flow["src_names"]
        targ_folder = dest_folder if delete_dest else src_folder
        for name in names:
            root, ext = os.path.splitext(name)
            if ext_list is None or ext in ext_list:
                targ_path = os.path.join(targ_folder, name)
                print(f"deleting {targ_path}")
                if really_delete and os.path.exists(targ_path):
                    os.remove(targ_path)
            

def handle_file(file_path):
    global n_duplicates
    h = hash_file(file_path)
    if h in inventory:
        print("found duplicate:")
        print(file_path)
        print(inventory[h])
        n_duplicates += 1
        add_flow(file_path, inventory[h])
    else:
        inventory[h] = file_path


def scan_dir(dir_path, cur_depth=0, recursive=True, remove_empty_dirs=True):
    global n_files, n_dirs
    print(f"scanning {dir_path}")
    items = os.listdir(dir_path)
    if len(items) == 0 and remove_empty_dirs:
        print(f"deleting empty directory")
        os.rmdir(dir_path)
    else:
        for item in items:
            item_path = os.path.join(dir_path, item)
            if os.path.islink(item_path):
                print(f"deleting symlink: {item}")
                os.remove(item_path)
            elif os.path.isdir(item_path):
                #print(f"depth {cur_depth} found folder: {item}")
                n_dirs += 1
                if recursive and MAX_DEPTH is None or cur_depth < MAX_DEPTH:
                    scan_dir(item_path, cur_depth+1)
            else:
                #print(f"depth {cur_depth} found file: {item}")
                n_files += 1
                handle_file(item_path)


scan_dir(MY_BASE_DIR)

print(f"{n_files} files")
print(f"{n_dirs} folders")
print(f"{n_duplicates} duplicates")

#print("flows:")
#print_flows()

with open("flows.txt", "w") as f:
    print_flows(f, wide=True, with_names=True)

#delete_all_flows(delete_dest=True, really_delete=False)

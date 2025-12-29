import os
PROJ_DIR = "D:\\Users\\msaus\\Pictures\\C08 Projects\\C08+42 Heidi 40"
for i in range(0, 40):
    folder_name = f"C08+42+{i+1:02} {1986+i}-{(87+i) % 100:02}"
    folder_path = os.path.join(PROJ_DIR, folder_name)
    os.mkdir(folder_path)
    file_path = os.path.join(folder_path, "contents.json")
    with open(file_path, mode="w") as f:
        f.write("{}\n")

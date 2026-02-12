import os
import sys

if len(sys.argv) != 2:
    sys.exit(1)


path = sys.argv[1]
if not os.path.exists(path):
    sys.exit(1)

print(f"path: {path}")


dirList = os.listdir(path)
fileList = []
for elem in dirList:
    elemPath = os.path.join(path, elem)
    if os.path.isfile(elemPath):
        fileList.append((elem, os.stat(elemPath).st_size))

fileList.sort(key=lambda x: (x[1], x[0]))

print("files:")
for file in fileList:
    print(f"\t{file[0]}: {file[1]} bytes")
import sys
import os

# 상위 디렉토리를 Python 경로에 추가하여 모듈 import 가능하게 함
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.funFilelist import scanFilelist, getPath

# obsidian_path = "/home/noguri/문서/obsidian"

def main():
    path = getPath()
    print(path)
    
    file_list = scanFilelist(path)
    print(file_list)

if __name__ == "__main__":
    main()

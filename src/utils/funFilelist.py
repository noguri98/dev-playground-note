import os
from pathlib import Path
from collections import defaultdict
from fastapi import Request

def getPath(path: str) -> list[str]:
    """
    frontend에서 통신으로 전달 받은 path를 반환하는 함수
    """
    # fastapi로 path 받기
    path = request.path
    return path

# frontend에서 전달 받은 path에 접근하여 file-list 가져오는 함수
def scanFilelist(path: str) -> list[str]:
    """
    주어진 경로의 파일들을 디렉토리별로 그룹화하여 반환하는 함수
    (점(.)으로 시작하는 디렉토리는 제외, 같은 레벨의 디렉토리들도 그룹화)
    
    Args:
        path (str): 탐색할 경로
        
    Returns:
        list[str]: 그룹화된 파일 정보 리스트
    """
    grouped_files = []
    
    try:
        if not os.path.exists(path):
            print(f"경로가 존재하지 않습니다: {path}")
            return grouped_files
            
        root_path = Path(path)
        
        def process_directory(directory: Path, current_path: str = "") -> str:
            """디렉토리를 재귀적으로 처리하여 그룹화된 문자열 반환"""
            items = [item for item in directory.iterdir() 
                    if not item.name.startswith('.')]
            
            dirs = [item for item in items if item.is_dir()]
            files = [item for item in items if item.is_file()]
            
            result_parts = []
            
            # 파일들을 그룹화
            if files:
                file_names = sorted([f.name for f in files])
                if len(file_names) == 1:
                    result_parts.append(file_names[0])
                else:
                    result_parts.append(f"[{', '.join(file_names)}]")
            
            # 디렉토리들을 처리
            if dirs:
                if len(dirs) == 1:
                    # 단일 디렉토리
                    dir_name = dirs[0].name
                    sub_result = process_directory(dirs[0], f"{current_path}/{dir_name}" if current_path else dir_name)
                    result_parts.append(f"{dir_name}: {sub_result}")
                else:
                    # 여러 디렉토리 - 그룹화
                    dir_results = []
                    for dir_item in sorted(dirs, key=lambda x: x.name):
                        dir_name = dir_item.name
                        sub_result = process_directory(dir_item, f"{current_path}/{dir_name}" if current_path else dir_name)
                        dir_results.append(f"{dir_name}: {sub_result}")
                    result_parts.append(f"[{', '.join(dir_results)}]")
            
            return ", ".join(result_parts) if result_parts else ""
        
        # 루트 디렉토리 처리
        result = process_directory(root_path)
        if result:
            grouped_files.append(result)
        
    except Exception as e:
        print(f"그룹화된 파일 리스트를 가져오는 중 오류 발생: {e}")
        
    return grouped_files
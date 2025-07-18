import os
import json
from pathlib import Path
from fastapi import Request

import os

async def getPath(request: Request) -> str:
    """
    frontend에서 통신으로 전달 받은 JSON의 note_path를 반환하는 함수
    환경변수에서 NOTE_PATH를 우선적으로 사용
    """
    # 환경변수에서 NOTE_PATH 확인
    env_path = os.getenv("NOTE_PATH")
    if env_path:
        return env_path
    
    try:
        # JSON body에서 note_path를 가져오기
        body = await request.json()
        path = body.get("note_path", "/Users/nogyumin/obsidian")
        return path
    except Exception as e:
        print(f"JSON 파싱 오류: {e}")
        # 기본값 반환
        return "/Users/nogyumin/obsidian"

def get_manual_sorting_data(vault_path: str) -> dict:
    """
    Manual Sorting 플러그인의 정렬 데이터 가져오기
    
    Args:
        vault_path (str): Obsidian 볼트 경로
        
    Returns:
        dict: Manual Sorting 데이터
    """
    try:
        manual_sorting_path = os.path.join(vault_path, '.obsidian', 'plugins', 'manual-sorting', 'data.json')
        
        if os.path.exists(manual_sorting_path):
            with open(manual_sorting_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
    except Exception as e:
        print(f"Manual Sorting 데이터 읽기 오류: {e}")
    
    return {}

def get_obsidian_sort_order(vault_path: str) -> tuple[str, dict]:
    """
    Obsidian 설정에서 정렬 순서 가져오기
    
    Args:
        vault_path (str): Obsidian 볼트 경로
        
    Returns:
        tuple: (정렬 타입, Manual Sorting 데이터)
    """
    # Manual Sorting 플러그인 데이터 확인
    manual_data = get_manual_sorting_data(vault_path)
    if manual_data:
        return 'manual', manual_data
    
    try:
        # .obsidian/app.json 파일 확인
        config_path = os.path.join(vault_path, '.obsidian', 'app.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # fileSortOrder 또는 fileExplorer.sortOrder 확인
            sort_order = config.get('fileSortOrder') or config.get('fileExplorer', {}).get('sortOrder')
            if sort_order:
                return sort_order, {}
        
        # workspace.json 파일 확인
        workspace_path = os.path.join(vault_path, '.obsidian', 'workspace.json')
        if os.path.exists(workspace_path):
            with open(workspace_path, 'r', encoding='utf-8') as f:
                workspace = json.load(f)
            
            # 파일 탐색기 설정 확인
            for leaf in workspace.get('leaves', []):
                if leaf.get('type') == 'file-explorer':
                    sort_order = leaf.get('state', {}).get('sortOrder')
                    if sort_order:
                        return sort_order, {}
        
    except Exception as e:
        print(f"Obsidian 설정 읽기 오류: {e}")
    
    # 기본값: 자연 순서 (파일 시스템 순서)
    return 'natural', {}

def sort_items_by_manual_order(items: list, manual_data: dict, current_path: str = "") -> list:
    """
    Manual Sorting 플러그인의 순서에 따라 아이템들을 정렬
    
    Args:
        items (list): 정렬할 아이템 리스트
        manual_data (dict): Manual Sorting 데이터
        current_path (str): 현재 경로
        
    Returns:
        list: 정렬된 아이템 리스트
    """
    try:
        # customFileOrder에서 현재 경로의 정렬 정보 찾기
        custom_order = manual_data.get('customFileOrder', {})
        
        # 현재 경로에 해당하는 정렬 순서 가져오기
        # 루트 경로는 "/"로, 하위 경로는 그대로 사용
        path_key = "/" if current_path == "" else current_path
        
        order_list = custom_order.get(path_key, [])
        
        if not order_list:
            return items
        
        # 정렬된 아이템 리스트
        sorted_items = []
        remaining_items = items.copy()
        
        # Manual Sorting 순서에 따라 아이템 정렬
        for order_item in order_list:
            # 경로에서 파일/폴더 이름만 추출
            if "/" in order_item:
                item_name = order_item.split("/")[-1]
            else:
                item_name = order_item
            
            # 해당하는 아이템 찾기
            for item in remaining_items[:]:  # 복사본으로 순회
                if item.name == item_name:
                    sorted_items.append(item)
                    remaining_items.remove(item)
                    break
        
        # 정렬 순서에 없는 나머지 아이템들 추가
        sorted_items.extend(remaining_items)
        
        return sorted_items
        
    except Exception as e:
        print(f"Manual Sorting 정렬 오류: {e}")
        return items

def sort_items_by_obsidian_order(items: list, sort_order: str, base_path: Path = None, manual_data: dict = None, current_path: str = "") -> list:
    """
    Obsidian 정렬 순서에 따라 아이템들을 정렬
    
    Args:
        items (list): 정렬할 아이템 리스트
        sort_order (str): 정렬 순서
        base_path (Path): 기준 경로 (파일 시간 정보 가져오기 위해)
        manual_data (dict): Manual Sorting 데이터
        current_path (str): 현재 경로
        
    Returns:
        list: 정렬된 아이템 리스트
    """
    if sort_order == 'manual' and manual_data:
        return sort_items_by_manual_order(items, manual_data, current_path)
    elif sort_order == 'alphabetical':
        return sorted(items, key=lambda x: x.name.lower())
    elif sort_order == 'byModifiedTime':
        if base_path:
            return sorted(items, key=lambda x: (base_path / x.name).stat().st_mtime, reverse=True)
        else:
            return sorted(items, key=lambda x: x.stat().st_mtime, reverse=True)
    elif sort_order == 'byCreatedTime':
        if base_path:
            return sorted(items, key=lambda x: (base_path / x.name).stat().st_ctime, reverse=True)
        else:
            return sorted(items, key=lambda x: x.stat().st_ctime, reverse=True)
    elif sort_order == 'byFileSize':
        if base_path:
            return sorted(items, key=lambda x: (base_path / x.name).stat().st_size, reverse=True)
        else:
            return sorted(items, key=lambda x: x.stat().st_size if x.is_file() else 0, reverse=True)
    else:  # 'natural' 또는 기타
        # 파일 시스템의 자연 순서 유지 (정렬하지 않음)
        return items

def scanFilelistUpdate(path: str) -> dict:
    """
    Obsidian의 정렬 순서를 유지하면서 파일들을 JSON 형태의 중첩된 딕셔너리로 반환하는 함수
    Manual Sorting 플러그인 지원 포함
    (점(.)으로 시작하는 디렉토리는 제외)
    
    Args:
        path (str): 탐색할 경로
        
    Returns:
        dict: 중첩된 파일 구조 딕셔너리
    """
    
    # Obsidian 정렬 순서 가져오기
    sort_order, manual_data = get_obsidian_sort_order(path)
    
    def build_file_structure(directory: Path, current_path: str = "") -> dict:
        """디렉토리를 재귀적으로 처리하여 JSON 구조 반환"""
        result = {}
        
        try:
            if not directory.exists():
                return result
                
            # 점(.)으로 시작하는 파일/디렉토리 제외
            items = [item for item in directory.iterdir() 
                    if not item.name.startswith('.')]
            
            # 디렉토리와 파일 분리
            dirs = [item for item in items if item.is_dir()]
            files = [item for item in items if item.is_file()]
            
            # Obsidian 정렬 순서에 따라 정렬
            dirs = sort_items_by_obsidian_order(dirs, sort_order, None, manual_data, current_path)
            files = sort_items_by_obsidian_order(files, sort_order, None, manual_data, current_path)
            
            # 디렉토리 처리
            for dir_item in dirs:
                dir_name = dir_item.name
                # 하위 디렉토리의 경로 계산
                sub_path = os.path.join(current_path, dir_name) if current_path else dir_name
                result[dir_name] = build_file_structure(dir_item, sub_path)
            
            # 파일 처리 - 파일들은 배열로 저장
            if files:
                file_names = [f.name for f in files]  # 이미 정렬됨
                # 파일들을 '_files' 키에 배열로 저장 (디렉토리명과 구분하기 위해)
                result['_files'] = file_names
            
        except Exception as e:
            # 디렉토리 처리 오류는 조용히 무시 (일반적인 경우)
            pass
            
        return result
    
    try:
        if not os.path.exists(path):
            return {}
            
        root_path = Path(path)
        file_structure = build_file_structure(root_path, "")
        
        return file_structure
        
    except Exception as e:
        # 심각한 오류만 로그 출력
        print(f"파일 구조를 가져오는 중 오류 발생: {e}")
        return {}

def scanFilelist(path: str) -> dict:
    """
    주어진 경로의 파일들을 JSON 형태의 중첩된 딕셔너리로 반환하는 함수
    (점(.)으로 시작하는 디렉토리는 제외)
    
    Args:
        path (str): 탐색할 경로
        
    Returns:
        dict: 중첩된 파일 구조 딕셔너리
    """
    
    def build_file_structure(directory: Path) -> dict:
        """디렉토리를 재귀적으로 처리하여 JSON 구조 반환"""
        result = {}
        
        try:
            if not directory.exists():
                return result
                
            # 점(.)으로 시작하는 파일/디렉토리 제외
            items = [item for item in directory.iterdir() 
                    if not item.name.startswith('.')]
            
            # 디렉토리와 파일 분리
            dirs = [item for item in items if item.is_dir()]
            files = [item for item in items if item.is_file()]
            
            # 디렉토리 처리
            for dir_item in sorted(dirs, key=lambda x: x.name):
                dir_name = dir_item.name
                result[dir_name] = build_file_structure(dir_item)
            
            # 파일 처리 - 파일들은 배열로 저장
            if files:
                file_names = sorted([f.name for f in files])
                # 파일들을 '_files' 키에 배열로 저장 (디렉토리명과 구분하기 위해)
                result['_files'] = file_names
            
        except Exception as e:
            # 디렉토리 처리 오류는 조용히 무시 (일반적인 경우)
            pass
            
        return result
    
    try:
        if not os.path.exists(path):
            return {}
            
        root_path = Path(path)
        file_structure = build_file_structure(root_path)
        
        return file_structure
        
    except Exception as e:
        # 심각한 오류만 로그 출력
        print(f"파일 구조를 가져오는 중 오류 발생: {e}")
        return {}

def scanFilelistFlat(path: str) -> list[str]:
    """
    기존 방식의 평면적인 파일 리스트 반환 (호환성을 위해 유지)
    """
    try:
        if not os.path.exists(path):
            return []
            
        root_path = Path(path)
        files = []
        
        for item in root_path.rglob('*'):
            if not any(part.startswith('.') for part in item.parts):
                if item.is_file():
                    relative_path = item.relative_to(root_path)
                    files.append(str(relative_path))
        
        return sorted(files)
        
    except Exception as e:
        # 심각한 오류만 로그 출력
        print(f"평면 파일 리스트를 가져오는 중 오류 발생: {e}")
        return []
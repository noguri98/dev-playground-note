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
        print(f"Using note path from environment variable: {env_path}")
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
            print(f"디렉토리 {directory} 처리 중 오류: {e}")
            
        return result
    
    try:
        if not os.path.exists(path):
            print(f"경로가 존재하지 않습니다: {path}")
            return {}
            
        root_path = Path(path)
        file_structure = build_file_structure(root_path)
        
        return file_structure
        
    except Exception as e:
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
        print(f"평면 파일 리스트를 가져오는 중 오류 발생: {e}")
        return []
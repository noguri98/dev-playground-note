import sys
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 상위 디렉토리를 Python 경로에 추가하여 모듈 import 가능하게 함
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.funFilelist import scanFilelist, scanFilelistFlat, getPath

def main():
    app = FastAPI(title="File List API", version="1.0.0")
    
    # CORS 미들웨어 추가 (프론트엔드와 백엔드 간 통신을 위해)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React 기본 포트
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {"message": "File List API Server is running"}

    @app.post("/")
    async def get_path(request: Request):
        """경로 확인용 엔드포인트"""
        path = await getPath(request)
        return {"path": path}

    @app.post("/api/filelist")
    async def get_filelist(request: Request):
        """JSON 구조의 파일 리스트를 반환하는 메인 엔드포인트"""
        try:
            # JSON body에서 note_path 가져오기
            path = await getPath(request)
            
            # 파일 구조를 JSON 형태로 스캔
            file_structure = scanFilelist(path)
            
            # 응답 반환
            response = {
                "path": path,
                "file_structure": file_structure,
                "status": "success"
            }
            
            return response
            
        except Exception as e:
            print(f"Error in get_filelist: {e}")
            return {
                "path": "",
                "file_structure": {},
                "status": "error",
                "error_message": str(e)
            }

    @app.post("/api/filelist/flat")
    async def get_filelist_flat(request: Request):
        """기존 방식의 평면적인 파일 리스트 반환 (호환성용)"""
        try:
            path = await getPath(request)
            
            file_list = scanFilelistFlat(path)
            
            response = {
                "path": path,
                "file_list": file_list,
                "status": "success"
            }
            
            return response
            
        except Exception as e:
            print(f"Error in get_filelist_flat: {e}")
            return {
                "path": "",
                "file_list": [],
                "status": "error",
                "error_message": str(e)
            }

    @app.get("/health")
    async def health_check():
        """헬스 체크 엔드포인트"""
        return {"status": "healthy", "message": "Server is running"}

    print("Starting FastAPI server...")
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    
    # 로그 레벨을 WARNING으로 설정하여 성공 요청 로그 비활성화
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False, log_level="warning")

if __name__ == "__main__":
    main()
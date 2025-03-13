from fastapi import FastAPI, HTTPException
from typing import Dict
import uvicorn
import threading
from datetime import datetime

class DepartureBoardAPI:
    def __init__(self, board_controller=None):
        self.app = FastAPI()
        self.board = board_controller
        
        @self.app.post("/station/{station_id}")
        async def change_station(station_id: str) -> Dict:
            if not self.board:
                raise HTTPException(status_code=503, detail="Board not initialized")
            try:
                await self.board.change_station(station_id)
                return {
                    "status": "success",
                    "station": station_id,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/status")
        async def get_status() -> Dict:
            if not self.board:
                raise HTTPException(status_code=503, detail="Board not initialized")
            return {
                "status": "running",
                "current_station": self.board.current_station,
                "services_count": len(self.board.Services)
            }

    def set_board(self, board_controller):
        self.board = board_controller

    def start(self):
        thread = threading.Thread(
            target=lambda: uvicorn.run(self.app, host="0.0.0.0", port=8081),
            daemon=True
        )
        thread.start()
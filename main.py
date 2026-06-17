from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from core.orchestrator import Orchestrator
from core.dashboard_api import dashboard_router
import uvicorn

app = FastAPI(title="THE-AGENTS-WORKSTATION API")

# Mount Dashboard
app.include_router(dashboard_router)

# Global Configuration
AI_MODEL = "gemini-3-flash-preview"

orchestrator = Orchestrator()


class GoalRequest(BaseModel):
    goal: str

@app.get("/")
async def root():
    return {"message": "Welcome to THE-AGENTS-WORKSTATION", "status": "online"}

@app.post("/execute")
async def execute_goal(request: GoalRequest):
    try:
        result = await orchestrator.process_goal(request.goal)
        try:
            from core.runtime_state import state_manager
            state_manager.push_event("goal_completed", {})
        except ImportError:
            pass
        # Use jsonable_encoder to safely handle datetimes and other non-serializable objects
        return jsonable_encoder(result)
    except Exception as e:
        try:
            from core.runtime_state import state_manager
            state_manager.push_event("goal_failed", {})
        except ImportError:
            pass
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/terminate")
async def terminate_mission():
    orchestrator.terminate_mission()
    try:
        from core.runtime_state import state_manager
        state_manager.push_event("goal_failed", {})
        state_manager.push_event("log", {"agent": "SYSTEM", "message": "Mission terminated by user.", "level": "warning"})
    except ImportError:
        pass
    return {"status": "terminated"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

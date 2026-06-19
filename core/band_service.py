import os
from typing import Dict, Optional, Any
from core.logger import system_logger
from core.runtime_state import state_manager

class BandCredentialLoader:
    @staticmethod
    def load_credentials(role: str) -> Optional[Dict[str, str]]:
        filename = f"{role.capitalize()}.txt"
        if not os.path.exists(filename):
            return None
            
        creds = {}
        with open(filename, 'r') as f:
            for line in f:
                if line.startswith("ID: "):
                    creds["id"] = line[4:].strip()
                elif line.startswith("API key: "):
                    creds["api_key"] = line[9:].strip()
                elif line.startswith("Handle: "):
                    creds["handle"] = line[8:].strip()
        
        if "api_key" in creds and "id" in creds:
            return creds
        return None

class BandService:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.clients: Dict[str, Any] = {}
        self.credentials: Dict[str, Dict[str, str]] = {}
        self.active_room: Optional[str] = None
        self.is_active = False
        self._initialize()
        
    def _initialize(self):
        try:
            from band.client.rest import AsyncRestClient
            
            planner_creds = BandCredentialLoader.load_credentials("planner")
            backend_creds = BandCredentialLoader.load_credentials("backend")
            supervisor_creds = BandCredentialLoader.load_credentials("supervisor")
            
            if planner_creds and backend_creds and supervisor_creds:
                self.credentials["planner"] = planner_creds
                self.credentials["backend"] = backend_creds
                self.credentials["supervisor"] = supervisor_creds
                
                self.clients["planner"] = AsyncRestClient(api_key=planner_creds["api_key"])
                self.clients["backend"] = AsyncRestClient(api_key=backend_creds["api_key"])
                self.clients["supervisor"] = AsyncRestClient(api_key=supervisor_creds["api_key"])
                
                self.is_active = True
                system_logger.info("[BAND] Successfully loaded credentials and initialized SDK.")
            else:
                system_logger.warning("[BAND] Missing credentials. Band integration disabled.")
        except ImportError:
            system_logger.warning("[BAND] band-sdk not found. Band integration disabled.")
        except Exception as e:
            system_logger.error(f"[BAND] Failed to initialize Band SDK: {str(e)}")
            self.is_active = False

    async def _ensure_room(self, goal_id: str):
        if not self.is_active or self.active_room:
            return
        
        try:
            from band.client.rest import ChatRoomRequest
            client = self.clients["planner"]
            response = await client.agent_api_chats.create_agent_chat(
                chat=ChatRoomRequest(task_id=goal_id)
            )
            
            # Extract chat ID safely
            if hasattr(response, 'id'):
                self.active_room = response.id
            elif hasattr(response, 'chat') and hasattr(response.chat, 'id'):
                self.active_room = response.chat.id
            elif isinstance(response, dict):
                self.active_room = response.get('id') or response.get('chat', {}).get('id')
            
            state_manager.push_event("band_status", {
                "active_room": self.active_room,
                "connected_agents": list(self.clients.keys())
            })
            system_logger.info(f"[BAND] Created Band room: {self.active_room}")
        except Exception as e:
            system_logger.error(f"[BAND] Failed to create Band room: {str(e)}")

    async def _send_message(self, agent_role: str, text: str, mentions: list = None):
        if not self.is_active or not self.active_room: return
        try:
            from band.client.rest import ChatMessageRequest
            client = self.clients[agent_role]
            
            req = ChatMessageRequest(content=text, mentions=mentions or [])
            await client.agent_api_messages.create_agent_chat_message(
                chat_id=self.active_room,
                message=req
            )
            state_manager.push_event("band_message", {"agent": agent_role, "message": text})
            system_logger.info(f"[BAND] {agent_role} sent message to room {self.active_room}")
        except Exception as e:
            system_logger.error(f"[BAND] {agent_role} publish failed: {str(e)}")
            
    async def publish_planner_summary(self, goal_state: Any):
        if not self.is_active: return
        await self._ensure_room(goal_state.goal_id)
        
        mentions = []
        try:
            from band.client.rest import ChatMessageRequestMentionsItem
            backend_creds = self.credentials["backend"]
            mentions = [ChatMessageRequestMentionsItem(id=backend_creds["id"], handle=backend_creds["handle"])]
        except Exception:
            pass
            
        backend_handle = self.credentials.get("backend", {}).get("handle", "@backend")
        msg = f"Task planning complete. {len(goal_state.tasks)} tasks identified. {backend_handle}, please proceed with backend generation."
        await self._send_message("planner", msg, mentions)

    async def publish_backend_start(self, task_desc: str):
        if not self.is_active: return
        msg = f"Received work assignment: {task_desc}. Initiating generation flow..."
        await self._send_message("backend", msg)

    async def publish_backend_complete(self, target_path: str):
        if not self.is_active: return
        
        mentions = []
        try:
            from band.client.rest import ChatMessageRequestMentionsItem
            sup_creds = self.credentials["supervisor"]
            mentions = [ChatMessageRequestMentionsItem(id=sup_creds["id"], handle=sup_creds["handle"])]
        except Exception:
            pass
            
        sup_handle = self.credentials.get("supervisor", {}).get("handle", "@supervisor")
        msg = f"Completed backend generation for {target_path}. Handing off to {sup_handle} for validation."
        await self._send_message("backend", msg, mentions)

    async def publish_supervisor_update(self, status: str, details: str):
        if not self.is_active: return
        msg = f"Supervisor Update: {status}. Details: {details}"
        await self._send_message("supervisor", msg)

band_service = BandService.get_instance()

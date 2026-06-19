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
                
                self.clients["planner"] = AsyncRestClient(api_key=planner_creds["api_key"], base_url="https://app.band.ai")
                self.clients["backend"] = AsyncRestClient(api_key=backend_creds["api_key"], base_url="https://app.band.ai")
                self.clients["supervisor"] = AsyncRestClient(api_key=supervisor_creds["api_key"], base_url="https://app.band.ai")
                
                self.is_active = True
                system_logger.info("[BAND] Successfully loaded credentials and initialized SDK.")
            else:
                system_logger.warning("[BAND] Missing credentials. Band integration disabled.")
        except ImportError:
            system_logger.warning("[BAND] band-sdk not found. Band integration disabled.")
        except Exception as e:
            system_logger.error(f"[BAND] Failed to initialize Band SDK: {str(e)}")
            self.is_active = False

    def _build_mention(self, role: str):
        """Build a mention object for the given agent role."""
        from band.client.rest import ChatMessageRequestMentionsItem
        creds = self.credentials.get(role)
        if not creds:
            return None
        return ChatMessageRequestMentionsItem(
            id=creds["id"],
            handle=creds.get("handle")
        )

    def _build_all_other_mentions(self, sender_role: str):
        """Build mention list for all agents EXCEPT the sender."""
        mentions = []
        for role in self.credentials:
            if role != sender_role:
                m = self._build_mention(role)
                if m:
                    mentions.append(m)
        return mentions

    async def _ensure_room(self, goal_id: str):
        if not self.is_active or self.active_room:
            return
        
        try:
            from band.client.rest import ChatRoomRequest, ParticipantRequest
            client = self.clients["planner"]
            response = await client.agent_api_chats.create_agent_chat(
                chat=ChatRoomRequest()
            )
            
            # SDK returns CreateAgentChatResponse with response.data.id
            if hasattr(response, 'data') and hasattr(response.data, 'id'):
                self.active_room = response.data.id
            elif hasattr(response, 'id'):
                self.active_room = response.id
            elif isinstance(response, dict):
                self.active_room = response.get('data', {}).get('id') or response.get('id')
            
            if self.active_room:
                for role, creds in self.credentials.items():
                    if role == "planner": continue
                    try:
                        await client.agent_api_participants.add_agent_chat_participant(
                            chat_id=self.active_room,
                            participant=ParticipantRequest(participant_id=creds["id"])
                        )
                    except Exception as e:
                        system_logger.error(f"[BAND] Failed to add {role} to room: {str(e)}")

                state_manager.push_event("band_status", {
                    "active_room": self.active_room,
                    "connected_agents": list(self.clients.keys())
                })
                system_logger.info(f"[BAND] Created Band room: {self.active_room}")
            else:
                system_logger.error("[BAND] Room created but could not extract room ID from response.")
        except Exception as e:
            system_logger.error(f"[BAND] Failed to create Band room: {str(e)}")

    async def _send_message(self, agent_role: str, text: str, mentions: list = None):
        """Send a message to the Band room. Mentions are REQUIRED by the Band API."""
        if not self.is_active or not self.active_room:
            return
        
        if not mentions:
            # Band API requires at least one mention; fall back to mentioning all other agents
            mentions = self._build_all_other_mentions(agent_role)
        
        if not mentions:
            system_logger.warning(f"[BAND] {agent_role} cannot send message: no valid mentions available.")
            return
            
        try:
            from band.client.rest import ChatMessageRequest
            client = self.clients[agent_role]
            
            req = ChatMessageRequest(content=text, mentions=mentions)
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
        
        # Mention backend to hand off work
        mentions = []
        backend_mention = self._build_mention("backend")
        if backend_mention:
            mentions.append(backend_mention)
            
        backend_handle = self.credentials.get("backend", {}).get("handle", "@backend")
        msg = f"Task planning complete. {len(goal_state.tasks)} tasks identified. {backend_handle}, please proceed with backend generation."
        await self._send_message("planner", msg, mentions)

    async def publish_backend_start(self, task_desc: str):
        if not self.is_active: return
        # Mention planner to acknowledge receipt of work
        mentions = []
        planner_mention = self._build_mention("planner")
        if planner_mention:
            mentions.append(planner_mention)
            
        planner_handle = self.credentials.get("planner", {}).get("handle", "@planner")
        msg = f"{planner_handle} Received work assignment: {task_desc}. Initiating generation flow..."
        await self._send_message("backend", msg, mentions)

    async def publish_backend_complete(self, target_path: str):
        if not self.is_active: return
        
        # Mention supervisor to hand off for validation
        mentions = []
        sup_mention = self._build_mention("supervisor")
        if sup_mention:
            mentions.append(sup_mention)
            
        sup_handle = self.credentials.get("supervisor", {}).get("handle", "@supervisor")
        msg = f"Completed backend generation for {target_path}. Handing off to {sup_handle} for validation."
        await self._send_message("backend", msg, mentions)

    async def publish_supervisor_update(self, status: str, details: str):
        if not self.is_active: return
        # Mention planner and backend to report validation results
        mentions = []
        planner_mention = self._build_mention("planner")
        backend_mention = self._build_mention("backend")
        if planner_mention:
            mentions.append(planner_mention)
        if backend_mention:
            mentions.append(backend_mention)
            
        planner_handle = self.credentials.get("planner", {}).get("handle", "@planner")
        backend_handle = self.credentials.get("backend", {}).get("handle", "@backend")
        msg = f"{planner_handle} {backend_handle} Supervisor Update: {status}. Details: {details}"
        await self._send_message("supervisor", msg, mentions)

band_service = BandService.get_instance()

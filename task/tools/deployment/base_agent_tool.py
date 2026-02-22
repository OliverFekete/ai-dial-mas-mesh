import json
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any

from aidial_client import AsyncDial
from aidial_sdk.chat_completion import Message, Role, CustomContent, Stage, Attachment
from pydantic import StrictStr

from task.tools.base_tool import BaseTool
from task.tools.models import ToolCallParams
from task.utils.stage import StageProcessor


class BaseAgentTool(BaseTool, ABC):

    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    @property
    @abstractmethod
    def deployment_name(self) -> str:
        pass

    async def _execute(self, tool_call_params: ToolCallParams) -> str | Message:
        # 1. All the agents that will used as tools will have two parameters in request:
        #   - `prompt` (the request to agent)
        #   - `propagate_history`, boolean whether we need to propagate the history of communication with called agent
        arguments = json.loads(tool_call_params.tool_call.function.arguments)
        prompt = arguments.get("prompt")
        propagate_history = arguments.get("propagate_history", False)

        # 2. Use AsyncDial (api_version='2025-01-01-preview'), call the agent with streaming option.
        client = AsyncDial(
            base_url=self.endpoint,
            api_key=tool_call_params.api_key,
            api_version='2025-01-01-preview'
        )

        # 3. Prepare:
        content = ""
        custom_content = CustomContent(attachments=[])
        stages_map: dict[int, Stage] = {}

        # 4. Iterate through chunks and:
        #    - Stream content to the Stage (from tool_call_params) for this tool call
        #    - For custom_content: propagate state and attachments, handle stages
        messages = self._prepare_messages(tool_call_params)
        extra_headers = {"x-conversation-id": tool_call_params.conversation_id}

        chunks_stream = await client.chat.completions.create(
            messages=messages,
            deployment_name=self.deployment_name,
            stream=True,
            extra_headers=extra_headers
        )

        stage = tool_call_params.stage

        async for chunk in chunks_stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    if stage:
                        stage.append_content(delta.content)
                    content += delta.content

                if delta.custom_content:
                    # propagate state
                    if delta.custom_content.state:
                        custom_content.state = delta.custom_content.state
                    # propagate attachments
                    if delta.custom_content.attachments:
                        for attachment in delta.custom_content.attachments:
                            custom_content.attachments.append(attachment)
                            tool_call_params.choice.add_attachment(attachment)
                    # propagate stages
                    if hasattr(delta.custom_content, "stages") and delta.custom_content.stages:
                        for s in delta.custom_content.stages:
                            idx = getattr(s, "index", None)
                            if idx is not None:
                                if idx in stages_map:
                                    stages_map[idx].append_content(s.content)
                                    if getattr(s, "attachments", None):
                                        for att in s.attachments:
                                            stages_map[idx].add_attachment(att)
                                    if getattr(s, "status", None) == "completed":
                                        StageProcessor.close_stage_safely(stages_map[idx])
                                else:
                                    new_stage = tool_call_params.choice.create_stage(s.name)
                                    new_stage.open()
                                    new_stage.append_content(s.content)
                                    if getattr(s, "attachments", None):
                                        for att in s.attachments:
                                            new_stage.add_attachment(att)
                                    stages_map[idx] = new_stage
                                    if getattr(s, "status", None) == "completed":
                                        StageProcessor.close_stage_safely(new_stage)

        # 5. Ensure that stages are closed
        for s in stages_map.values():
            StageProcessor.close_stage_safely(s)

        # 6. Return Tool message
        msg = Message(
            role=Role.TOOL,
            name=StrictStr(tool_call_params.tool_call.function.name),
            tool_call_id=StrictStr(tool_call_params.tool_call.id),
            content=StrictStr(content),
            custom_content=custom_content
        )
        return msg

    def _prepare_messages(self, tool_call_params: ToolCallParams) -> list[dict[str, Any]]:
        # 1. Get: `prompt` and `propagate_history` params from tool call
        arguments = json.loads(tool_call_params.tool_call.function.arguments)
        prompt = arguments.get("prompt")
        propagate_history = arguments.get("propagate_history", False)

        # 2. Prepare empty `messages` array
        messages = []

        # 3. Collect the proper history
        if propagate_history:
            # Per-To-Per history propagation
            for msg in tool_call_params.messages:
                if msg.role == Role.ASSISTANT:
                    if msg.custom_content and msg.custom_content.state and self.name in msg.custom_content.state:
                        # Add user message before assistant
                        idx = tool_call_params.messages.index(msg)
                        if idx > 0:
                            user_msg = tool_call_params.messages[idx - 1]
                            messages.append({
                                "role": user_msg.role,
                                "content": user_msg.content
                            })
                        # Add assistant message with only the relevant state
                        assistant_msg = deepcopy(msg)
                        assistant_msg.custom_content.state = assistant_msg.custom_content.state[self.name]
                        messages.append(assistant_msg.dict(exclude_none=True))
                    else:
                        messages.append(msg.dict(exclude_none=True))
                else:
                    messages.append(msg.dict(exclude_none=True))
        # 4. Lastly, add the user message with `prompt`
        messages.append({
            "role": Role.USER,
            "content": prompt
        })
        return messages
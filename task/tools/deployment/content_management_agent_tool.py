from typing import Any

from task.tools.deployment.base_agent_tool import BaseAgentTool


class ContentManagementAgentTool(BaseAgentTool):

    @property
    def deployment_name(self) -> str:
        return "content-managemen-agent"

    @property
    def name(self) -> str:
        return "content_management_agent_tool"

    @property
    def description(self) -> str:
        return "Allows you to delegate document extraction, analysis, and content management tasks to the Content Management Agent."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The request to the Content Management Agent"
                },
                "propagate_history": {
                    "type": "boolean",
                    "description": "Whether to propagate the history of communication with the called agent"
                }
            },
            "required": ["prompt"]
        }
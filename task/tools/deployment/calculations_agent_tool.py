from typing import Any

from task.tools.deployment.base_agent_tool import BaseAgentTool


class CalculationsAgentTool(BaseAgentTool):

    @property
    def deployment_name(self) -> str:
        return "calculations-agent"

    @property
    def name(self) -> str:
        return "calculations_agent_tool"

    @property
    def description(self) -> str:
        return "Allows you to delegate calculation and math-related tasks to the Calculations Agent."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The request to the Calculations Agent"
                },
                "propagate_history": {
                    "type": "boolean",
                    "description": "Whether to propagate the history of communication with the called agent"
                }
            },
            "required": ["prompt"]
        }
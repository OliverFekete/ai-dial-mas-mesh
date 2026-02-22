from typing import Any

from task.tools.deployment.base_agent_tool import BaseAgentTool


class WebSearchAgentTool(BaseAgentTool):

    @property
    def deployment_name(self) -> str:
        return "web-search-agent"

    @property
    def name(self) -> str:
        return "web_search_agent_tool"

    @property
    def description(self) -> str:
        return "Allows you to delegate web search and research tasks to the Web Search Agent."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The request to the Web Search Agent"
                },
                "propagate_history": {
                    "type": "boolean",
                    "description": "Whether to propagate the history of communication with the called agent"
                }
            },
            "required": ["prompt"]
        }
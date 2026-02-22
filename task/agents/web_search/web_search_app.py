import os

import uvicorn
from aidial_sdk import DIALApp
from aidial_sdk.chat_completion import ChatCompletion, Request, Response

from task.agents.web_search.web_search_agent import WebSearchAgent
from task.tools.base_tool import BaseTool
from task.tools.deployment.calculations_agent_tool import CalculationsAgentTool
from task.tools.deployment.content_management_agent_tool import ContentManagementAgentTool
from task.tools.mcp.mcp_client import MCPClient
from task.tools.mcp.mcp_tool import MCPTool
from task.utils.constants import DIAL_ENDPOINT, DEPLOYMENT_NAME

_DDG_MCP_URL = os.getenv('DDG_MCP_URL', "http://localhost:8051/mcp")

class WebSearchApplication(ChatCompletion):
    def __init__(self):
        self._tools: list[BaseTool] = []
        self._agent: WebSearchAgent = None
        self._mcp_tools_loaded = False

    async def _load_mcp_tools(self):
        if not self._mcp_tools_loaded:
            mcp_client = await MCPClient.create(_DDG_MCP_URL)
            mcp_tools_models = await mcp_client.get_tools()
            mcp_tools = [MCPTool(mcp_client, tool_model) for tool_model in mcp_tools_models]
            self._tools.extend(mcp_tools)
            self._tools.append(CalculationsAgentTool(DIAL_ENDPOINT))
            self._tools.append(ContentManagementAgentTool(DIAL_ENDPOINT))
            self._mcp_tools_loaded = True

    async def chat_completion(self, request: Request, response: Response):
        if not self._mcp_tools_loaded:
            await self._load_mcp_tools()
        if self._agent is None:
            self._agent = WebSearchAgent(
                endpoint=DIAL_ENDPOINT,
                tools=self._tools
            )
        choice = response.create_choice()
        await self._agent.handle_request(
            deployment_name=DEPLOYMENT_NAME,
            choice=choice,
            request=request,
            response=response
        )
        response.add_choice(choice)

app = DIALApp(
    deployment_name="web-search-agent",
    impl=WebSearchApplication()
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5003)
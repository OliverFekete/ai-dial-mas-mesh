import os

import uvicorn
from aidial_sdk import DIALApp
from aidial_sdk.chat_completion import ChatCompletion, Request, Response

from task.agents.calculations.calculations_agent import CalculationsAgent
from task.agents.calculations.tools.simple_calculator_tool import SimpleCalculatorTool
from task.tools.base_tool import BaseTool
from task.agents.calculations.tools.py_interpreter.python_code_interpreter_tool import PythonCodeInterpreterTool
from task.tools.deployment.content_management_agent_tool import ContentManagementAgentTool
from task.tools.deployment.web_search_agent_tool import WebSearchAgentTool
from task.utils.constants import DIAL_ENDPOINT, DEPLOYMENT_NAME

class CalculationsApplication(ChatCompletion):
    def __init__(self):
        # Prepare tools
        tools: list[BaseTool] = [
            SimpleCalculatorTool(),
            # PythonCodeInterpreterTool is async factory, so we need to create it in async context
            # We'll create it in chat_completion below
            ContentManagementAgentTool(DIAL_ENDPOINT),
            WebSearchAgentTool(DIAL_ENDPOINT)
        ]
        self._tools = tools
        self._agent: CalculationsAgent = None

    async def chat_completion(self, request: Request, response: Response):
        # Prepare PythonCodeInterpreterTool (async)
        if not any(isinstance(t, PythonCodeInterpreterTool) for t in self._tools):
            py_tool = await PythonCodeInterpreterTool.create(
                mcp_url=os.getenv("MCP_URL", "http://localhost:8051/mcp"),
                tool_name="python_code_interpreter_tool",
                dial_endpoint=DIAL_ENDPOINT
            )
            self._tools.insert(1, py_tool)
        if self._agent is None:
            self._agent = CalculationsAgent(
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
    deployment_name="calculations-agent",
    impl=CalculationsApplication()
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
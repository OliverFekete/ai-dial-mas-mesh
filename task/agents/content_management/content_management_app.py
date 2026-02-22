import uvicorn
from aidial_sdk import DIALApp
from aidial_sdk.chat_completion import ChatCompletion, Request, Response

from task.agents.content_management.content_management_agent import ContentManagementAgent
from task.agents.content_management.tools.files.file_content_extraction_tool import FileContentExtractionTool
from task.agents.content_management.tools.rag.document_cache import DocumentCache
from task.agents.content_management.tools.rag.rag_tool import RagTool
from task.tools.base_tool import BaseTool
from task.tools.deployment.calculations_agent_tool import CalculationsAgentTool
from task.tools.deployment.web_search_agent_tool import WebSearchAgentTool
from task.utils.constants import DIAL_ENDPOINT, DEPLOYMENT_NAME

class ContentManagementApplication(ChatCompletion):
    def __init__(self):
        self._document_cache = DocumentCache.create()
        self._tools: list[BaseTool] = [
            FileContentExtractionTool(DIAL_ENDPOINT),
            RagTool(DIAL_ENDPOINT, DEPLOYMENT_NAME, self._document_cache),
            CalculationsAgentTool(DIAL_ENDPOINT),
            WebSearchAgentTool(DIAL_ENDPOINT)
        ]
        self._agent: ContentManagementAgent = None

    async def chat_completion(self, request: Request, response: Response):
        if self._agent is None:
            self._agent = ContentManagementAgent(
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
    deployment_name="content-managemen-agent",
    impl=ContentManagementApplication()
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002)
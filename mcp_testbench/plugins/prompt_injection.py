from mcp_testbench.engine import Plugin

class PromptInjection(Plugin):
    async def run(self, base_url):
        # Simulate prompt injection test
        vulnerable = base_url.endswith("/vulnerable")
        if vulnerable:
            return {"prompt_injection": True, "details": "Prompt injection vulnerability detected."}
        else:
            return {"prompt_injection": False, "details": "No prompt injection detected."}

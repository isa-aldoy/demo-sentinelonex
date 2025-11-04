from mcp_testbench.engine import Plugin
import random

class Fuzzer(Plugin):
    async def run(self, base_url):
        # Simulate fuzzing
        crash = random.choice([False, False, True])
        if crash:
            return {"crash": True, "details": "Crash detected during fuzzing."}
        else:
            return {"crash": False, "details": "No crash detected."}

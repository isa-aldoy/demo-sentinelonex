import sys
import importlib
from pathlib import Path

class Plugin:
    def run(self, base_url):
        raise NotImplementedError("Plugin must implement run()")

class PluginRegistry:
    def __init__(self):
        self.plugins = []
        self.discover_plugins()

    def discover_plugins(self):
        plugins_dir = Path(__file__).parent / "plugins"
        for plugin_file in plugins_dir.glob("*.py"):
            if plugin_file.name == "__init__.py":
                continue
            module_name = f"mcp_testbench.plugins.{plugin_file.stem}"
            module = importlib.import_module(module_name)
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, type) and issubclass(obj, Plugin) and obj is not Plugin:
                    self.plugins.append(obj())

class TestEngine:
    def __init__(self, base_url):
        self.base_url = base_url
        self.registry = PluginRegistry()

    async def run_all(self):
        results = {}
        for plugin in self.registry.plugins:
            try:
                result = await plugin.run(self.base_url)
                results[plugin.__class__.__name__] = result
            except Exception as e:
                results[plugin.__class__.__name__] = {"error": str(e)}
        return results

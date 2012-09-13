import exc

import os
import subprocess

TOOLS_LIST = ['loudness']

def check_tools(tools=TOOLS_LIST):
    exists = lambda tool: not subprocess.call(['which', tool], stdout=subprocess.PIPE)

    for tool in tools:
        if not exists(tool):
            raise exc.ToolMissing(tool)


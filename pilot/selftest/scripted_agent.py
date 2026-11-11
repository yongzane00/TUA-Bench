"""Self-test of the H7 stop mechanics in a real task container, with a scripted model (no model server).

The plan's engineering checks (p11: long tool cancellation, the saved deliverable when the budget runs out, the
hard stop) need a run where the timing is known in advance. Here the model is a script: each reply is a fixed
terminus JSON answer, returned after a fixed delay. Everything else is the real Harbor pipeline: Docker task
environment, tmux terminal with recording, budget meter, verifier.

Script "interrupt" (budget 20 s in pilot/selftest/selftest-interrupt.yaml):
  reply 1 after 2 s:  edit a file, start `sleep 900 &` (background), print the process tree into the pane log
                      (agent/terminus_2.pane), start `sleep 600` (foreground, waited 1 s)
  reply 2 after 60 s: still being written at the deadline, so the hard deadline cancels it
Expected metadata.budget: stop "time", cut_replies 1, stop_interrupt with sleep in the foreground before and none
after (stopped true, 1 Ctrl-C), the background sleep still listed, final_diff with 1 file changed.
Result on 2026-11-11 (django__django-11099): all as expected; work stopped at 21.7 s, cleanup 2.8 s, deliverable
final at 24.5 s (4.5 s past the 20 s budget).

    cd ~/work/TUA-Bench
    PYTHONPATH=pilot/selftest uv run --no-sync harbor run -c pilot/selftest/selftest-interrupt.yaml \
        -o <TUA-Bench on C:>/jobs/pilot/selftest-interrupt --yes
"""
import asyncio
import json

from harbor.agents.terminus_2.terminus_2 import Terminus2
from harbor.agents.terminus_2.terminus_2_harness7 import Terminus2Harness7
from harbor.llms.base import BaseLLM, LLMResponse
from harbor.models.metric.usage_info import UsageInfo


def reply(commands, done=False):
    return json.dumps({"analysis": "scripted", "plan": "scripted",
                       "commands": [{"keystrokes": k, "duration": d} for k, d in commands],
                       "task_complete": done})


SCRIPTS = {
    "interrupt": [
        (2.0, reply([("echo '# selftest' >> /testbed/README.rst\n", 0.5),
                     ("sleep 900 &\n", 0.5),
                     ("ps -eo pid,ppid,pgid,sid,tty,tpgid,stat,comm,args | cut -c1-150\n", 1.0),
                     ("sleep 600\n", 1.0)])),
        (60.0, reply([("", 1.0)])),
    ],
    # Plugin-off check: the same short conversation for stock terminus-2 and for H7 with each feedback level.
    # Commands with fixed output (no progress meters); 8 s replies so that concurrent trials overlap.
    "baseline": [
        (8.0, reply([("ls /testbed | head -3\n", 1.0), ("python -c 'print(6*7)'\n", 1.0)])),
        (8.0, reply([("echo selftest-done\n", 0.5)], done=True)),
    ],
}


class ScriptedLLM(BaseLLM):
    def __init__(self, script: str):
        super().__init__()
        self._script = list(SCRIPTS[script])

    async def call(self, prompt: str, **kwargs) -> LLMResponse:
        delay, text = self._script.pop(0) if self._script else (0.0, reply([], done=True))
        await asyncio.sleep(delay)
        return LLMResponse(content=text, model_name="scripted",
                           usage=UsageInfo(prompt_tokens=len(prompt) // 4, completion_tokens=len(text) // 4,
                                           cache_tokens=0, cost_usd=0.0))

    def get_model_context_limit(self) -> int:
        return 131072

    def get_model_output_limit(self) -> int | None:
        return 8192


class ScriptedStock(Terminus2):
    def __init__(self, *args, script: str = "baseline", **kwargs):
        super().__init__(*args, **kwargs)
        self._llm = ScriptedLLM(script)

    def version(self) -> str | None:
        return (super().version() or "") + "-scripted"


class ScriptedH7(Terminus2Harness7):
    def __init__(self, *args, script: str = "interrupt", **kwargs):
        super().__init__(*args, **kwargs)
        self._llm = ScriptedLLM(script)

    def version(self) -> str | None:
        return super().version() + "-scripted"

#!/usr/bin/env bash
# Batch 4 of subset/results/analysis-plan.md: Harbor's claude-code agent (unchanged) through the time-budget proxy,
# hidden vs full, on the 20 dev tasks, in quiet-start rounds like the other batches.
#
#   cd ~/work/TUA-Bench && bash subset/tools/run_cc_batch.sh [rounds]
#
# Starts one proxy per arm in tmux session `ccproxy` (hidden on port 8911, full on 8912; 900 s per run from its first
# model request, hard deadline, the report request in both arms, one run per conversation because the 2 concurrent
# trials of an arm share one URL), then the rounds via run_parallel.sh in tmux session `cc4`. Proxy events (one JSON
# line per model call, note sent, stop) go to ~/work/proxy-runs/cc4-<arm>.jsonl. Stop all:
#   tmux kill-session -t cc4; tmux kill-session -t ccproxy
rounds=${1:-3}
UPSTREAM=${UPSTREAM:-http://<qwen38-vllm-host-2>:8000/v1}
cd ~/work/TUA-Bench || exit 1
tmux has-session -t ccproxy 2>/dev/null && { echo "tmux session ccproxy already exists"; exit 1; }
mkdir -p ~/work/proxy-runs
proxy() {  # <arm> <port>
  echo "cd ~/work/harbor && uv run --no-project --with aiohttp --with-editable ./packages/time-budget \
python -m time_budget.proxy --upstream $UPSTREAM --budget 900 --feedback $1 --report-request --track-conversations \
--port $2 --events ~/work/proxy-runs/cc4-$1.jsonl 2>&1 | tee -a ~/work/proxy-runs/cc4-$1.log"
}
tmux new-session -d -s ccproxy -n hidden "$(proxy hidden 8911)"
tmux new-window -t ccproxy -n full "$(proxy full 8912)"
for port in 8911 8912; do
  for i in $(seq 1 30); do curl -s -m 2 -o /dev/null "http://127.0.0.1:$port/runs" && break; sleep 2; done
  curl -s -m 2 -o /dev/null "http://127.0.0.1:$port/runs" || { echo "proxy on $port did not start"; exit 1; }
done
bash subset/tools/run_parallel.sh cc4 qwen38-flash-next "$rounds" cc-dev-hidden-time900-rounds3 cc-dev-full-time900-rounds3

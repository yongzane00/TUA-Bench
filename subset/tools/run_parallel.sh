#!/usr/bin/env bash
# Run several configs of one model at the same time, one tmux window each, so the arms of an ablation
# share the same server conditions. Set n_concurrent_trials in each config so the total stays at 3-4.
#
#   cd ~/work/TUA-Bench
#   bash subset/tools/run_parallel.sh <session> <model> <config> [<config> ...]
#
# Each window runs subset/tools/run_one.sh: it waits until Docker and the model server answer, then runs the
# config once (skipped if it already has a finished run). Starts are 90 s apart so the arms do not build
# images at the same moment. Logs: ~/work/<session>-<config>.log.
# Stop one arm: Ctrl+C in its window. Stop all: tmux kill-session -t <session>.

session=$1; model=$2; shift 2
[ $# -gt 0 ] || { echo "usage: run_parallel.sh <session> <model> <config>..."; exit 1; }
cd ~/work/TUA-Bench || exit 1
for cfg in "$@"; do
  [ -f "subset/variants/$model/$cfg.yaml" ] || { echo "missing config $model/$cfg"; exit 1; }
done
tmux has-session -t "$session" 2>/dev/null && { echo "tmux session $session already exists"; exit 1; }

delay=0
for cfg in "$@"; do
  cmd="bash subset/tools/run_one.sh $model $cfg $delay $HOME/work/$session-$cfg.log; exec bash"
  if tmux has-session -t "$session" 2>/dev/null; then
    tmux new-window -t "$session" -n "$cfg" -c ~/work/TUA-Bench "$cmd"
  else
    tmux new-session -d -s "$session" -n "$cfg" -c ~/work/TUA-Bench "$cmd"
  fi
  delay=$((delay + 90))
done
tmux list-windows -t "$session"

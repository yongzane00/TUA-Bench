#!/usr/bin/env bash
# Run the arms of an ablation side by side, in rounds that start only when the model server is quiet.
#
#   cd ~/work/TUA-Bench
#   bash subset/tools/run_parallel.sh <session> <model> <rounds> <config> [<config> ...]
#
# Each config should have n_attempts: 1 and n_concurrent_trials: 1, so one round = every arm runs all its
# tasks once, the arms share the same server conditions, and our load stays at one trial per arm.
# A tmux session gets one "gate" window (subset/tools/run_gate.sh) and one window per arm
# (subset/tools/run_one.sh). Before each round the gate waits until the server has had no running or waiting
# request from anyone for IDLE_MIN minutes (default 10), then lets the arms start; the next round waits for
# every arm to finish and for the server to be quiet again. Each round is its own job folder under
# jobs/<model>/<config>/. Restarting the script skips rounds that already have a finished job folder.
# Logs: ~/work/<session>-gate.log and ~/work/<session>-<config>.log. Stop all: tmux kill-session -t <session>.

session=$1; model=$2; rounds=$3; shift 3
[ $# -gt 0 ] && [ "$rounds" -ge 1 ] 2>/dev/null || { echo "usage: run_parallel.sh <session> <model> <rounds> <config>..."; exit 1; }
cd ~/work/TUA-Bench || exit 1
for cfg in "$@"; do
  [ -f "subset/variants/$model/$cfg.yaml" ] || { echo "missing config $model/$cfg"; exit 1; }
done
tmux has-session -t "$session" 2>/dev/null && { echo "tmux session $session already exists"; exit 1; }
state=~/work/$session.state
mkdir -p "$state" && rm -f "$state"/go-* "$state"/done-*

tmux new-session -d -s "$session" -n gate -c ~/work/TUA-Bench \
  "METRICS_URL=$METRICS_URL TUA_JOBS=$TUA_JOBS DOCKER_CONFIG=$DOCKER_CONFIG HARBOR_APT_MIRROR=$HARBOR_APT_MIRROR bash subset/tools/run_gate.sh $session $model $rounds $*; exec bash"
delay=0
for cfg in "$@"; do
  tmux new-window -t "$session" -n "$cfg" -c ~/work/TUA-Bench \
    "TUA_JOBS=$TUA_JOBS DOCKER_CONFIG=$DOCKER_CONFIG HARBOR_APT_MIRROR=$HARBOR_APT_MIRROR bash subset/tools/run_one.sh $session $model $cfg $rounds $delay; exec bash"
  delay=$((delay + 60))
done
tmux list-windows -t "$session"

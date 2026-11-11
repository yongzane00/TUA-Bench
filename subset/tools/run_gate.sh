#!/usr/bin/env bash
# Gate for run_parallel.sh: before each round, wait until Docker answers and the model server has had no
# running or waiting request for IDLE_MIN minutes (checked every 30 s), then let the arms start
# (~/work/<session>.state/go-<round>); then wait until every arm has finished that round.
#
#   bash subset/tools/run_gate.sh <session> <model> <rounds> <config>...

session=$1; model=$2; rounds=$3; shift 3
cfgs=("$@")
IDLE_MIN=${IDLE_MIN:-10}
cd ~/work/TUA-Bench || exit 1
state=~/work/$session.state; log=~/work/$session-gate.log
JOBS=/mnt/c/Users/<win-user>/Desktop/playground/TUA-Bench/jobs
say() { echo "$(date '+%F %T') $*" | tee -a "$log"; }
finished() { grep -l '"finished_at": *"' "$JOBS/$model/$1"/*/result.json 2>/dev/null | wc -l; }
url=$(grep -m1 -oE 'api_base: *[^ ]+' "subset/variants/$model/${cfgs[0]}.yaml" | awk '{print $2}')
murl="${url%/v1}/metrics"
load() {  # prints "running waiting", or nothing if the server does not answer
  curl -sf -m 20 "$murl" | awk '/^vllm:num_requests_running\{/ {r += $2} /^vllm:num_requests_waiting\{/ {w += $2}
                                END {if (NR) print r + 0, w + 0}'
}

for r in $(seq 1 "$rounds"); do
  all=1
  for c in "${cfgs[@]}"; do [ "$(finished "$c")" -ge "$r" ] || all=0; done
  if [ $all = 1 ]; then say "round $r already finished for every arm"; touch "$state/go-$r"; continue; fi

  say "round $r: waiting for $IDLE_MIN quiet minutes on $murl"
  quiet=0; last=""
  while [ $quiet -lt $((IDLE_MIN * 2)) ]; do
    l=$(load)
    if docker info >/dev/null 2>&1 && [ "$l" = "0 0" ]; then quiet=$((quiet + 1)); else quiet=0; fi
    [ "$l" != "$last" ] && say "server running/waiting: ${l:-no answer}"; last=$l
    sleep 30
  done
  say "round $r: GO"
  touch "$state/go-$r"
  while true; do
    n=0
    for c in "${cfgs[@]}"; do [ -e "$state/done-$r-$c" ] && n=$((n + 1)); done
    [ $n -eq ${#cfgs[@]} ] && break
    sleep 60
  done
  say "round $r: every arm done"
done
say "all $rounds rounds done"

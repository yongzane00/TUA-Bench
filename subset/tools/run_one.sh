#!/usr/bin/env bash
# One arm of run_parallel.sh: for each round, wait for the gate (~/work/<session>.state/go-<round>), wait
# <delay> s (so the arms do not build images at the same moment), run the config once, and report done.
# A round that already has a finished job folder is skipped. A run that ends unfinished is tried once more.
#
#   bash subset/tools/run_one.sh <session> <model> <config> <rounds> <delay_sec>

session=$1; model=$2; cfg=$3; rounds=$4; delay=$5
export PATH="$HOME/.local/bin:$PATH"
cd ~/work/TUA-Bench || exit 1
state=~/work/$session.state; log=~/work/$session-$cfg.log
JOBS=/mnt/c/Users/<win-user>/Desktop/playground/TUA-Bench/jobs
say() { echo "$(date '+%F %T') $*" | tee -a "$log"; }
finished() { grep -l '"finished_at": *"' "$JOBS/$model/$cfg"/*/result.json 2>/dev/null | wc -l; }

for r in $(seq 1 "$rounds"); do
  if [ "$(finished)" -ge "$r" ]; then say "round $r already finished"; touch "$state/done-$r-$cfg"; continue; fi
  say "round $r: waiting for the gate"
  until [ -e "$state/go-$r" ]; do sleep 30; done
  sleep "$delay"
  for try in 1 2; do
    say "round $r: START $model/$cfg (try $try)"
    uv run --no-sync harbor run -c "subset/variants/$model/$cfg.yaml" -o "$JOBS/$model/$cfg" --yes 2>&1 | tee -a "$log"
    say "round $r: END $model/$cfg (exit ${PIPESTATUS[0]}, finished runs $(finished))"
    [ "$(finished)" -ge "$r" ] && break
  done
  touch "$state/done-$r-$cfg"
done
say "all rounds done"

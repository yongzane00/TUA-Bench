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
JOBS=${TUA_JOBS:-/mnt/c/Users/<win-user>/Desktop/playground/TUA-Bench/jobs}  # TUA_JOBS=/mnt/cfresh/... when /mnt/c gives I/O errors (CLAUDE.md)
say() { echo "$(date '+%F %T') $*" | tee -a "$log"; }
finished() {  # job folders with finished_at and at least one trial that did not error (an all-error run is not a round)
  python3 - "$JOBS/$model/$cfg" <<'PY'
import glob, json, sys
n = 0
for p in glob.glob(sys.argv[1] + "/*/result.json"):
    try:
        d = json.load(open(p))
    except Exception:
        continue
    s = d.get("stats") or {}
    n += bool(d.get("finished_at")) and s.get("n_errored_trials", 0) < (d.get("n_total_trials") or 1)
print(n)
PY
}

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
  [ "$(finished)" -ge "$r" ] || say "round $r: UNFINISHED after 2 tries (restart run_parallel.sh to run it again)"
  touch "$state/done-$r-$cfg"
done
say "all rounds done"

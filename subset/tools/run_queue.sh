#!/usr/bin/env bash
# Run one model's queue (subset/queue/<model>.txt) one config at a time, until every config is done.
#
#   cd ~/work/TUA-Bench
#   tmux new -d -s q38 'bash subset/tools/run_queue.sh qwen38-flash-next 2>&1 | tee -a ~/work/qwen38-queue.log'
#
# Before each run it re-reads the queue file (so you can reorder or add lines while it runs) and picks the
# first config without a finished run (job result.json with finished_at). A run that crashes or is
# interrupted stays unfinished and is retried once more later in the same pass; after 2 failed tries it is
# skipped. Before each run it waits until Docker and the model server (api_base in the config) answer, so an
# outage pauses the queue instead of using up tries. To stop after the current run: touch ~/work/STOP-<model>.
# Ctrl+C in the tmux window stops at once.

model=$1
[ -f "subset/queue/$model.txt" ] || [ -f ~/work/TUA-Bench/subset/queue/"$model.txt" ] || { echo "no queue file for '$model'"; exit 1; }
export PATH="$HOME/.local/bin:$PATH"  # uv, also when tmux starts a plain shell
cd ~/work/TUA-Bench || exit 1
JOBS=/mnt/c/Users/<win-user>/Desktop/playground/TUA-Bench/jobs
declare -A tries

finished() {  # newest run of this config has finished_at
  local d
  d=$(ls -d "$JOBS/$model/$1"/*/ 2>/dev/null | sort | tail -1)
  [ -n "$d" ] && grep -q '"finished_at": *"' "$d/result.json" 2>/dev/null
}

while true; do
  if [ -e ~/work/STOP-"$model" ]; then
    echo "$(date '+%F %T') STOP file found, ending queue"; rm -f ~/work/STOP-"$model"; break
  fi
  next=""
  while read -r cfg; do
    [[ -z "$cfg" || "$cfg" == \#* ]] && continue
    finished "$cfg" && continue
    [ "${tries[$cfg]:-0}" -ge 2 ] && continue
    pgrep -f "variants/$model/$cfg.yaml" >/dev/null && continue  # already running elsewhere
    next=$cfg; break
  done < "subset/queue/$model.txt"
  [ -z "$next" ] && { echo "$(date '+%F %T') queue done (nothing left to run)"; break; }

  # wait until Docker and the model server answer, so an outage doesn't use up a config's 2 tries in seconds
  url=$(grep -m1 -oE 'api_base: *[^ ]+' "subset/variants/$model/$next.yaml" | awk '{print $2}')
  waited=0
  until docker info >/dev/null 2>&1 && { [ -z "$url" ] || curl -sf -m 20 "$url/models" >/dev/null; }; do
    [ $waited = 0 ] && echo "$(date '+%F %T') WAIT  Docker or $url not ready; checking every 60 s"
    waited=1; sleep 60
    [ -e ~/work/STOP-"$model" ] && break
  done
  [ $waited = 1 ] && echo "$(date '+%F %T') READY"
  [ -e ~/work/STOP-"$model" ] && continue

  tries[$next]=$(( ${tries[$next]:-0} + 1 ))
  echo "$(date '+%F %T') START $model/$next (try ${tries[$next]})"
  uv run --no-sync harbor run -c "subset/variants/$model/$next.yaml" -o "$JOBS/$model/$next" --yes
  echo "$(date '+%F %T') END   $model/$next (exit $?)"
done

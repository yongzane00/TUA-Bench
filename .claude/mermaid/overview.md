# Harness variants: which step of the H0 loop each one changes

Read it as a table. Left: the stock terminus-2 (H0) steps, top to bottom; steps 2 to 5 repeat every
turn. Right: the variants that change that step. Colours match the results plot. H7–H9 share one
meter and differ only in which budgets they show and enforce (H7 time, H8 cost, H9 both plus the
turn number). Each variant has its own file (`H1.md` ... `H9.md`, `H0-timeout12000.md`).

```mermaid
block-beta
    columns 4
    t0["H0 step (stock terminus-2)"] t1["changed by"]:3

    s1["1 Start<br/>prompt = system prompt + task + first screen"]
    v1a["H5: BEFORE snapshot of the machine"] v1b["H6: + 'you have 40 turns'"] v1c["H7-H9: + 'your budget is 2400 s / $0.048 / both'"]

    s2["2 Model turn (repeats)<br/>reply = analysis, plan, keystrokes, duration"]
    n2["no variant"]:3

    s3["3 Run (repeats)<br/>type keystrokes, sleep 'duration' (max 60 s)"]
    v3a["H3: wait until bash shows its prompt again (max 180 s)"]:3

    s4["4 Observe (repeats)<br/>read the screen text"]
    v4a["H6: '[Turn N of 40]' on top"] v4b["H7-H9: budget meter on top: time or dollars used and left, speed, tokens, turns that still fit"]:2

    s5["5 Remember (repeats)<br/>history = every reply + every screen, reasoning dropped"]
    v5a["H2: keep the reasoning"] v5b["H4: last 3 screens verbatim, older ones summarized"]:2

    s6["6 Says done<br/>'Are you sure?' + screen, model confirms"]
    v6a["H1: + the task instruction again"] v6b["H5: AFTER snapshot, verifier judges the diff, FAIL sends reasons back"]:2

    s7["7 Ends and is graded<br/>done, or the 2400 s clock runs out"]
    v7a["H0 long: clock 12000 s"] v7b["H6: also after 40 turns"] v7c["H7-H9: also when the time or cost budget is used up"]

    classDef head fill:none,stroke:none,font-weight:bold
    classDef step fill:#f2f2f0,stroke:#888888,color:#111
    classDef none fill:none,stroke:#bbbbbb,stroke-dasharray:4 3,color:#888888
    classDef h1 fill:#dbe8ff,stroke:#2a5bd7,color:#111
    classDef h2 fill:#ffe4cc,stroke:#d9730d,color:#111
    classDef h3 fill:#ccf2ef,stroke:#0f8a80,color:#111
    classDef h4 fill:#e6e1ff,stroke:#4a3aa7,color:#111
    classDef h5 fill:#fbe0ea,stroke:#d55181,color:#111
    classDef h6 fill:#d9f0d9,stroke:#008300,color:#111
    classDef hb fill:#fdf0cc,stroke:#b27600,color:#111
    classDef ht fill:#eeeeee,stroke:#666666,color:#111
    class t0,t1 head
    class s1,s2,s3,s4,s5,s6,s7 step
    class n2 none
    class v6a h1
    class v5a h2
    class v3a h3
    class v5b h4
    class v1a,v6b h5
    class v1b,v4a,v7b h6
    class v1c,v4b,v7c hb
    class v7a ht
```

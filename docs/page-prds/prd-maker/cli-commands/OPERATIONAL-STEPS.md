# PRD Pipeline - Operational Steps

## OPTION A: Start From Your Own Agent OS Document (Current Setup)

You already did brainstorming, Agent OS, gap analysis, and second Agent OS pass on your own.
Now you just want to run it through the automated pipeline (stages 4-10).

### Steps

1. **Create your app folder**
   - In File Explorer, go to: `prd-output\`
   - Create a new folder with your app name (e.g., `prd-output\my-app\`)

2. **Drop your Agent OS document in the folder**
   - Save your finished Agent OS markdown file in that folder
   - Name it whatever you want (e.g., `agent-os.md`)

3. **Open Claude Code CLI**
   - Press `Windows + R`, type `cmd`, hit Enter
   - Type: `cd C:\Users\lober\.autoforge\workspace\repos\digisurfsome__Greptacular`
   - Type: `claude`
   - Wait for it to load (you'll see a chat prompt)

4. **Run the prep command**
   - Type: `/prd-prep prd-output/my-app/agent-os.md`
   - This reads your document and creates `context_packet.json`
   - It will tell you what it found and where the chain will start (Stage 3 or 4)
   - Wait for it to finish (1-2 minutes)

5. **Run the chain**
   - Type: `/prd-chain prd-output/my-app/`
   - This runs stages 3-10 (or 4-10) automatically
   - You'll see progress updates after each stage
   - Total time: 10-30 minutes depending on complexity

6. **If it stops mid-chain (context limit)**
   - It will save your progress automatically
   - Close the session (type `/exit` or close the window)
   - Open a new terminal, navigate to repo, launch `claude` again
   - Type: `/prd-chain prd-output/my-app/`
   - It picks up where it left off

7. **Collect your output**
   - When done, your folder will contain:
     - `context_packet.json` (pipeline state)
     - `phases/phase-1.md`, `phase-2.md`, etc. (build phases)
     - `build.sh` (build script)
     - `CLAUDE.md` (coding agent instructions)
     - `BUILD_RULES.md` (enforcement rules)
     - `README.md` (project readme)

---

## OPTION B: Full Pipeline in CLI (Start From Scratch)

You want to do the ENTIRE process in the CLI, from idea to final PRD.

### Steps

1. **Create your app folder**
   - Same as Option A step 1

2. **Open Claude Code CLI**
   - Same as Option A step 3

3. **Run the full pipeline**
   - Type: `/prd-start prd-output/my-app/`
   - This walks you through everything interactively:
     - Boilerplate selection (do you have one? which one?)
     - Idea capture (describe your app, go back and forth)
     - First Agent OS pass (structures your idea)
     - Gap analysis (finds holes, asks you questions)
     - Second Agent OS pass (merges everything into a complete spec)
   - When the interactive part is done, it saves `context_packet.json`

4. **Run the chain**
   - Type: `/prd-chain prd-output/my-app/`
   - Same as Option A steps 5-7

---

## Quick Reference

| What you want to do | Command |
|---------------------|---------|
| Convert existing Agent OS doc to pipeline format | `/prd-prep prd-output/my-app/agent-os.md` |
| Run automated chain (stages 3-10) | `/prd-chain prd-output/my-app/` |
| Resume chain after context limit | `/prd-chain prd-output/my-app/` (same command, new session) |
| Full pipeline from scratch (interactive + chain) | `/prd-start prd-output/my-app/` then `/prd-chain prd-output/my-app/` |

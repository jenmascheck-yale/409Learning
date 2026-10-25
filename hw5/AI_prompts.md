# AI Prompts

Homework 5: Campus Customs Multi-Agent Operations. A log of what I typed to my vibe coder, one section per problem.

---

## Problem 1: Vibe Coder Prompts

**Prompt:**

> Prob #1-time for hw5, it works the same way hw4 did.  review my word doc with the prompts in my own words that has the assignmnet, and i'll paste the screenshots so you can verfy the doc matches the live page.  then set up the AI_prompts.md log right at the start like we did for hw4 - one section per problem with the problem number and title and my prompt in my own words, plus a follow up if i needed one, and keep it updated as we go so by the end its a full record of how i described each problem to you.

---

## Problem 2: Study the Campus Customs Database

**Prompt:**

> Prob #2-lets study the campus customs databse now.  set up the hw5/data/ folder and put campus_customs.db in it, then make a working copy called campus_customs_new.db and point the mcp server and backend at the copy later so the orignal stays clean for resets.  go thru evry table and its feilds so i understand the whole db.  then study the three open tickets (101, 102, 103) and show how each one links out to the other tables (like sku to inventory and pricing, invoice_id to invoices, lease_id to leases).  then start output/harness.md and for evry table list its feilds and one short line on why that table matters for the agents — i'll keep growing this harness file in the later problms.

---

## Problem 3: Build the MCP Server

**Prompt:**

> Prob #3-lets build the MCP server now.  make it in mcp_server/server.py using FastMCP and point it at the working copy data/campus_customs_new.db, not the orignal.  i dont need to run or connect it yet, thats later.  write three clear read-only tools, one for each open ticket, and never make up data - only pull whats actualy in the db:  check_stock(sku, size) that reads inventory for ticket 101 (the size S tee thats out of stock), get_lease(lease_id) that reads leases for ticket 102 (the rent due), and get_pricing(sku) that reads pricing for ticket 103 (the bulk hoodie discount so accounting can check margin).  save the restock/invoice and the human-approved pay tools for problem 5.  then in output/harness.md list each tool with which table it reads, which ticket it unlocks, and one sentence on why its the right tool for that ticket, and add a short mcp_server/README.md that says what the server is for, which db file it uses, and the three tools.

**Follow-up:**

> also need a tool for get open invoices

*What was lacking after the first prompt: the three tools were key lookups, but ticket 101's tee restock is blocked by vendor 1's open invoice, so the team also needs to read open invoices to honor the "a vendor won't ship while they have an unpaid invoice" rule.*

---

## Problem 4: Add the MCP Server to Vibe Coder and Test Each Tool

**Prompt:**

> Prob #4-connect the MCP server to the vibe coder now and test the tools.  add the server to this project so claude code can call the tools and save the connection json in .mcp.json at the hw5 root.  then test each tool (check_stock, get_lease, get_pricing, and the get_open_invoices one i added) and save the evidence in output/mcp_smoke.json — for evry tool put the prompt i asked, the tool name, and the tool output, and make sure the output actualy matches the values in data/campus_customs_new.db.

---

## Problem 5: Build the Agent Team and Grow the MCP Tools

**Prompt:**

> Prob #5-build the full agent team for campus customs with pydanticAI - boss, inventory, accounting, facilities, and customer service - and give them full connectivity so any agent can delegate to any other.  put one prompt file per agent in backend/prompts/, the data types in backend/models.py, and the agent files under backend/.  use my PORTKEY_API_KEY and ONLY gpt-6-luna for evry agent, wired the same way we did hw4.  write each agent prompt in my own words and detailed, covering that agents whole job and the shop rules it needs (human approval for payments, no negative cash, a vendor wont ship with an open invoice, only real db data, drafts stay on the board).  grow the mcp server with whatever tools the agents need to actualy work the three tickets, and make sure all shop facts come from the mcp server over campus_customs_new.db - dont build a second tools layer that skips mcp.  wire the agents to append to output/audit_trail.json as they run (append, dont wipe).  then update output/harness.md with every agent and every mcp tool and which table it uses, plus a short safety section with the guardrails and the token limits, and update mcp_server/README.md so the tool list matches.

**Follow-up:**

> use the proposed tool set (prepare_payment + an approved pay, restock, get_vendor, get_cash_balance, list/get tickets, record_discount, resolve_ticket) and do a small live smoke run now on one ticket so i know it realy works

*What was lacking after the first prompt: the first prompt said "whatever tools the agents need" and left the live-run timing open, so I confirmed the exact tool set and asked for one small Portkey smoke run (ticket 102) to prove delegation + the human-approval guardrail before the full Problem 9 run.*

---

## Problem 6: Plan the Three Tickets

**Prompt:**

> Prob #6-before we wire the backend lets plan the three tickets.  build output/desk_tickets.html that i can just double click, with one tab per ticket (101, 102, 103) plus empty Cash and Reflection tabs for later (just a short "coming later" note for now).  on each ticket tab fill ONLY the Expected section and leave room for an Actual section i'll fill after the agents run.  in the expected section write in my own words who the boss should call first and why, all the delegations i expect (not "boss calls everyone"), and which mcp tools that run should use.  keep each ticket targeted to the right specialists so it dosnt look like every specialist works every ticket.  use the yale / bulldog blue look (garamond headings, verdana body) since campus customs is the same shop as hw4.

---

## Problem 7: Backend Routes

**Prompt:**

> Prob #7-build the fastapi backend in backend/main.py so the react dashboard can call it.  add routes to: return the three tickets and whether each is open or resolved, take a ticket id and run my agent team on that ticket, return the recent agent events (what each agent said and which tools they used) so the board can refresh, approve a payment or purchase after a human clicks approve - the agents only prepare the pay so THIS route is what actualy changes cash and updates the tables, return the current checking balance from cash_accounts, and reset the database back to the orignal values for a fresh run.  allow the vite dev origin (localhost:5173) so the browser can call it, and make sure it runs from the backend folder with uvicorn main:app --reload --port 8000.  then list each route in output/harness.md in one line.

---

## Problem 8: Agent Dashboard

**Prompt:**

> Prob #8-build the frontend dashboard in frontend/ with react + vite + typescript that talks to my backend at localhost:8000.  the board needs to: list all three tickets, let me pick one and start the agent team on it, show each agent and what theyre saying/doing while the ticket runs, mark a ticket resolved when the run finishes, show a short summary of what each agent did, let me (a human) approve a pay or purchase when the agents ask, and show the checking balance so it drops after an approved pay.  make it look really good and creative - a real desk someone would want to sit at - using the yale / bulldog blue look with garamond headings and verdana body like the rest of campus customs.  start it with npm run dev (the backend already allows the 5173 origin).  then write output/design.md explaining the layout, how each agent reads differently, how resolved tickets and the cash show up, and the creative choices that make it feel special.

---

## Problem 9: Resolve the Tickets

**Prompt:**

> Prob #9-time for the full run.  first reset the working db data/campus_customs_new.db so we start clean, and note the starting checking balance.  then run all three tickets (101, 102, 103) until each is resolved - run the agent teams first so they prepare the payments and resolve, then i approve the payments that make sense as the human so the cash actualy moves (that keeps the vendor invoice unpaid during the runs so nothing gets a free restock).  then fill the Actual section on each ticket tab in output/desk_tickets.html from what really happened (which agents worked, what they delegated, which tools they used) and keep my Expected so i can compare.  fill the Cash tab: starting balance after reset, how cash changed per ticket and why (which pay, dollar amount), and the ending balance - and make it match cash_accounts in the db.  save output/resolved_tickets.json (id, final status, short outcome, what each agent did, and any human approvals) and output/resolved_board.html that i can double click with a screenshot of the react board for each resolved ticket.  make sure the real runs are appended to output/audit_trail.json, and finish output/harness.md so it covers the tables, mcp tools, the five agents, the api routes, the dashboard, and the safety rules.

---

## Problem 10: Reflection

**Prompt:**

> Prob #10-fill the Reflection tab in output/desk_tickets.html, detailed and in my own vibe, and tie evry answer to this app and the three tickets we actualy ran (use the ticket tabs and the cash tab as my evidence, not a generic ai essay).  answer all five: how would i evaluate the agents performance on each ticket and why; for each ticket how did Actual compare to the Expected plan i wrote; what wouldve been simpler as one agent with tools and why; three new problems campus customs might face that this team COULD solve with the tools we built; and three new problems it could NOT solve with what we have, plus the tools and agents id need to add to solve them.

**Follow-up:**

> add more depth - put in the real run numbers (event and delegation counts, the cash trail), grade the safety/human-approval guardrail, dig into why the 103 draft said 20% and how id fix it, and use a balance sheet as a could-solve and a year-end income statement as a could-NOT-solve (since we never modeled revenue).  add a short manager takeaway at the end.

*What was lacking after the first prompt: the first version was solid but qualitative, so I added hard evidence from the run, a safety evaluation, a concrete failure fix, and the balance-sheet-vs-income-statement contrast to show I understand what the data does and doesn't support.*

---

## Problem 11: Submit to GitHub

**Prompt:**

> Prob #11-lets submit.  set up the hw5 folder as a git repo and push it to a PUBLIC github repo under my class account so graders can clone it.  add a .gitignore that keeps my real .env, the .venv, and node_modules out, but DO include both database files under data/ (the orignal and the working copy) since the assignment wants graders to run it.  write a root README.md that explains how to run everything: copy the orignal db to the working copy for a clean run, start the mcp server, start the fastapi backend, start the react board, and reset the db before a full three ticket run.  put the repo url in output/github_url.txt too.  then commit and push.

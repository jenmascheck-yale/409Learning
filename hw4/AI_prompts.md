# AI Prompts

Homework 4: Campus Customs Shop + Chatbot. A log of what I typed to my vibe coder, one section per problem.

---

## Problem 1: Vibe Coder Prompts

**Prompt:**

> Prob #1-set up an AI_prompts.md file right at the start so we log evry prompt i give you as we buid.  one section per problem with the problem number and title and my prompt in my own words, plus a follow up if i needed one.  keep it updated as we go so by the end its a full record of how i described each problem to you, whch is what problem 1 is graded on.

---

## Problem 2: Analyze the Database

**Prompt:**

> Prob #2-look at the campus_customs.db databse and help me undertand it.  go thru each table (at least catalogue, inventory, and users) and work out the feilds in each one.  then start output/harness.md and write down evry table with its fields and one short line on why each field matters for the shop or the chatbot, since i'll keep growing this harness file in the later problms.

---

## Problem 3: Build the Campus Customs Website

**Prompt:**

> Prob #3-build the Campus Customs website. Scaffold a react + vite + typescript front end for campus customs.  put a nav bar at the top that links to main pages:  Home, Products, About Us, Log in, Create Account.  Pull the Campus Customs-stylr wording from https://yalebulldogblue.com/.  write Homw & About Us in your own words (don not copy original text)  make sure to update the app appearance in agents.md for this folder.  On the products oage, show the product images from the catalog using the image paths in the database with basic product info like name, proce, short description.  Make each product open a single item page (large image on one side and full product text ont he other description price sizes stock when you have them.) clicking a card on products should take the shopper there.  Add achat interface in the bottom right of the site-it does not need to talk to an agent yet, a stub that will call your backend later is enough for #3.  you will need a small API soon to read the database.  start a simple fastapi app int he backend/main.py just to serve prodcucts and images, the grow it into the agent backend in problem 5

---

## Problem 4: Create Account and Login

**Prompt:**

> Prob #4-build create account and login flow Create account should ask for first name, last name, email, password and confirm password.  lOg in email and password.  New accounts fo into the users table.  Make sure to store passwords securely so hackers humans and ai cannot access them

---

## Problem 5: PydanticAI Agent Backend

**Prompt:**

> Prob #5-build the shop chatbot as a pydanticAI agent behind fastapi and hook it up to the chat widget on the site.  keep the api app in backend/main.py since thats the file i run with uvicorn, and keep the agent in four files next to it: prompts/prompt.md for the sytem prompt, agent.py for the wiring, tools.py for the tools (those come later), and models.py for the pydantic types.  expose a chat route in main.py so when someone types in the chat on the websie it sends the mesage to the agent and shows the agents reply back.  use openai directly with gpt-6-luna from my .env key, not portkey.  give the chatbot a freindly yale shop helper voice, like a student working the campus customs counter, and put basic safety rules in prompt.md: only use real databse data and never make up prices or stock, stay on campus customs topics, no personal or finanical advice, and keep it respectful and apropriate for everyone.  start the types in models.py for the chat reply (and product cards for later).  update output/harness.md with how the front end talks to fastapi and how the agent loads (prompt file + model).  make sure the backend still runs from the backend folder like uvicorn main:app --reload --port 8000.

---

## Problem 6: Tools — Product Info and Stock

**Prompt:**

> Prob #6-give the agent tools that look up real info from campus_customs.db so it can answer about a products descripton, its price, and how many are in stock (by size when someone asks about a size).  the agent has to actually use the databse for this and never make up prices or quantites, and if a size is out of stock it should say so clearly.  make it three seperate, clearly named tools (one for description, one for price, one for stock) since there are three things to look up and its easier to follow.  the stock tool should return the size and the quantity and say "sold out" when the quantity is 0, insted of handing back raw databse rows, so the agent answers honestly.  also let the tools find a product from how a shopper describes it (like "the big yale hoodie") by matching on the product name and type, not just an exact id.  put the tools in tools.py and register them on the agent in agent.py.  expand prompts/prompt.md so the agent knows to call these tools whenver someone asks about price or stock.  add or update the return types in models.py for what the tools give back.  then in output/harness.md list each tool and explain which model feilds i picked for the lookup results and why.

---

## Problem 7: Chat Search That Updates the Page

**Prompt:**

> Prob #7-add a neat feature so when a customer asks about a type of item (like "what hoodies do you have?") the agent serches the catalogue and the matching items show up as product cards with the image, name, price and a short bit of info.  make this an api contract like the problem says - the agent retuns structured product matches and then the front end renders them on the site.  give the agent a serch tool that finds the matches, and send those matches back in the structured chat reply (the products list we alredy have in models.py).  i want the cards to show up in BOTH places - right under the agents reply in the chat pannel, AND update the main products grid on the page so the page itself changes.  then make sure the single item page from problem 3 still works: evry product card, including the ones the chat just put on the page, should still open the big detail view (large image + full info) when you click it.  update prompts/prompt.md and output/harness.md so its clear how the serch results get from the agent to the page.

---

## Problem 8: Customer Memory

**Prompt:**

> Prob #8-give the chatbot excellcent memory.  when a shoper is logged in, save their chat histroy in the databse in an apropriate table and reload it when they come back so the convo picks up were they left off.  we alredy have a chat_messages table so use that one.  the agent should know who its talkng to (name and email) - put that in the agent deps or tools it can call so it can greet them and keep it personel.  also pass enough page context that if someone is on a product page and asks "do you have this in pink?" the agent knows wich item they mean (the hint says you can put code into the agent context).  guests can still chat but the histroy only needs to persist for logged in users.  then documnet in output/harness.md how the chat histroy is stored, what customer feilds the agent sees, and how the page context gets passed.

---

## Problem 9: Usability Improvements

**Prompt:**

> Prob #9-now that the core shop works lets improve it.  i want 2 front end usability improvments and 2 agent/backend ones, and they all have to actually show up in the running app.  for the front end: (1) add a filter and serch on the products page so shoppers can narrow down by catagory (hoodies, tees, quarter-zips etc) and type in a serch box, and (2) add quick question chips in the chat - little tappable suggested questions like "what hoodies do you have?" so people can start chatting in one click.  for the agent/backend: (1) give the agent a browse-catagories tool so it can tell someone what kinds of items we sell when they dont know what to ask for, and (2) make the calls cheaper and faster by caping the serch results and triming the chat histroy we send to the model so we dont waste tokens.  then write output/usability.md as i build and for each improvment say what i added and why it helps a campus customs shopper or the busness.  make sure all 4 realy show up in the app becuase the graders will look for them.

---

## Problem 10: Style the Website

**Prompt:**

> Prob #10-add creative design so the site feels like a real campus customs storefront - fonts, color, hierarchy, motion, product presentation, the chat feel.  i want a classic collegiate look that fits yale: keep the yale blue and the garamond headings and verdana body we alredy set, and make it feel refined and timeless with generous whitespace, nice type hierarchy, some crest or seal type touches, and subtle motion like soft fades and hover lifts on the product cards (nothing over the top).  polish the hero, the product cards, the single item page and the chat panel so it all looks like one real store.  im going for imaginative and innovative since thats worth more points.  then write output/design.md, keep it concrete and short, saying what i changed and why it should help customers stick around and buy.

---

## Problem 11: Site Testing (App Check)

**Prompt:**

> Prob #11-test the live site and documnet it in output/app_check.html so i can just double click it open.  put in clear screenshots with short captions for three checks: (1) the chat checking the inventory level of an item so it shows honest stock and price from the databse, (2) the dynamic serch result cards showing up after a catagory question like hoodies, and (3) one of the usability featurs i added in problem 9 - use the filter and serch on the products page.  make the html easy to grade with a heading for each check, the screenshot, and one or two sentences on what the screenshot proves.  put the screenshot image files in output/app_check_images/ and link them from app_check.html with relative paths like app_check_images/inventory.png.

---

## Problem 12: Audit Trail, Safety, Finish Harness

**Prompt:**

> Prob #12-keep an append-only output/audit_trail.json that logs the agent loop activity - the time, the tool name, short args and result, and the stop reason - and do NOT wipe it between runs, just keep appending.  also finalize the safety rules for the agent in prompts/prompt.md (we alredy have the ones i picked earlier, keep those and tighten them up).  then finish output/harness.md so its clear how the whole system works: the model fields in models.py and why i chose them, the tools and abilities, the safety rules, and the specs like loop limits, result caps, which model, and how to run the front end and back end.

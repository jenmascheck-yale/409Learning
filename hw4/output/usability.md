# Usability Improvements (Problem 9)

Four improvements — two front-end, two agent/backend. All four show up in the running app.

## Front-end

### 1. Filter and search on the Products page

**What I added:** Category buttons (All, Hoodies, Crewnecks, T-Shirts, Quarter-Zips, Jackets) and a search box above the product grid. The buttons filter the catalogue to one category; the search box matches on product name, type, and description. A live "N products" count updates as you filter, and a friendly message shows when nothing matches.

**Why it helps:** The shop has 102 products with inconsistent type labels. A shopper who wants a hoodie shouldn't have to scroll past everything else. Filtering and searching lets them get to what they want in seconds, which keeps them browsing and makes them more likely to buy.

### 2. Quick-question chips in the chat

**What I added:** A row of one-tap suggested questions in the chat panel ("What do you sell?", "What hoodies do you have?", "Show me quarter-zips", "What crewnecks are there?"). Tapping one sends it instantly.

**Why it helps:** A blank chat box is intimidating and shoppers may not know what to ask. The chips show what the assistant can do and let someone start a useful conversation in one click, so more shoppers actually use the chat — and the chat drives them to products.

## Agent / backend

### 3. Browse-categories tool (`list_categories`)

**What I added:** A new agent tool that lists the kinds of items the shop sells (crewnecks, T-shirts, hoodies, quarter-zips, jackets) with a count of each, grouped from the messy `garment_type` labels in the database. The system prompt tells the agent to use it when a shopper asks what's sold or isn't sure what to look for.

**Why it helps:** Shoppers often don't know the exact product name. Instead of a dead-end "I'm not sure," the assistant can now accurately say what categories exist and guide them to a section — more helpful, and grounded in real data rather than a guess.

### 4. Cheaper and faster agent calls

**What I added:** Two caps that cut token use and latency. (a) Catalogue searches are capped at 12 results (`SEARCH_LIMIT`), so a broad question never dumps the whole catalogue into the model. (b) Only the last 10 messages of a shopper's history (`MODEL_HISTORY_LIMIT`) are sent to the model, even though the full conversation stays saved in the database and is shown in the chat panel.

**Why it helps:** Fewer tokens per call means lower cost for the business and faster replies for the shopper, without losing the saved history or the on-page product cards. It keeps the assistant affordable to run as conversations get long.

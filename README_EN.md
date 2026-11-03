# How to Run the Project

1. **Clone the repository and create a virtual environment:**
```bash
python -m venv venv
```

2. **Activate the virtual environment:**
- On Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```
- On Linux/macOS:
```bash
source venv/bin/activate
```

3. **Install the project dependencies:**
```bash
pip install -r requirements/requirements.txt
```

4. **Configure your Gemini API Key:**
Create a `.env` file inside the `src/` folder (you can use `example.env` as a template) and add your key:
```env
GEMINI_API_KEY=YOUR_API_KEY_HERE
```

5. **Run the ETL script (Gold Layer) to generate the processed datasets:**
```bash
python src/etl/gold.py
```

6. **Run the main agent:**
```bash
python src/agent/music_agent.py
```

---

# Proposed Solution - Theory

I developed the project by first designing an architecture. This architecture consists of a main agent that answers user questions about the store; this agent queries the databases using tools: one of these knowledge bases contains the company policies (in PDF) and the other contains the processed datasets of products/promotions and orders/customers (in CSV). I also included an input guardrail to block malicious prompts or questions outside the context of the music store, and an output guardrail to prevent the agent from leaking sensitive database information or out-of-scope content.

I used distinct Information Retrieval techniques for each knowledge base. The company policy knowledge base uses a PDF containing information about Empório da Música; I split this PDF into text chunks by page, transformed them into vectors (embeddings), and stored them in the FAISS vector database. I chose to do this because the PDF contains many data entities and it would be complicated to use other information retrieval techniques. For the products/promotions and orders/customers datasets, I used the TF-IDF technique, which measures the importance of a word in a specific document relative to a collection of documents. In the context of this work, I measured the importance of the words in the database relative to what the user is looking for—for example, if the user wants to know about a guitar, that word is important and will be searched in the database.

![Agent Architecture](./diagrama_musicae.drawio%20(1).png)


## Technologies Used


* LLM: I used the `gemini-flash-lite-latest` model for the guardrails and the `gemini-3-flash-preview` model for the main agent (along with `gemini-embedding-001` to generate the PDF embeddings). I chose to use Google models because the company offers twenty free daily requests for its models via API. To use the models, you need to create an API key [Here](https://aistudio.google.com/).

* Frameworks: I used [Pandas](https://pandas.pydata.org/) to process and perform exploratory data analysis on the data; I used the [Scikit-Learn](https://scikit-learn.org/) library to apply TF-IDF; I used [PyPDF](https://pypdf.readthedocs.io/) and [LangChain](https://www.langchain.com/) to extract the PDF data into chunks, transform them into embeddings, and create the tools; I used [LangGraph](https://www.langchain.com/langgraph) to build the agent workflow and the guardrails; I used [FAISS](https://faiss.ai/index.html) as a vector database to store the embeddings of the store policy PDF;

* AI Assistants: I used Antigravity to recall Pandas commands, to validate whether the agent code in LangGraph was correct, and to investigate bugs that came up during the process, such as Google API request issues and GuardRails blocks caused by the System Prompt I used;

## Points for Improvement

* Model response validation: I did not include automated validation of the LLM response due to time constraints. However, this point is extremely crucial to verify whether the LLM is hallucinating or whether another LLM model performs better than the production one;

* Multi-Agent System Architecture: It would be interesting to develop a Multi-Agent System architecture; to improve the agent's response, we could split the current agent's work into two. For example, one agent could be responsible for knowing about the store policies while another could be responsible for knowing about the store's products and orders;

* GuardRails: The GuardRails present a serious issue: the LLM itself decides when content is appropriate or not, meaning that if the LLM hallucinates, content might be wrongly blocked or allowed through to the agent. Despite this limitation, the current GuardRails worked well and blocked several out-of-scope user questions, such as in this case:

> **Question:** What is the price of a 64 GB DDR5 RAM stick?
>
> **Answer:** Sorry, I can only answer questions related to the Empório da Música store (musical instruments, stock, promotions, orders, and store policies).

However, the GuardRails let questions related to bands pass through; even though the agent shows that a band X does not exist in the database, it still answers about the musical content before steering the conversation back to the store's instruments. Example:

> **Question:** Tell me about the band Calcinha Preta
>
> **Answer:** For sure! Talking about Calcinha Preta is talking about one of the biggest icons of electronic forró in Brazil. The band started in Aracaju back in 1995 and revolutionized the genre with that more romantic vibe, super well-produced shows, and, of course, the iconic voices that passed through it, such as Daniel Diau, Silvânia Aquino, and the eternal Paulinha Abelha.
>
> They have anthems that everyone knows, like "Você Não Vale Nada", "Manchete dos Jornais", and "Hoje à Noite". It's the kind of sound that gets everyone moving and marked generations!
>
> Since I'm the assistant here at **Empório da Música**, my focus is helping folks find the ideal instrument to play that kind of sound (or any other!). If you're looking for a keyboard, an acoustic guitar, or a bass to play those Calcinha Preta hits, just let me know and I'll check our stock for you.
>
> Just a reminder that here at the store we focus exclusively on musical instruments, okay? How can I help you today?

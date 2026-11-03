# Como Executar o Projeto

1. **Clone o repositório e crie o ambiente virtual:**
```bash
python -m venv venv
```

2. **Ative o ambiente virtual:**
- No Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```
- No Linux/macOS:
```bash
source venv/bin/activate
```

3. **Instale as dependências do projeto:**
```bash
pip install -r requirements/requirements.txt
```

4. **Configure a chave de API do Gemini:**
Crie um arquivo `.env` dentro da pasta `src/` (você pode usar o arquivo `example.env` como base) e adicione a sua chave:
```env
GEMINI_API_KEY=SUA_CHAVE_AQUI
```

5. **Execute o script de ETL (Camada Gold) para gerar as bases tratadas:**
```bash
python src/etl/gold.py
```

6. **Execute o agente principal:**
```bash
python src/agent/music_agent.py
```

---

# Solução Proposta - Teoria

Desenvolvi o projeto construindo primeiramente uma arquitetura. Essa arquitetura consiste em um agente principal, que vai responder o usuário sobre as suas dúvidas em relação à loja, esse agente vai fazer requisições às bases de dados utilizando tools: uma dessas bases contém a política da empresa (em PDF) e a outra contém os dados tratados das bases de produtos/promoções e pedidos/clientes (em CSV). Incluí também um input guardrails, para barrar prompts maliciosos ou fora do contexto da loja de música, e também incluí um output guardrails para fazer com que o agente não vaze dados sensíveis das bases ou informações fora do escopo.

Utilizei técnicas distintas de Recuperação da Informação para as bases. A base de políticas da empresa faz uso de um PDF contendo informações sobre a Empório da Música, dividi esse PDF em pedaços de texto por página, transformei em vetores (embeddings) e os armazenei no banco vetorial FAISS, optei em fazer isso porque o PDF tem muitas entidades de dados e seria complicado utilizar outras técnicas de recuperação da informação. Para as bases de dados dos produtos/promoções e pedidos/clientes utilizei a técnica TF-IDF, essa técnica mede a importância de uma palavra em um documento específico em relação a um conjunto de documentos, no caso desse trabalho, medi a importância das palavras da base em relação ao que o usuário deseja, por exemplo, se o usuário deseja saber sobre uma guitarra essa palavra é importante e será buscada na base de dados.

![Arquitetura do Agente](./diagrama_musicae.drawio%20(1).png)


## Tecnologias Utilizadas


* LLM: Utilizei o modelo `gemini-flash-lite-latest` nos guardrails e o modelo `gemini-3-flash-preview` para o agente principal (além do `gemini-embedding-001` para gerar os embeddings do PDF), optei por utilizar modelos do Google porque a empresa oferece vinte requisições diárias gratuitas para seus modelos por meio de API. Para utilizar os modelos é necessário que você crie uma chave de API [Aqui](https://aistudio.google.com/).

* Frameworks: Utilizei [Pandas](https://pandas.pydata.org/) para tratar e fazer uma análise exploratória dos dados; Utilizei a biblioteca [Scikit-Learn](https://scikit-learn.org/) para aplicar o TF-IDF; Utilizei o [PyPDF](https://pypdf.readthedocs.io/) e o [LangChain](https://www.langchain.com/) para extrair os dados do PDF em pedaços, transformá-los em embeddings e criar as tools; Utilizei o [LangGraph](https://www.langchain.com/langgraph) para desenvolver o fluxo do agente e os guardrails; Utilizei o [FAISS](https://faiss.ai/index.html) como banco vetorial para armazenar os embeddings do PDF das políticas da loja;

* Assistentes de IA: Utilizei o Antigravity para relembrar de comandos do Pandas, para validar se o código dos agentes no LangGraph estava correto; Para investigar bugs que apareceram no processo, como problemas de requisições à API do Google e travas no GuardRails por causa do System Prompt que utilizei;

## Pontos para melhorar

* Validação da resposta dos modelos: Não incluí a validação automatizada da resposta do modelo de LLM por falta de tempo. Mas, esse ponto é extremamente crucial para verificar se a LLM está alucinando ou se um outro modelo de LLM funciona melhor que o de produção;

* Arquitetura de Sistemas Multiagentes: Seria interessante desenvolver uma arquitetura de Sistemas Multiagentes, para melhorar a resposta do agente poderíamos dividir o trabalho do agente atual em dois. Por exemplo, um agente pode ser responsável por saber sobre a política da loja enquanto outro pode ser responsável por saber sobre os produtos e pedidos da loja;

* GuardRails: O GuardRails apresenta um problema grave, a LLM que decide quando o conteúdo é apropriado ou não, ou seja, se a LLM alucinar pode ser que o conteúdo seja barrado ou passe para o agente. Apesar desse problema, o GuardRails atual funcionou bem e barrou algumas perguntas do usuário, como nesse caso:

> **Pergunta:** Qual o valor de um pente de memória RAM de 64 GB DDR5 ?
>
> **Resposta:** Desculpe, só posso responder perguntas relacionadas à loja Empório da Música (instrumentos musicais, estoque, promoções, pedidos e políticas da loja).

Entretanto, o GuardRails deixa passar quando fazemos perguntas relacionadas a bandas, apesar de o agente mostrar que uma banda X não existe no banco de informações, ele ainda responde sobre o conteúdo musical antes de puxar a conversa para os instrumentos da loja. Exemplo:

> **Pergunta:** Me fale sobre a banda Calcinha Preta
>
> **Resposta:** Com certeza! Falar de Calcinha Preta é falar de um dos maiores ícones do forró eletrônico no Brasil. A banda surgiu em Aracaju, lá em 1995, e revolucionou o gênero com aquela pegada mais romântica, shows super produzidos e, claro, as vozes marcantes que passaram por lá, como Daniel Diau, Silvânia Aquino e a eterna Paulinha Abelha.
>
> Eles têm hinos que todo mundo conhece, como "Você Não Vale Nada", "Manchete dos Jornais" e "Hoje à Noite". É o tipo de som que não deixa ninguém parado e marcou gerações!
>
> Como sou o assistente aqui da **Empório da Música**, meu foco é ajudar a galera a encontrar o instrumento ideal para fazer esse tipo de som (ou qualquer outro!). Se você estiver procurando um teclado, um violão ou um baixo para tirar esses sucessos do Calcinha Preta, é só me falar que eu dou uma olhada no nosso estoque para você.
>
> Lembrando que aqui na loja focamos exclusivamente em instrumentos musicais, tá bom? Como posso te ajudar hoje?
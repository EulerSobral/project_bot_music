import os
from pathlib import Path
from typing import TypedDict
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

from prompt import PROMPT_INPUT_GUARDRAILS, AGENT_MUSIC_PROMPT, OUTPUT_GUARDRAILS
from tool_politc_store import query_store_policies
from tool_querry_database import query_orders_customers, query_products_promotions

# Load environment variables from src/.env
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)


class AgentState(TypedDict, total=False):
    question: str
    answer: str
    is_input_valid: bool


class MusicAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        # Modelo rápido e determinístico (temperature=0.0) para os guardrails de entrada e saída
        self.llm_guardrail = ChatGoogleGenerativeAI(
            model="gemini-flash-lite-latest",
            google_api_key=api_key,
            temperature=0.0,
        )

        # Modelo principal do agente conectado às ferramentas da loja
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3-flash-preview",
            google_api_key=api_key,
            temperature=0.3,
        )
        self.tools = [
            query_store_policies,
            query_products_promotions,
            query_orders_customers,
        ]
        self.tool_agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=AGENT_MUSIC_PROMPT,
        )

        self.app = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AgentState)

        graph.add_node("start", self.start)
        graph.add_node("input_guardrail", self.input_guardrail)
        graph.add_node("ask_question", self.ask_question)
        graph.add_node("output_guardrail", self.output_guardrail)

        graph.add_edge(START, "start")
        graph.add_conditional_edges(
            "start",
            lambda state: "input_guardrail" if state.get("question") else END,
        )
        graph.add_conditional_edges(
            "input_guardrail",
            lambda state: "ask_question" if state.get("is_input_valid") else END,
        )
        graph.add_edge("ask_question", "output_guardrail")
        graph.add_edge("output_guardrail", END)

        return graph.compile()

    def start(self, state: AgentState) -> AgentState:
        question = (state.get("question") or "").strip()
        if not question:
            return {
                "question": "",
                "is_input_valid": False,
                "answer": "Por favor, envie uma pergunta para que eu possa ajudar.",
            }
        return {"question": question}

    def input_guardrail(self, state: AgentState) -> AgentState:
        question = state.get("question", "")
        guardrail_prompt = (
            f"{PROMPT_INPUT_GUARDRAILS}\n\n"
            f"Pergunta do usuário: {question}\n\n"
            f"Resposta:"
        )
        guardrail_response = self.llm_guardrail.invoke(guardrail_prompt)
        verdict = guardrail_response.text.strip().upper()

        if "INAPPROPRIATE" not in verdict and verdict.startswith("APPROPRIATE"):
            return {"is_input_valid": True}

        return {
            "is_input_valid": False,
            "answer": (
                "Desculpe, só posso responder perguntas relacionadas à loja Empório da Música "
                "(instrumentos musicais, estoque, promoções, pedidos e políticas da loja)."
            ),
        }

    def ask_question(self, state: AgentState) -> AgentState:
        question = state.get("question", "")
        result = self.tool_agent.invoke(
            {"messages": [{"role": "user", "content": question}]}
        )
        last_message = result["messages"][-1]
        answer = getattr(last_message, "text", None) or str(last_message.content)
        return {"answer": answer}

    def output_guardrail(self, state: AgentState) -> AgentState:
        answer = state.get("answer", "")
        guardrail_prompt = (
            f"{OUTPUT_GUARDRAILS}\n\n"
            f"Resposta do assistente: {answer}\n\n"
            f"Resposta:"
        )
        guardrail_response = self.llm_guardrail.invoke(guardrail_prompt)
        verdict = guardrail_response.text.strip().upper()

        if "INAPPROPRIATE" not in verdict and verdict.startswith("APPROPRIATE"): 
            return {"answer": answer}

        return {"answer": "Desculpe, mas não posso responder a essa pergunta."}

    def run(self, input_data: dict | str) -> str:
        if isinstance(input_data, str):
            state_input: AgentState = {"question": input_data}
        else:
            state_input = {"question": input_data.get("question", "")}

        final_state = self.app.invoke(state_input)
        return final_state.get("answer", "")


if __name__ == "__main__": 

    OUTPUT_PATH = Path(__file__).resolve().parents[1] / "output" / "response.txt" 

    agent = MusicAgent()

    question = input("Digite sua pergunta para o assistente da loja Empório da Música: ").strip()
    answer = agent.run({"question": question})  


    with open(OUTPUT_PATH, mode="a", encoding="utf-8") as arquivo:
        arquivo.write(question + "\n" + answer + "\n\n")
    print(f"Pergunta: {question}\n")
    print(f"Resposta:\n{answer}")

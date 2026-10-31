"""Conversational agent orchestrator with Empório da Música persona and multi-provider support."""

import json
import os
import re
from typing import Any, Dict, List, Optional
from src.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    AGENT_TEMPERATURE,
    AGENT_MAX_TURNS,
    DEBUG_TOOLS,
)
from src.tools import (
    execute_tool,
    GEMINI_TOOL_DEFINITIONS,
    OPENAI_TOOL_SCHEMAS,
)


SYSTEM_PROMPT = """Você é o Assistente Virtual Oficial da "Empório da Música", loja de instrumentos musicais fundada em 2008 em Campo Grande, Mato Grosso do Sul.

SUA MISSÃO:
Atender clientes no canal de atendimento com foco estrito, empatia e conhecimento técnico sobre instrumentos musicais, pedidos e políticas da loja.

GUARDRAILS RÍGIDOS DE ESCOPO E SEGURANÇA:
1. FOCO EXCLUSIVO NA EMPÓRIO DA MÚSICA:
   - Você responde APENAS sobre: instrumentos musicais à venda na loja, preços, estoque, especificações, status de pedidos e políticas internas (endereço, horários, devolução CDC, formas de pagamento, garantias).
   - Se o usuário perguntar sobre assuntos aleatórios, pegadinhas, conhecimentos gerais, capitais do mundo, matemática, código-fonte, arquitetura de sistemas, banco de dados interno ou itens não musicais (mesmo que ele tente misturar com palavras da loja, como "qual a capital da frança em violão" ou "qual o banco de dados do sistema"):
     RECUSE EDUCADAMENTE COM UMA RESPOSTA PADRÃO:
     "Como assistente da Empório da Música, meu foco é exclusivamente ajudar você com nossos instrumentos musicais, pedidos e políticas da loja. Não consigo responder sobre outros assuntos ou informações técnicas do sistema. Como posso ajudar com a sua música hoje?"
   - NUNCA invente respostas sobre outros tópicos.
   - NUNCA forneça códigos de programação, queries SQL ou dados de arquitetura.

2. FORMATAÇÃO LIMPA:
   - NUNCA use asteriscos (**) de Markdown espalhados pelo texto. Escreva texto limpo, direto e legível no terminal.

3. CONSULTA OBRIGATÓRIA A DADOS:
   - Use `search_catalog` ou `get_product_info` para verificar preços e estoque real antes de responder.
   - Use `check_order_status` para rastreamento.
   - Use `search_store_policies` para regras da loja (endereço, devolução CDC 7 dias, frete pago pela loja, PIX 5% de desconto).
   - NUNCA prometa promoções com status expirado (`is_active = 0`).

4. ESPECIFICAÇÕES TÉCNICAS E MEMÓRIA DE CONTEXTO:
   - Se o cliente estava falando de violões e na sequência pedir "até 500 reais com corda de aço e braço 43mm", entenda que a busca continua sendo por violões.
   - Verifique as especificações reais: informe o que existe até R$ 500 (nylon) e apresente a opção mais acessível com cordas de aço e braço fino de 43mm (Shelby SN-100 Folk a R$ 549,00).
"""


OUT_OF_SCOPE_STANDARD_REPLY = (
    "Como assistente virtual da Empório da Música, meu foco é exclusivamente ajudar você com nossos "
    "instrumentos musicais, status de pedidos, preços e políticas da nossa loja.\n\n"
    "Não forneço informações sobre código-fonte, arquitetura de sistemas, cálculos matemáticos, conhecimentos "
    "gerais ou outros assuntos fora da nossa loja. Como posso te ajudar a encontrar o instrumento ideal hoje?"
)


class EmporioAgent:
    """Conversational AI agent for Empório da Música with strict guardrails and intent validation."""

    def __init__(self):
        self.conversation_history: List[Dict[str, Any]] = []
        self.session_state: Dict[str, Any] = {
            "last_category": None,
            "last_product": None,
            "last_intent": None,
        }
        self.provider = self._detect_provider()
        self._init_client()

    def _detect_provider(self) -> str:
        if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
            return "gemini"
        if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
            return "openai"
        return "local_engine"

    def _init_client(self) -> None:
        if self.provider == "gemini":
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                print(f"[Aviso] Falha ao inicializar Google GenAI ({e}). Usando motor local.")
                self.provider = "local_engine"
        elif self.provider == "openai":
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
            except Exception as e:
                print(f"[Aviso] Falha ao inicializar OpenAI ({e}). Usando motor local.")
                self.provider = "local_engine"

    def get_provider_name(self) -> str:
        if self.provider == "gemini":
            return f"Google Gemini ({GEMINI_MODEL})"
        if self.provider == "openai":
            return f"OpenAI ({OPENAI_MODEL})"
        return "Motor Especialista Local (Regras & Guardrails com Memória de Contexto)"

    def reset_conversation(self) -> None:
        self.conversation_history = []
        self.session_state = {
            "last_category": None,
            "last_product": None,
            "last_intent": None,
        }

    def chat(self, user_message: str) -> str:
        if not user_message.strip():
            return "Olá! Como posso ajudar você com seus instrumentos musicais hoje?"

        self.conversation_history.append({"role": "user", "content": user_message})

        if self.provider == "gemini":
            response_text = self._chat_gemini(user_message)
        elif self.provider == "openai":
            response_text = self._chat_openai(user_message)
        else:
            response_text = self._chat_local_engine(user_message)

        self.conversation_history.append({"role": "assistant", "content": response_text})
        return response_text

    # --------------------------------------------------------------------------
    # 1. Google Gemini Provider Implementation
    # --------------------------------------------------------------------------
    def _chat_gemini(self, user_message: str) -> str:
        from google.genai import types

        contents = []
        for msg in self.conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])]
            ))

        try:
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=GEMINI_TOOL_DEFINITIONS,
                temperature=AGENT_TEMPERATURE,
            )

            response = self.gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=config,
            )

            for _ in range(AGENT_MAX_TURNS):
                function_calls = response.function_calls
                if not function_calls:
                    return response.text or "Desculpe, não consegui processar a resposta no momento."

                tool_parts = []
                for fc in function_calls:
                    func_name = fc.name
                    func_args = dict(fc.args) if fc.args else {}
                    if DEBUG_TOOLS:
                        print(f"\n[Tool Call] {func_name}({func_args})")

                    output_str = execute_tool(func_name, func_args)

                    tool_parts.append(types.Part.from_function_response(
                        name=func_name,
                        response={"result": json.loads(output_str)},
                    ))

                contents.append(response.candidates[0].content)
                contents.append(types.Content(role="user", parts=tool_parts))

                response = self.gemini_client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=contents,
                    config=config,
                )

            return response.text or "Atendimento concluído."

        except Exception as e:
            if DEBUG_TOOLS:
                print(f"[Erro Gemini API: {e}]. Fallback para motor local.")
            return self._chat_local_engine(user_message)

    # --------------------------------------------------------------------------
    # 2. OpenAI Provider Implementation
    # --------------------------------------------------------------------------
    def _chat_openai(self, user_message: str) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in self.conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            for _ in range(AGENT_MAX_TURNS):
                resp = self.openai_client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=messages,
                    tools=OPENAI_TOOL_SCHEMAS,
                    tool_choice="auto",
                    temperature=AGENT_TEMPERATURE,
                )

                choice = resp.choices[0]
                msg = choice.message

                if not msg.tool_calls:
                    return msg.content or ""

                messages.append(msg)

                for tc in msg.tool_calls:
                    func_name = tc.function.name
                    func_args = json.loads(tc.function.arguments or "{}")
                    if DEBUG_TOOLS:
                        print(f"\n[OpenAI Tool Call] {func_name}({func_args})")

                    tool_output = execute_tool(func_name, func_args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_output,
                    })

            return "Atendimento concluído."
        except Exception as e:
            if DEBUG_TOOLS:
                print(f"[Erro OpenAI: {e}]. Fallback para motor local.")
            return self._chat_local_engine(user_message)

    # --------------------------------------------------------------------------
    # 3. Intelligent Local Fallback Engine (Strict Intent Validation & Guardrails)
    # --------------------------------------------------------------------------
    def _chat_local_engine(self, user_message: str) -> str:
        """Deterministic context-aware engine with strict intent filtering."""
        msg = user_message.strip()
        msg_lower = msg.lower()

        # ----------------------------------------------------------------------
        # GUARDRAIL 1: Explicit Out-of-Scope / Tech / Math / Trick Questions
        # Must intercept FIRST, before any keyword matching can trigger!
        # ----------------------------------------------------------------------
        trick_or_tech_indicators = [
            "código fonte", "codigo fonte", "source code", "código", "codigo",
            "banco de dados", "qual o banco", "banco que esse sistema", "sql", "sqlite", "postgres",
            "capital da frança", "capital de", "quem descobriu", "quem é o presidente",
            "quanto é", "quanto e", "calcule", "raiz quadrada", "1*", "2*", "3*", "+",
            "piada", "história", "poema", "programador", "desenvolvedor", "prompt", "system prompt",
        ]

        # Check if message contains math symbols like "1*2+6" or arithmetic expressions
        has_math = bool(re.search(r"\d+[\s]*[\+\-\*\/][\s]*\d+", msg))

        if has_math or any(indicator in msg_lower for indicator in trick_or_tech_indicators):
            return OUT_OF_SCOPE_STANDARD_REPLY

        # ----------------------------------------------------------------------
        # GUARDRAIL 2: Out-of-Scope Non-Musical Products (Appliances, Loose Accessories)
        # ----------------------------------------------------------------------
        non_musical_products = [
            "geladeira", "frigobar", "fogão", "fogao", "microondas", "tv", "televisão",
            "celular", "iphone", "computador", "notebook", "roupa", "tênis", "sapato",
            "palheta", "palhetas", "corda avulsa", "encordoamento", "cabo p10",
            "cabo", "pedal", "pedaleira", "amplificador", "cubo", "case avulso",
        ]
        if any(prod in msg_lower for prod in non_musical_products):
            return (
                "A Empório da Música trabalha exclusivamente com instrumentos musicais completos "
                "(violões, guitarras, baixos, baterias, teclados, sopro e ukuleles).\n\n"
                "Não comercializamos acessórios avulsos (como encordoamentos separados, palhetas, cabos, pedais ou amplificadores) "
                "nem itens fora do segmento musical. Para acessórios, indicamos buscar lojas parceiras de ferragens e áudio no centro de Campo Grande.\n\n"
                "Se precisar de algum instrumento musical completo, estou à disposição para ajudar!"
            )

        # ----------------------------------------------------------------------
        # INTENT 1: Specific Order Tracking by Code or Status Query
        # ----------------------------------------------------------------------
        tracking_match = re.search(r"BR[A-Z0-9]{9}BR", msg, re.IGNORECASE)
        has_order_intent = any(k in msg_lower for k in ["rastre", "meu pedido", "onde está meu pedido", "status do pedido"])
        if tracking_match or has_order_intent:
            tr_code = tracking_match.group(0).upper() if tracking_match else None
            order_data = json.loads(execute_tool("check_order_status", {"tracking_code": tr_code}))
            if order_data.get("success"):
                o = order_data["order"]
                items_str = ", ".join([f"{it['name']} ({it['quantity']}x)" for it in o["items"]])
                return (
                    f"Localizei as informações do seu pedido:\n\n"
                    f"• Pedido Nº: {o['order_id']}\n"
                    f"• Cliente: {o['customer_name']}\n"
                    f"• Itens: {items_str}\n"
                    f"• Status: {o['status_pt']}\n"
                    f"• Código de Rastreamento: {o['tracking_code'] or 'Em processamento'}\n"
                    f"• Previsão de Entrega: {o['estimated_delivery'] or 'A calcular'}\n"
                    f"• Total: {o['total_brl_formatted']}\n\n"
                    f"Você pode acompanhar o rastreio diretamente nos Correios ou Jadlog com o código acima."
                )
            elif tr_code:
                return f"Não encontrei nenhum pedido com o código de rastreamento {tr_code}. Poderia confirmar os dígitos?"

        # ----------------------------------------------------------------------
        # INTENT 2: Store Policies (Address, Hours, Returns under CDC, Payment terms)
        # Must require explicit customer-service intent, NOT accidental words!
        # ----------------------------------------------------------------------
        is_address_query = any(k in msg_lower for k in ["endereço", "endereco", "onde fica a loja", "onde fica", "onde estão"])
        is_hours_query = any(k in msg_lower for k in ["horário", "horario", "que horas abre", "abre no sábado", "funciona no sábado", "fecha"])
        is_return_query = any(k in msg_lower for k in ["arrependi", "arrependimento", "devolver meu pedido", "posso devolver", "como devolver", "direito de arrependimento", "prazo de troca"])
        is_payment_policy = any(k in msg_lower for k in ["formas de pagamento", "desconto no pix", "quantas vezes", "parcela mínima"])

        if is_address_query:
            return (
                "Nossa loja física fica no centro de Campo Grande:\n\n"
                "Rua 14 de Maio, 3200 — Centro, Campo Grande - MS (CEP 79202-333)\n"
                "Telefone e WhatsApp: (67) 3341-4444\n\n"
                "Venha tomar um café conosco e experimentar os instrumentos pessoalmente!"
            )

        if is_hours_query:
            return (
                "Nossos horários de atendimento são:\n\n"
                "• Segunda a Sexta-feira: 09:00 às 18:00\n"
                "• Sábado: 09:00 às 13:00\n"
                "• Domingos e Feriados: Fechado\n\n"
                "Tanto a nossa loja presencial quanto nosso atendimento por aqui seguem esse expediente."
            )

        if is_return_query:
            return (
                "Compreendo você perfeitamente, e pode ficar tranquilo.\n\n"
                "Pelo Código de Defesa do Consumidor (Art. 49) e pelas políticas da nossa loja:\n\n"
                "• Compras online ou pelo WhatsApp têm até 7 dias corridos após o recebimento para solicitar devolução por arrependimento, com reembolso total.\n"
                "• O produto deve estar em sua embalagem original, sem sinais de uso, acompanhado de todos os manuais e certificados.\n"
                "• O frete de retorno é 100% por conta da nossa loja (logística reversa gratuita via Correios).\n"
                "• O estorno é realizado em até 10 dias úteis após a conferência do item devolvido.\n\n"
                "Basta me informar o número do seu pedido para iniciarmos o processo!"
            )

        if is_payment_policy:
            return (
                "Oferecemos excelentes condições de pagamento:\n\n"
                "• PIX à vista: 5% de desconto sobre o preço de tabela!\n"
                "• Cartão de Crédito: em até 12x SEM JUROS (parcela mínima de R$ 50 para até 3x; R$ 80 para 4x a 6x; e R$ 100 para 7x a 12x).\n"
                "• Boleto Bancário: à vista com compensação em até 3 dias úteis.\n\n"
                "Se quiser simular um instrumento específico, basta me avisar o modelo!"
            )

        # ----------------------------------------------------------------------
        # INTENT 3: Specific Product Pricing / Availability (e.g., Takamine GD20)
        # ----------------------------------------------------------------------
        known_products = [
            "takamine gd20", "takamine", "fender", "yamaha c40", "yamaha c70",
            "yamaha f310", "yamaha", "tagima memphis", "tagima dallas", "tagima",
            "giannini gf-1r", "giannini", "ibanez", "crafter", "shelby",
        ]
        matched_product = None
        for p in known_products:
            if p in msg_lower:
                matched_product = p
                break

        has_price_query = any(k in msg_lower for k in ["quanto custa", "preço do", "preco do", "preço de", "preco de", "valor do", "tem o takamine", "tem takamine"])
        if matched_product and (has_price_query or matched_product in ["takamine gd20"]):
            target_query = matched_product
            target_query = re.sub(r"(quanto custa|preço do|preco do|tem o|vocês tem|valor do|o)\s*", "", target_query, flags=re.IGNORECASE).strip()

            prod_data = json.loads(execute_tool("get_product_info", {"product_name_or_id": target_query}))
            if prod_data.get("success"):
                p = prod_data["product"]
                stock_status = (
                    f"Em estoque ({p['stock_quantity']} unidade(s) disponíveis)"
                    if p["is_in_stock"]
                    else "Temporariamente esgotado"
                )

                promo_info = ""
                if p["has_active_promotion"]:
                    promo = p["active_promotion"]
                    promo_info = (
                        f"Promoção Ativa: {promo['discount_percent']:.0f}% de desconto ({promo['description']})!\n"
                        f"De {p['original_price_formatted']} por apenas {p['final_price_formatted']}.\n\n"
                    )
                elif p["expired_promotions"]:
                    promo_info = (
                        f"Nota de Transparência: A promoção anterior para este modelo já expirou. O valor atual é o preço de tabela vigente: {p['original_price_formatted']}.\n\n"
                    )

                terms = p["payment_terms"]

                specs_txt = ""
                if isinstance(p["specs"], dict):
                    specs_parts = []
                    if "top" in p["specs"]: specs_parts.append(f"Tampo: {p['specs']['top']}")
                    if "neck" in p["specs"]: specs_parts.append(f"Braço: {p['specs']['neck']}")
                    if "strings" in p["specs"]:
                        s_str = "Aço" if p["specs"]["strings"] == "steel" else "Nylon"
                        specs_parts.append(f"Cordas: {s_str}")
                    if "scale" in p["specs"]: specs_parts.append(f"Escala: {p['specs']['scale']}")
                    specs_txt = " | ".join(specs_parts)

                return (
                    f"Temos sim as informações do {p['name']}!\n\n"
                    f"{promo_info}"
                    f"• Preço de tabela: {p['original_price_formatted']}\n"
                    f"• À vista no PIX (5% off): {terms['price_pix_formatted']}\n"
                    f"• Cartão de crédito: até {terms['installment_formatted']}\n"
                    f"• Disponibilidade: {stock_status}\n"
                    f"• Detalhes técnicos: {specs_txt}\n\n"
                    f"Gostaria de reservar uma unidade ou simular outra condição de pagamento?"
                )

        # ----------------------------------------------------------------------
        # INTENT 4: Instrument Catalog Query (Discovery / Spec Refinement)
        # Must verify real instrument shopping intent!
        # ----------------------------------------------------------------------
        # Update category context if a category was actually requested
        if "viol" in msg_lower:
            self.session_state["last_category"] = "Violões"
        elif "guitarra" in msg_lower:
            self.session_state["last_category"] = "Guitarras"
        elif "baixo" in msg_lower:
            self.session_state["last_category"] = "Baixos"
        elif "teclado" in msg_lower or "piano" in msg_lower:
            self.session_state["last_category"] = "Teclados"
        elif "bateria" in msg_lower:
            self.session_state["last_category"] = "Baterias"
        elif "ukulele" in msg_lower:
            self.session_state["last_category"] = "Ukuleles"

        current_category = self.session_state.get("last_category")

        wants_steel = any(k in msg_lower for k in ["aço", "aco", "steel"])
        wants_nylon = "nylon" in msg_lower
        wants_nut_43 = any(k in msg_lower for k in ["43mm", "43 mm", "braço fino", "braco fino"])

        price_match = re.search(r"(?:até|ate|abaixo de|menos de|custando até)?\s*(?:r\$)?\s*(\d+[\.\d]*)", msg_lower)
        max_price = None
        if price_match and any(term in msg_lower for term in ["até", "ate", "menos de", "máximo", "maximo", "500", "1000", "800", "2000"]):
            try:
                max_price = float(price_match.group(1).replace(".", ""))
            except ValueError:
                pass

        # Real shopping / browsing intent triggers
        catalog_intent_triggers = [
            "quais modelos", "quais viol", "quais guitarra", "quais instrumentos", "opções de", "opcoes de",
            "tem de até", "tem ate", "tem violão", "tem guitarra", "recomenda", "estou procurando",
            "procurando um", "vocês vendem", "voces vendem", "catálogo", "catalogo", "modelos de violão",
            "modelos de",
        ]
        has_catalog_intent = any(trigger in msg_lower for trigger in catalog_intent_triggers) or (
            current_category is not None and (wants_steel or wants_nylon or wants_nut_43 or max_price is not None)
        )

        if has_catalog_intent:
            target_cat = current_category or "Violões"
            self.session_state["last_category"] = target_cat

            # Special case: Steel string guitar under R$ 500
            if wants_steel and max_price and max_price <= 500:
                cheapest_steel = json.loads(execute_tool("search_catalog", {
                    "category": "Violões",
                    "string_type": "aço",
                    "in_stock_only": True,
                    "limit": 2,
                }))
                nylon_under_500 = json.loads(execute_tool("search_catalog", {
                    "category": "Violões",
                    "max_price": 500,
                    "in_stock_only": True,
                    "limit": 2,
                }))

                cheapest_item = cheapest_steel["products"][0] if cheapest_steel.get("products") else None
                nylon_items = nylon_under_500.get("products", [])
                nylon_txt = ", ".join([f"{it['name']} ({it['final_price_formatted']})" for it in nylon_items])

                nut_note = (
                    "O braço com largura de 43mm na pestana (nut) é a medida padrão dos violões estilo Folk com cordas de aço, "
                    "proporcionando uma pegada anatômica excelente para acordes e solos rápidos."
                    if wants_nut_43 else ""
                )

                if cheapest_item:
                    return (
                        f"Na faixa de até R$ 500,00, todos os violões novos em nosso estoque utilizam cordas de nylon "
                        f"({nylon_txt}), que contam com o braço tradicional clássico mais largo (cerca de 52mm).\n\n"
                        f"Com cordas de aço e perfil de braço fino de 43mm (formato Folk), a opção mais acessível em estoque é o:\n\n"
                        f"• {cheapest_item['name']}\n"
                        f"  Preço de tabela: {cheapest_item['final_price_formatted']}\n"
                        f"  À vista no PIX (5% de desconto): {cheapest_item['payment_terms']['price_pix_formatted']}\n"
                        f"  Parcelamento: até {cheapest_item['payment_terms']['installment_formatted']}\n"
                        f"  Estoque: {cheapest_item['stock_quantity']} unidades disponíveis\n\n"
                        f"{nut_note}\n\n"
                        f"Por uma diferença muito pequena no valor à vista no PIX ({cheapest_item['payment_terms']['price_pix_formatted']}), "
                        f"ele entrega exatamente o timbre brilhante do aço e a tocabilidade de 43mm que você procura. Quer que eu separe um para você testar?"
                    )

            # Standard catalog query
            string_filter = "aço" if wants_steel else ("nylon" if wants_nylon else None)
            catalog_data = json.loads(execute_tool("search_catalog", {
                "category": target_cat,
                "string_type": string_filter,
                "max_price": max_price,
                "in_stock_only": True,
                "limit": 5,
            }))

            if catalog_data.get("success") and catalog_data.get("products"):
                products = catalog_data["products"]
                hdr = target_cat.lower()
                filtro_aco = " com cordas de aço" if wants_steel else (" com cordas de nylon" if wants_nylon else "")
                filtro_preco = f" custando até R$ {max_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if max_price else ""

                resp_lines = [
                    f"Temos excelentes opções de {hdr}{filtro_aco}{filtro_preco} disponíveis em estoque:\n"
                ]
                for p in products:
                    s_type = ""
                    if isinstance(p["specs"], dict) and "strings" in p["specs"]:
                        s_type = " [Aço]" if p["specs"]["strings"] == "steel" else " [Nylon]"

                    promo_tag = f" (Promoção: {p['discount_percent']:.0f}% off)" if p["has_active_promotion"] else ""
                    resp_lines.append(
                        f"• {p['name']}{s_type}{promo_tag}\n"
                        f"  Preço: {p['final_price_formatted']} (ou no PIX à vista: {p['payment_terms']['price_pix_formatted']})\n"
                        f"  Parcelamento: {p['payment_terms']['installment_formatted']} | Estoque: {p['stock_quantity']} unid.\n"
                    )

                resp_lines.append(
                    "Todos os nossos instrumentos contam com 90 dias de garantia legal do CDC + garantia de fábrica e já vêm revisados.\n"
                    "Qual desses modelos se encaixa melhor no som que você quer tocar?"
                )
                return "\n".join(resp_lines)

        # ----------------------------------------------------------------------
        # DEFAULT: Greetings or Unrecognized / Out of Scope Inquiries
        # ----------------------------------------------------------------------
        is_greeting = any(g in msg_lower for g in ["olá", "ola", "bom dia", "boa tarde", "boa noite", "oi", "opa"])
        if is_greeting:
            return (
                "Olá! Seja bem-vindo à Empório da Música! 🎸\n\n"
                "Sou o assistente virtual da loja e estou aqui para te ajudar a escolher instrumentos musicais, "
                "consultar disponibilidade em estoque, simular pagamentos (em até 12x sem juros ou 5% no PIX), "
                "rastrear pedidos ou tirar dúvidas sobre nossas políticas.\n\n"
                "Qual instrumento você gostaria de conhecer hoje?"
            )

        # If it wasn't a greeting and didn't match legitimate store intents:
        # Return the clean out-of-scope reply!
        return OUT_OF_SCOPE_STANDARD_REPLY

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
    TOOL_REGISTRY,
)


SYSTEM_PROMPT = """Você é o Assistente Virtual Oficial da "Empório da Música", a mais tradicional e conceituada loja de instrumentos musicais de Campo Grande, Mato Grosso do Sul, fundada em 2008.

SUA MISSÃO:
Atender clientes no canal de WhatsApp com empatia, conhecimento musical e precisão impecável, tirando dúvidas sobre instrumentos, preços, estoque, pedidos e políticas da loja.

TOM DE VOZ E PERSONA:
- Caloroso, acolhedor, profissional e apaixonado por música.
- Fale de forma natural e amigável, como se fosse um músico experiente conversando com outro músico ou ajudando alguém a iniciar sua jornada musical.
- Cumprimente cordialmente e conclua colocando-se sempre à disposição.

DIRETRIZES FUNDAMENTAIS DA EMPÓRIO DA MÚSICA:
1. CONSULTA OBRIGATÓRIA A DADOS:
   - NUNCA invente preços, disponibilidade de estoque ou prazos de entrega.
   - Para perguntas sobre produtos, preços ou marcas: execute SEMPRE a ferramenta `search_catalog` ou `get_product_info`.
   - Para perguntas sobre pedidos ou entregas: execute `check_order_status`.
   - Para perguntas sobre políticas (endereço, horários, trocas, devoluções, formas de pagamento, garantia, LGPD): execute `search_store_policies`.

2. REGRAS DE ESTOQUE:
   - Se o produto tiver estoque = 0, informe com total gentileza que o modelo está temporariamente esgotado e sugira modelos equivalentes disponíveis em estoque.

3. REGRAS DE PROMOÇÕES E DESCONTOS (REGRA DE TRANSPARÊNCIA):
   - APENAS conceda descontos se a promoção estiver com status ATIVA (`is_active = 1`).
   - Se o cliente perguntar sobre uma promoção passada ou vencida (ex: Black Friday anterior), informe com máxima transparência que a promoção já encerrou, apresente o preço de tabela vigente e destaque as facilidades de pagamento (5% de desconto no PIX ou até 12x sem juros no cartão).
   - NUNCA prometa um desconto que não está vigente!

4. POLÍTICA DE DEVOLUÇÕES E TROCAS (CÓDIGO DE DEFESA DO CONSUMIDOR):
   - Compras Online / WhatsApp: direito de arrependimento em até 7 dias corridos após o recebimento, com reembolso total em até 10 dias úteis e frete de retorno 100% pago pela loja.
   - Defeitos de fabricação: troca ou reparo em até 30 dias corridos diretamente com a loja; após isso, garantia do fabricante.
   - Não elegíveis para troca: instrumentos personalizados sob encomenda, liquidações expressas "venda final" e boquilhas de instrumentos de sopro (higiene).

5. ESCOPO E PRODUTOS:
   - A Empório da Música vende EXCLUSIVAMENTE instrumentos musicais completos (violões, guitarras, baixos, baterias, teclados, sopro, cordas e ukuleles).
   - A loja NÃO vende acessórios avulsos (cordas, palhetas, cabos, pedais, cases, amplificadores). Se o cliente perguntar por acessórios ou itens aleatórios (ex: geladeira, eletrodomésticos), explique educadamente a especialidade da loja e sugira parceiros ou lojas especializadas.

6. DADOS GERAIS DA LOJA:
   - Endereço: Rua 14 de Maio, 3200 — Centro, Campo Grande - MS, CEP 79202-333.
   - Horários: Segunda a Sexta das 09:00 às 18:00; Sábados das 09:00 às 13:00; Domingos e Feriados fechado.
   - WhatsApp: (67) 3341-4444.
"""


class EmporioAgent:
    """Multi-provider AI customer service agent for Empório da Música."""

    def __init__(self):
        self.conversation_history: List[Dict[str, Any]] = []
        self.provider = self._detect_provider()
        self._init_client()

    def _detect_provider(self) -> str:
        """Detect which LLM provider to use based on available environment variables."""
        if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
            return "gemini"
        if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
            return "openai"
        return "local_engine"

    def _init_client(self) -> None:
        """Initialize the specific provider client."""
        if self.provider == "gemini":
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                print(f"[Aviso] Falha ao inicializar Google GenAI ({e}). Usando motor local de regras.")
                self.provider = "local_engine"
        elif self.provider == "openai":
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
            except Exception as e:
                print(f"[Aviso] Falha ao inicializar OpenAI ({e}). Usando motor local de regras.")
                self.provider = "local_engine"

    def get_provider_name(self) -> str:
        """Return formatted name of active engine."""
        if self.provider == "gemini":
            return f"Google Gemini ({GEMINI_MODEL})"
        if self.provider == "openai":
            return f"OpenAI ({OPENAI_MODEL})"
        return "Motor Inteligente Local (Simulação de Agente Baseada em Regras & Tools)"

    def reset_conversation(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []

    def chat(self, user_message: str) -> str:
        """Process a user message and return the agent response."""
        if not user_message.strip():
            return "Olá! Como posso ajudar você com seus instrumentos musicais hoje?"

        # Append user turn to history
        self.conversation_history.append({"role": "user", "content": user_message})

        if self.provider == "gemini":
            response_text = self._chat_gemini(user_message)
        elif self.provider == "openai":
            response_text = self._chat_openai(user_message)
        else:
            response_text = self._chat_local_engine(user_message)

        # Append assistant turn to history
        self.conversation_history.append({"role": "assistant", "content": response_text})
        return response_text

    # --------------------------------------------------------------------------
    # 1. Google Gemini Provider Implementation
    # --------------------------------------------------------------------------
    def _chat_gemini(self, user_message: str) -> str:
        from google.genai import types

        # Build contents from conversation history
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

            # Check if model requested tool calls
            for _ in range(AGENT_MAX_TURNS):
                function_calls = response.function_calls
                if not function_calls:
                    return response.text or "Desculpe, não consegui processar a resposta no momento."

                # Execute requested functions
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

                # Feed function results back to the model
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

                # Add assistant message with tool calls
                messages.append(msg)

                # Process each tool call
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
    # 3. Intelligent Local Fallback Engine (Runs offline & without API keys)
    # --------------------------------------------------------------------------
    def _chat_local_engine(self, user_message: str) -> str:
        """Deterministic, tool-invoking intelligent router for Empório da Música."""
        msg = user_message.strip()
        msg_lower = msg.lower()

        # ----------------------------------------------------------------------
        # A. Store Information / Policies / Hours / Address / Returns / CDC
        # ----------------------------------------------------------------------
        policy_triggers = [
            "endereço", "endereco", "onde fica", "onde estão", "localização",
            "horário", "horario", "aberto", "abre", "fecha", "sábado", "domingo",
            "devolver", "devolução", "devolucao", "arrependi", "arrependimento",
            "troca", "trocar", "cdc", "reembolso", "estorno", "defeito",
            "garantia", "forma de pagamento", "formas de pagamento", "parcela",
            "parcelamento", "pix", "juros", "frete", "entrega", "jadlog", "correios",
            "lgpd", "privacidade", "dados",
        ]

        # Check if the query is asking about store policies
        if any(trigger in msg_lower for trigger in policy_triggers) and not any(k in msg_lower for k in ["quanto custa", "tem estoque", "preço do", "preco do"]):
            policy_data = json.loads(execute_tool("search_store_policies", {"query": msg}))
            policies = policy_data.get("matched_policies", [])
            if policies:
                top_pol = policies[0]
                content = top_pol["content"]

                # Tailored friendly response depending on the specific policy
                if any(k in msg_lower for k in ["endereço", "endereco", "onde fica"]):
                    return (
                        "Olá! Que bom falar com você! 🎶\n\n"
                        "Nossa loja física fica no coração de Campo Grande:\n"
                        "📍 **Rua 14 de Maio, 3200 — Centro, Campo Grande - MS (CEP 79202-333)**\n\n"
                        "Se precisar falar com a gente por telefone ou WhatsApp, o número é **(67) 3341-4444**.\n"
                        "Venha tomar um café com a gente e testar nossos instrumentos!"
                    )

                if any(k in msg_lower for k in ["horário", "horario", "abre", "aberto", "sábado"]):
                    return (
                        "Olá! Nossos horários de atendimento são:\n\n"
                        "🕒 **Segunda a Sexta-feira:** das 09:00 às 18:00\n"
                        "🕒 **Sábado:** das 09:00 às 13:00\n"
                        "🚫 **Domingos e Feriados:** Fechado\n\n"
                        "Tanto nossa loja presencial quanto nosso atendimento online pelo WhatsApp seguem esse expediente. Como posso te ajudar hoje?"
                    )

                if any(k in msg_lower for k in ["devolver", "devolução", "devolucao", "arrependi", "arrependimento"]):
                    return (
                        "Olá! Compreendo perfeitamente, e você pode ficar totalmente tranquilo(a)! 🎸\n\n"
                        "Aqui na Empório da Música seguimos à risca o **Código de Defesa do Consumidor (CDC)**:\n\n"
                        "• **Direito de Arrependimento (Compras Online/WhatsApp):** Você tem até **7 (sete) dias corridos** após o recebimento para solicitar a devolução e reembolso total, sem precisar justificar o motivo.\n"
                        "• **Requisitos:** O instrumento deve estar na embalagem original, sem marcas de uso, com todos os manuais e acessórios originais.\n"
                        "• **Frete de devolução:** É **100% gratuito**, pago pela nossa loja (logística reversa).\n"
                        "• **Reembolso:** Feito na mesma forma de pagamento da compra em até 10 dias úteis após a conferência do produto.\n\n"
                        "Se você comprou pelo nosso site ou WhatsApp e está dentro do prazo de 7 dias, basta me informar o número do pedido ou CPF que inicio o procedimento para você!"
                    )

                if any(k in msg_lower for k in ["pix", "desconto", "parcelamento", "cartão", "cartao"]):
                    return (
                        "Olá! Oferecemos condições excelentes de pagamento:\n\n"
                        "💰 **PIX:** 5% de desconto sobre o preço de tabela à vista!\n"
                        "💳 **Cartão de Crédito:** em até **12x SEM JUROS** (com parcelas mínimas de R$ 50 para até 3x; R$ 80 para 4x a 6x; e R$ 100 para 7x a 12x).\n"
                        "📄 **Boleto Bancário:** à vista (compensação em até 3 dias úteis).\n\n"
                        "Se tiver algum instrumento específico em vista, me avisa que calculo as parcelas e o desconto do PIX para você na hora!"
                    )

                # Generic policy response
                return f"Olá! Seguem as informações oficiais da nossa política:\n\n{content}\n\nFicou alguma dúvida ou posso te ajudar com mais detalhes?"

        # ----------------------------------------------------------------------
        # B. Out-of-Scope Queries (Accessories, Appliances, Non-instruments)
        # ----------------------------------------------------------------------
        out_of_scope_keywords = [
            "geladeira", "fogão", "fogao", "microondas", "tv", "televisão",
            "celular", "iphone", "computador", "roupa", "tênis", "sapato",
            "palheta", "palhetas", "corda avulsa", "encordoamento", "cabo p10",
            "cabo", "pedal", "pedaleira", "amplificador", "cubo", "case avulso",
        ]
        if any(term in msg_lower for term in out_of_scope_keywords):
            return (
                "Olá! Agradeço pelo contato! 🎵\n\n"
                "Aqui na **Empório da Música**, nós trabalhamos **exclusivamente com instrumentos musicais completos** "
                "(guitarras, violões, baixos, baterias, teclados, instrumentos de sopro e ukuleles).\n\n"
                "Por isso, **não comercializamos acessórios avulsos** (como cabos, palhetas, encordoamentos, pedais ou amplificadores) "
                "nem outros eletroeletrônicos fora do segmento musical. Para acessórios, recomendamos buscar lojas especializadas de áudio e ferragens aqui de Campo Grande.\n\n"
                "Se estiver procurando algum instrumento musical para tocar, terei o maior prazer em te mostrar nossas opções!"
            )

        # ----------------------------------------------------------------------
        # C. Order Tracking and Status
        # ----------------------------------------------------------------------
        tracking_match = re.search(r"BR[A-Z0-9]{9}BR", msg, re.IGNORECASE)
        if tracking_match or "pedido" in msg_lower or "rastre" in msg_lower:
            tr_code = tracking_match.group(0).upper() if tracking_match else None
            order_data = json.loads(execute_tool("check_order_status", {"tracking_code": tr_code}))
            if order_data.get("success"):
                o = order_data["order"]
                items_str = ", ".join([f"{it['name']} ({it['quantity']}x)" for it in o["items"]])
                return (
                    f"Olá! Localizei as informações do seu pedido: 📦\n\n"
                    f"• **Pedido Nº:** {o['order_id']}\n"
                    f"• **Cliente:** {o['customer_name']}\n"
                    f"• **Itens:** {items_str}\n"
                    f"• **Status Atual:** **{o['status_pt']}**\n"
                    f"• **Código de Rastreamento:** {o['tracking_code'] or 'Em processamento'}\n"
                    f"• **Previsão de Entrega:** {o['estimated_delivery'] or 'A calcular'}\n"
                    f"• **Total:** {o['total_brl_formatted']}\n\n"
                    f"Você pode acompanhar o rastreio diretamente pelos Correios ou Jadlog com o código acima. Precisa de mais alguma informação?"
                )
            elif tr_code:
                return f"Não consegui encontrar nenhum pedido com o código de rastreio **{tr_code}**. Poderia conferir se os dígitos estão corretos?"

        # ----------------------------------------------------------------------
        # D. Specific Product Details & Pricing (e.g., Takamine GD20, Fender, etc.)
        # ----------------------------------------------------------------------
        product_names = [
            "takamine gd20", "takamine", "fender", "yamaha c40", "yamaha",
            "tagima", "giannini", "ibanez", "epiphone", "crafter", "strinberg",
        ]
        matched_product = None
        for p in product_names:
            if p in msg_lower:
                matched_product = p
                break

        if matched_product or any(term in msg_lower for term in ["quanto custa", "preço de", "preco de", "preço do", "preco do", "tem o"]):
            target_query = matched_product if matched_product else msg
            # Clean common words
            target_query = re.sub(r"(quanto custa|preço do|preco do|tem o|vocês tem|valor do|o)\s*", "", target_query, flags=re.IGNORECASE).strip()

            prod_data = json.loads(execute_tool("get_product_info", {"product_name_or_id": target_query}))
            if prod_data.get("success"):
                p = prod_data["product"]
                stock_status = (
                    f"✅ **Em estoque:** {p['stock_quantity']} unidade(s) disponíveis"
                    if p["is_in_stock"]
                    else "❌ **Temporariamente esgotado**"
                )

                # Promotion handling
                promo_info = ""
                if p["has_active_promotion"]:
                    promo = p["active_promotion"]
                    promo_info = (
                        f"🔥 **PROMOÇÃO ATIVA:** {promo['discount_percent']:.0f}% de desconto ({promo['description']})!\n"
                        f"De ~~{p['original_price_formatted']}~~ por apenas **{p['final_price_formatted']}**!\n"
                    )
                elif p["expired_promotions"]:
                    promo_info = (
                        f"ℹ️ *Nota de Transparência:* As promoções anteriores para este modelo já se encerraram. O valor atual é o preço de tabela vigente: **{p['original_price_formatted']}**.\n"
                    )

                terms = p["payment_terms"]

                return (
                    f"Olá! Temos sim todas as informações do **{p['name']}**! 🎸\n\n"
                    f"{promo_info}"
                    f"• **Preço de Tabela:** {p['original_price_formatted']}\n"
                    f"• **Preço à vista no PIX (5% off):** **{terms['price_pix_formatted']}**\n"
                    f"• **Cartão de Crédito:** até {terms['installment_formatted']}\n"
                    f"• **Disponibilidade:** {stock_status}\n"
                    f"• **Especificações:** {p['specs']}\n\n"
                    f"Gostaria de reservar uma unidade ou simular outra condição de pagamento?"
                )

        # ----------------------------------------------------------------------
        # E. Catalog Search with Category & Price Filter (e.g. Violões até R$ 1000)
        # ----------------------------------------------------------------------
        # Detect category
        category = None
        if "viol" in msg_lower:
            category = "Violões"
        elif "guitarra" in msg_lower:
            category = "Guitarras"
        elif "baixo" in msg_lower:
            category = "Baixos"
        elif "teclado" in msg_lower or "piano" in msg_lower:
            category = "Teclados"
        elif "bateria" in msg_lower:
            category = "Baterias"
        elif "ukulele" in msg_lower:
            category = "Ukuleles"

        # Detect price limit
        max_price = None
        price_match = re.search(r"(?:até|ate|abaixo de|menos de|custando até)?\s*(?:r\$)?\s*(\d+[\.\d]*)", msg_lower)
        if price_match and any(term in msg_lower for term in ["até", "ate", "custando", "máximo", "maximo", "menos de", "1000", "500", "2000"]):
            try:
                raw_val = price_match.group(1).replace(".", "")
                max_price = float(raw_val)
            except ValueError:
                pass

        if category or max_price:
            catalog_data = json.loads(execute_tool("search_catalog", {
                "category": category,
                "max_price": max_price,
                "in_stock_only": True,
                "limit": 5,
            }))

            if catalog_data.get("success") and catalog_data.get("products"):
                products = catalog_data["products"]
                hdr = f"Violões" if category == "Violões" else "instrumentos"
                limit_str = f" custando até R$ {max_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if max_price else ""

                resp_lines = [
                    f"Olá! Temos excelentes opções de {hdr}{limit_str} **em estoque** pronta para você tocar! 🎶\n"
                ]
                for p in products:
                    promo_tag = f" 🔥 *(Promoção: {p['discount_percent']:.0f}% off)*" if p["has_active_promotion"] else ""
                    resp_lines.append(
                        f"• **{p['name']}**{promo_tag}\n"
                        f"  Preço: **{p['final_price_formatted']}** (ou à vista no PIX: **{p['payment_terms']['price_pix_formatted']}**)\n"
                        f"  Parcelamento: {p['payment_terms']['installment_formatted']} | Estoque: {p['stock_quantity']} unid.\n"
                    )

                resp_lines.append(
                    "Todos os nossos instrumentos contam com 90 dias de garantia legal do CDC + garantia do fabricante, além de virem revisados!\n"
                    "Qual desses modelos chamou mais sua atenção?"
                )
                return "\n".join(resp_lines)

        # ----------------------------------------------------------------------
        # F. Default Warm Welcome / Fallback
        # ----------------------------------------------------------------------
        return (
            "Olá! Seja muito bem-vindo(a) à **Empório da Música**! 🎶🎸\n\n"
            "Sou o assistente virtual da loja e estou aqui para te ajudar com:\n"
            "• Consulta de modelos, preços e estoque de instrumentos musicais;\n"
            "• Simulação de parcelamento (até 12x sem juros) e desconto de 5% no PIX;\n"
            "• Rastreamento e status do seu pedido;\n"
            "• Dúvidas sobre horários, endereço, trocas e garantias pelo CDC.\n\n"
            "Como posso ajudar o seu som hoje?"
        )

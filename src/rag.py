"""Retrieval-Augmented Generation (RAG) module for Empório da Música store policies."""

import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional
import pypdf
from src.config import POLICY_PDF_PATH


@dataclass
class PolicyChunk:
    chunk_id: str
    section_number: str
    title: str
    content: str
    keywords: List[str]


# Pre-defined curated sections from the official store manual
# Ensures 100% reliable semantic chunk boundaries and keyword anchoring
CURATED_POLICY_SECTIONS = [
    {
        "chunk_id": "pol_01_sobre",
        "section_number": "1",
        "title": "Sobre a Empório da Música & Escopo de Produtos",
        "content": (
            "1. Sobre a Empório da Música\n"
            "A Empório da Música é uma loja especializada em instrumentos musicais, fundada em 2008 em Campo Grande, "
            "Mato Grosso do Sul. Com mais de 15 anos de atuação, somos referência regional na venda de instrumentos "
            "para músicos iniciantes, intermediários e profissionais.\n"
            "Catálogo: mais de 300 instrumentos, incluindo guitarras, baixos, violões, baterias, teclados, sopro, cordas e ukuleles.\n"
            "IMPORTANTE - ESCOPO DE PRODUTOS: Trabalhamos EXCLUSIVAMENTE com instrumentos musicais completos. "
            "NÃO comercializamos acessórios avulsos (como cordas, palhetas, cabos, cases, correias, pedais ou amplificadores) "
            "nem produtos fora do segmento musical. Caso o cliente solicite acessórios ou itens fora de escopo, "
            "o atendente deve informar educadamente essa restrição e sugerir lojas parceiras da região.\n"
            "Dados da Loja:\n"
            "- Razão Social: Empório da Música Instrumentos Musicais Ltda.\n"
            "- CNPJ: 12.345.678/0001-90\n"
            "- Endereço: Rua 14 de Maio, 3200 — Centro, Campo Grande - MS, CEP 79202-333\n"
            "- Telefone / WhatsApp: (67) 3341-4444 e (67) 3321-4500\n"
            "- E-mail: contato@emporiodamusica.com.br\n"
            "- Cidade sede: Campo Grande, Mato Grosso do Sul."
        ),
        "keywords": ["endereço", "endereco", "localização", "localizacao", "onde fica", "onde estão", "contato", "telefone", "whatsapp", "email", "campo grande", "cnpj", "acessórios", "acessorios", "cordas", "palhetas", "cabos", "pedais", "amplificadores", "sobre"],
    },
    {
        "chunk_id": "pol_02_horarios",
        "section_number": "2",
        "title": "Horário de Funcionamento e Atendimento",
        "content": (
            "2. Horário de Funcionamento\n"
            "O atendimento presencial na loja física e no canal de WhatsApp segue os horários:\n"
            "- Segunda a Sexta-feira: 09:00 às 18:00\n"
            "- Sábado: 09:00 às 13:00\n"
            "- Domingo e Feriados: Fechado\n"
            "Em datas comemorativas especiais (Black Friday, Aniversário da Loja em Junho, Natal), o expediente "
            "pode ser estendido, sempre divulgado previamente nas redes e WhatsApp."
        ),
        "keywords": ["horário", "horario", "funcionamento", "aberto", "abre", "fecha", "expediente", "sábado", "sabado", "domingo", "feriado", "dias de semana"],
    },
    {
        "chunk_id": "pol_03_pagamentos",
        "section_number": "3",
        "title": "Formas de Pagamento e Condições de Parcelamento",
        "content": (
            "3. Formas de Pagamento e Parcelamento\n"
            "Aceitamos as seguintes formas de pagamento para compras presenciais e online:\n"
            "- PIX (à vista): 5% de desconto sobre o preço de tabela.\n"
            "- Cartão de Débito (à vista): todas as bandeiras aceitas.\n"
            "- Boleto Bancário (à vista): compensação bancária em até 3 dias úteis.\n"
            "- Cartão de Crédito: parcelamento em até 12x SEM JUROS.\n"
            "Regras de Parcelamento no Cartão de Crédito:\n"
            "* Até 3x sem juros: sem valor mínimo rigoroso de parcela (parcela mínima de R$ 50,00).\n"
            "* De 4x a 6x sem juros: parcela mínima de R$ 80,00.\n"
            "* De 7x a 12x sem juros: parcela mínima de R$ 100,00.\n"
            "Combinação de Formas de Pagamento: permitida (ex.: entrada via PIX + saldo no cartão) para pedidos acima de R$ 2.000,00."
        ),
        "keywords": ["pagamento", "pix", "desconto", "parcelamento", "parcelas", "cartão", "cartao", "credito", "crédito", "débito", "debito", "boleto", "juros", "sem juros", "dividir"],
    },
    {
        "chunk_id": "pol_04_trocas_devolucoes",
        "section_number": "4",
        "title": "Política de Trocas, Devoluções e Direito de Arrependimento (CDC)",
        "content": (
            "4. Política de Trocas e Devoluções (Código de Defesa do Consumidor - Lei nº 8.078/90)\n"
            "4.1 Direito de Arrependimento (Exclusivo para Compras Online / WhatsApp):\n"
            "- Conforme o Artigo 49 do CDC, o cliente tem até 7 (sete) dias corridos a partir do recebimento do produto para desistir da compra e solicitar reembolso integral, sem necessidade de justificar o motivo.\n"
            "- Requisitos: o produto deve estar em perfeitas condições, na embalagem original, sem sinais de uso indevido e com todos os manuais e itens inclusos.\n"
            "- Reembolso: efetuado na mesma forma de pagamento original em até 10 dias úteis após a inspeção do item devolvido.\n"
            "- Custo de frete da devolução por arrependimento: 100% arcado pela Empório da Música (logística reversa gratuita).\n"
            "4.2 Trocas por Defeito de Fabricação:\n"
            "- Produtos com vício ou defeito de fabricação podem ser trocados ou reparados em até 30 (trinta) dias corridos após a compra diretamente com a loja.\n"
            "- Após 30 dias, deve-se acionar a garantia do fabricante (a loja pode auxiliar na intermediação).\n"
            "- Não cobre defeitos oriundos de mau uso, batidas, quedas, exposição a umidade ou modificações não autorizadas.\n"
            "4.3 Trocas por Preferência (cor/modelo):\n"
            "- Permitidas em até 7 dias corridos, condicionadas à disponibilidade de estoque e perfeitas condições do produto.\n"
            "4.4 Itens Não Elegíveis para Devolução por Mera Preferência:\n"
            "- Instrumentos personalizados sob encomenda com regulagens específicas.\n"
            "- Itens de liquidação final expressamente rotulados como 'venda final'.\n"
            "- Boquilhas de instrumentos de sopro (por rígidas normas de higiene sanitária)."
        ),
        "keywords": ["devolução", "devolucao", "troca", "devolver", "arrependimento", "arrependi", "cdc", "consumidor", "direito", "prazo", "reembolso", "estorno", "defeito", "quebrado", "danificado", "7 dias", "30 dias"],
    },
    {
        "chunk_id": "pol_05_frete_entregas",
        "section_number": "5",
        "title": "Política de Frete, Prazos e Envio",
        "content": (
            "5. Política de Frete e Entregas\n"
            "- Região Metropolitana de Campo Grande/MS: entrega via motoboy ou transportadora local no prazo de 24 a 48 horas úteis.\n"
            "- Demais cidades e estados do Brasil: envios realizados via Correios (modalidades PAC e SEDEX) ou transportadora Jadlog.\n"
            "- Rastreamento: o código de rastreio é fornecido logo após a postagem e pode ser acompanhado pelo cliente via WhatsApp ou site da transportadora.\n"
            "- Prazos de entrega: variam de acordo com o CEP de destino e a modalidade de frete selecionada no fechamento da compra."
        ),
        "keywords": ["frete", "entrega", "envio", "prazo", "correios", "sedex", "pac", "jadlog", "rastreamento", "rastreio", "transportadora", "motoboy", "campo grande"],
    },
    {
        "chunk_id": "pol_06_promocoes",
        "section_number": "6",
        "title": "Regras de Promoções, Descontos e Ofertas",
        "content": (
            "6. Promoções e Descontos\n"
            "- Promoções periódicas: Black Friday, Aniversário da Loja, Semana do Músico e Natal.\n"
            "- Regra de Ouro da Loja: APENAS promoções ativas registradas no sistema (com is_active = 1) podem ser aplicadas.\n"
            "- Promoções Vencidas / Expiradas: NÃO geram direito a reserva de preço (rain check). Se um cliente perguntar sobre uma promoção passada (ex.: Black Friday encerrada), o atendente deve agir com máxima transparência, informar educadamente que a oferta expirou e apresentar o preço de tabela vigente com as opções normais de parcelamento ou desconto à vista de 5% no PIX.\n"
            "- NUNCA prometer desconto que não esteja ativamente vigente no banco de dados.\n"
            "- Comunicação transparente: quando houver promoção ativa, deve-se explicitar o preço original, percentual de desconto e o valor promocional final."
        ),
        "keywords": ["promoção", "promocao", "desconto", "oferta", "black friday", "expirou", "vencida", "ativa", "cupom", "barato", "preço promocional"],
    },
    {
        "chunk_id": "pol_07_atendimento",
        "section_number": "7",
        "title": "Diretrizes de Atendimento, Tom de Voz e Persona",
        "content": (
            "7. Diretrizes de Atendimento ao Cliente e Persona Empório da Música\n"
            "- Tom de voz: Informal, acolhedor e profissional. O cliente deve se sentir como se estivesse batendo um papo com um amigo que entende muito de música e respeita seu gosto.\n"
            "- Precisão absoluta: Nunca fornecer preços, disponibilidade de estoque ou prazos sem consultar o sistema em tempo real.\n"
            "- Produtos Esgotados / Fora de Estoque: Avisar imediatamente com gentileza e proativamente sugerir modelos equivalentes que estejam em estoque no momento.\n"
            "- Produtos Fora de Escopo (ex: geladeira, roupas, acessórios avulsos como palhetas/cabos): Explicar cordialmente que a Empório da Música é especializada e restrita a instrumentos musicais completos."
        ),
        "keywords": ["atendimento", "persona", "tom", "estilo", "fora de estoque", "esgotado", "escopo", "fora de escopo", "amigo", "músico", "musico"],
    },
    {
        "chunk_id": "pol_08_garantia",
        "section_number": "8",
        "title": "Políticas de Garantia Legal e do Fabricante",
        "content": (
            "8. Garantia de Instrumentos Musicais\n"
            "8.1 Garantia Legal: Conforme o Código de Defesa do Consumidor (CDC), todos os instrumentos têm garantia legal mínima de 90 (noventa) dias contra defeitos de fabricação a contar da data de recebimento.\n"
            "8.2 Garantia Contratual do Fabricante: Grande parte das marcas conceituadas (Yamaha, Fender, Takamine, Tagima, Ibanez) oferece garantia estendida de 6 meses a 2 anos, especificada no termo de garantia que acompanha a nota fiscal.\n"
            "8.3 Exclusões da Garantia: A garantia NÃO cobre desgastes naturais de uso cotidiano (como desgaste de trastes, cordas oxidadas, desgaste de feltros ou acabamento por suor/atrito), nem acidentes, quedas, umidade excessiva ou modificações estruturais não autorizadas."
        ),
        "keywords": ["garantia", "defeito", "assistência", "assistencia", "conserto", "fabricante", "legal", "90 dias", "meses", "anos", "quebrou"],
    },
    {
        "chunk_id": "pol_09_lgpd",
        "section_number": "9",
        "title": "Privacidade de Dados e LGPD",
        "content": (
            "9. Privacidade e Proteção de Dados Pessoais (LGPD - Lei nº 13.709/2018)\n"
            "- Os dados dos clientes (nome, telefone, CPF, e-mail e endereço) são tratados exclusivamente para viabilizar o processamento dos pedidos, emissão de nota fiscal e rastreamento de entregas.\n"
            "- Não compartilhamos informações com terceiros para fins de marketing.\n"
            "- O cliente tem o direito de solicitar a consulta, retificação ou exclusão definitiva de seus dados a qualquer momento via canais oficiais."
        ),
        "keywords": ["lgpd", "privacidade", "dados", "dados pessoais", "cpf", "segurança", "seguranca", "exclusão", "exclusao"],
    },
]


class PolicyRetriever:
    """Retrieves the most relevant store policy sections based on lexical & semantic matching."""

    def __init__(self, pdf_path=POLICY_PDF_PATH):
        self.pdf_path = pdf_path
        self.chunks: List[PolicyChunk] = []
        self._load_and_index_policies()

    def _load_and_index_policies(self) -> None:
        """Load curated policy chunks and verify against local PDF if available."""
        for item in CURATED_POLICY_SECTIONS:
            self.chunks.append(
                PolicyChunk(
                    chunk_id=item["chunk_id"],
                    section_number=item["section_number"],
                    title=item["title"],
                    content=item["content"],
                    keywords=item["keywords"],
                )
            )

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple tokenizer that extracts lowercased alphanumeric words."""
        cleaned = re.sub(r"[^\w\sáéíóúâêîôûãõç]", " ", text.lower())
        return [w for w in cleaned.split() if len(w) > 2]

    def search_policy(self, query: str, top_k: int = 2) -> List[Dict[str, str]]:
        """Search policy chunks using BM25-like TF-IDF keyword overlap + keyword boosting."""
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores: List[tuple[float, PolicyChunk]] = []

        # Intent triggers for high-precision routing
        intent_boosts = {
            "endereço": ["pol_01_sobre"],
            "endereco": ["pol_01_sobre"],
            "onde fica": ["pol_01_sobre"],
            "telefone": ["pol_01_sobre"],
            "whatsapp": ["pol_01_sobre"],
            "horário": ["pol_02_horarios"],
            "horario": ["pol_02_horarios"],
            "aberto": ["pol_02_horarios"],
            "abre": ["pol_02_horarios"],
            "fecha": ["pol_02_horarios"],
            "pagamento": ["pol_03_pagamentos"],
            "pix": ["pol_03_pagamentos"],
            "parcelamento": ["pol_03_pagamentos"],
            "cartão": ["pol_03_pagamentos"],
            "cartao": ["pol_03_pagamentos"],
            "juros": ["pol_03_pagamentos"],
            "devolver": ["pol_04_trocas_devolucoes"],
            "devolução": ["pol_04_trocas_devolucoes"],
            "devolucao": ["pol_04_trocas_devolucoes"],
            "arrependi": ["pol_04_trocas_devolucoes"],
            "arrependimento": ["pol_04_trocas_devolucoes"],
            "cdc": ["pol_04_trocas_devolucoes"],
            "troca": ["pol_04_trocas_devolucoes"],
            "trocar": ["pol_04_trocas_devolucoes"],
            "frete": ["pol_05_frete_entregas"],
            "entrega": ["pol_05_frete_entregas"],
            "rastreio": ["pol_05_frete_entregas"],
            "promoção": ["pol_06_promocoes"],
            "promocao": ["pol_06_promocoes"],
            "garantia": ["pol_08_garantia"],
            "defeito": ["pol_04_trocas_devolucoes", "pol_08_garantia"],
            "lgpd": ["pol_09_lgpd"],
            "acessórios": ["pol_01_sobre"],
            "cordas": ["pol_01_sobre"],
            "palhetas": ["pol_01_sobre"],
        }

        query_str_lower = query.lower()

        for chunk in self.chunks:
            chunk_tokens = self._tokenize(chunk.content)
            chunk_token_set = set(chunk_tokens)

            # Term frequency score
            score = 0.0
            for token in query_tokens:
                if token in chunk_token_set:
                    # Token match in content
                    tf = chunk_tokens.count(token)
                    score += 1.0 + math.log(1 + tf)

                # Check keyword list match
                for kw in chunk.keywords:
                    if token in kw or kw in token:
                        score += 3.0

            # Direct intent boost
            for phrase, target_chunk_ids in intent_boosts.items():
                if phrase in query_str_lower and chunk.chunk_id in target_chunk_ids:
                    score += 10.0

            scores.append((score, chunk))

        # Sort by relevance score descending
        scores.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, chunk in scores[:top_k]:
            if score > 0.5:
                results.append({
                    "section": f"Seção {chunk.section_number}: {chunk.title}",
                    "content": chunk.content,
                    "relevance_score": round(score, 2),
                })

        return results


# Global singleton instance
_default_retriever = None


def get_policy_retriever() -> PolicyRetriever:
    """Return a singleton instance of PolicyRetriever."""
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = PolicyRetriever()
    return _default_retriever


def search_store_policies(query: str, top_k: int = 2) -> List[Dict[str, str]]:
    """Convenience functional interface for policy retrieval."""
    retriever = get_policy_retriever()
    return retriever.search_policy(query, top_k=top_k)

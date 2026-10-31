"""Tool definitions and execution pipeline for LLM Function Calling."""

import json
from typing import Any, Dict, List, Optional
from src.db import (
    search_products,
    get_product_details,
    get_order_status,
    get_all_active_promotions,
)
from src.rag import search_store_policies


# ==============================================================================
# Tool Implementation Functions
# ==============================================================================

def tool_search_catalog(
    query: Optional[str] = None,
    category: Optional[str] = None,
    string_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock_only: bool = True,
    limit: int = 5,
) -> Dict[str, Any]:
    """Search instruments in the store catalog with category, price, stock, and string type filters."""
    results = search_products(
        query=query,
        category_name=category,
        string_type=string_type,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        limit=limit,
    )

    if not results:
        return {
            "success": True,
            "total_found": 0,
            "products": [],
            "message": "Nenhum instrumento encontrado com esses critérios de busca.",
        }

    return {
        "success": True,
        "total_found": len(results),
        "products": results,
    }


def tool_get_product_info(product_name_or_id: str) -> Dict[str, Any]:
    """Retrieve exact details, stock, pricing, and promotion status for an instrument."""
    result = get_product_details(product_name_or_id)
    if not result:
        return {
            "success": False,
            "message": f"Instrumento '{product_name_or_id}' não encontrado em nosso catálogo.",
        }

    return {
        "success": True,
        "product": result,
    }


def tool_check_order_status(
    tracking_code: Optional[str] = None,
    order_id: Optional[int] = None,
    customer_query: Optional[str] = None,
) -> Dict[str, Any]:
    """Check the status, tracking code, and items of a purchase order."""
    result = get_order_status(
        tracking_code=tracking_code,
        order_id=order_id,
        customer_query=customer_query,
    )
    if not result:
        return {
            "success": False,
            "message": "Pedido não localizado. Verifique se o código de rastreamento ou número do pedido está correto.",
        }

    return {
        "success": True,
        "order": result,
    }


def tool_search_store_policies(query: str) -> Dict[str, Any]:
    """Search store policies manual (hours, address, return rules, CDC, warranties)."""
    results = search_store_policies(query, top_k=2)
    if not results:
        return {
            "success": False,
            "message": "Nenhuma seção específica encontrada no manual para essa consulta.",
        }

    return {
        "success": True,
        "matched_policies": results,
    }


def tool_list_active_promotions() -> Dict[str, Any]:
    """List all currently active promotional offers in the store."""
    promos = get_all_active_promotions()
    return {
        "success": True,
        "active_promotions_count": len(promos),
        "promotions": promos,
    }


# ==============================================================================
# Dispatcher for Tool Execution
# ==============================================================================

TOOL_REGISTRY = {
    "search_catalog": tool_search_catalog,
    "get_product_info": tool_get_product_info,
    "check_order_status": tool_check_order_status,
    "search_store_policies": tool_search_store_policies,
    "list_active_promotions": tool_list_active_promotions,
}


def execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    """Execute a tool by name and return JSON-serialized string output."""
    handler = TOOL_REGISTRY.get(name)
    if not handler:
        return json.dumps({
            "error": f"Tool '{name}' is not recognized.",
            "available_tools": list(TOOL_REGISTRY.keys()),
        }, ensure_ascii=False)

    try:
        output = handler(**arguments)
        return json.dumps(output, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "error": f"Error executing tool '{name}': {str(e)}",
        }, ensure_ascii=False)


# ==============================================================================
# Declarations for Google Gemini GenAI SDK
# ==============================================================================

GEMINI_TOOL_DEFINITIONS = [
    tool_search_catalog,
    tool_get_product_info,
    tool_check_order_status,
    tool_search_store_policies,
    tool_list_active_promotions,
]


# ==============================================================================
# Declarations for OpenAI Function Calling Schema
# ==============================================================================

OPENAI_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_catalog",
            "description": "Busca instrumentos musicais no catálogo da Empório da Música por palavra-chave, categoria, tipo de corda, faixa de preço e estoque.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Termo de busca do instrumento (ex: 'violão', 'yamaha', 'tagima', 'estudante').",
                    },
                    "category": {
                        "type": "string",
                        "description": "Categoria do instrumento (ex: 'Violões', 'Guitarras', 'Baixos', 'Baterias', 'Teclados', 'Sopro', 'Cordas Orquestrais', 'Ukuleles').",
                    },
                    "string_type": {
                        "type": "string",
                        "description": "Tipo de corda desejada: 'aço' ('steel') ou 'nylon'.",
                    },
                    "min_price": {
                        "type": "number",
                        "description": "Preço mínimo em reais (BRL).",
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Preço máximo em reais (BRL). Exemplo: 1000 para instrumentos até R$ 1.000,00.",
                    },
                    "in_stock_only": {
                        "type": "boolean",
                        "description": "Se verdadeiro, filtra apenas produtos com estoque disponível (> 0). Padrão é true.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Número máximo de resultados a retornar (padrão 5).",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_info",
            "description": "Obtém detalhes completos, especificações técnicas, preço atual, estoque real e status de promoção de um instrumento específico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name_or_id": {
                        "type": "string",
                        "description": "Nome exato ou parcial do instrumento ou ID (ex: 'Takamine GD20', 'Yamaha C40', '81').",
                    },
                },
                "required": ["product_name_or_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_order_status",
            "description": "Consulta o status de um pedido de compra, código de rastreamento dos Correios/transportadora e previsão de entrega.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tracking_code": {
                        "type": "string",
                        "description": "Código de rastreamento do pedido (ex: 'BRJL5544332BR').",
                    },
                    "order_id": {
                        "type": "integer",
                        "description": "Número identificador do pedido.",
                    },
                    "customer_query": {
                        "type": "string",
                        "description": "Nome ou e-mail do cliente.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_store_policies",
            "description": "Consulta o manual de políticas internas da Empório da Música (endereço, horário de funcionamento, regras de troca e devolução CDC, formas de pagamento, garantias, LGPD).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Dúvida ou tema sobre a política (ex: 'devolução arrependimento', 'endereço da loja', 'horário de funcionamento', 'desconto no PIX', 'garantia legal').",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_active_promotions",
            "description": "Lista todas as promoções e descontos que estão ATIVOS no momento na loja.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

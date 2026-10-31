"""Automated test suite for Empório da Música AI Agent system."""

import pytest
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from src.db import search_products, get_product_details, get_order_status, get_all_active_promotions
from src.rag import search_store_policies
from src.tools import execute_tool
from src.agent import EmporioAgent


class TestDatabaseAndCatalog:
    """Tests for database layer and business rules."""

    def test_search_violoes_under_1000(self):
        """Verify search for violões under R$ 1000 in stock."""
        products = search_products(category_name="Violões", max_price=1000, in_stock_only=True)
        assert len(products) > 0
        for p in products:
            assert p["final_price"] <= 1000
            assert p["stock_quantity"] > 0
            assert p["is_in_stock"] is True

    def test_out_of_stock_filtering(self):
        """Verify that products with zero stock are filtered when requested."""
        in_stock = search_products(in_stock_only=True, limit=100)
        for p in in_stock:
            assert p["stock_quantity"] > 0

    def test_takamine_gd20_details_and_expired_promo(self):
        """Verify Takamine GD20 price, stock, and expired promotion status."""
        prod = get_product_details("Takamine GD20")
        assert prod is not None
        assert "Takamine GD20" in prod["name"]
        assert prod["original_price"] == 2199.0
        assert prod["stock_quantity"] == 5
        assert prod["is_in_stock"] is True
        # Verify expired promotion is not treated as active
        assert prod["has_active_promotion"] is False
        assert len(prod["expired_promotions"]) > 0

    def test_active_promotions_integrity(self):
        """Verify active promotions have is_active == 1 and correct discount."""
        active_promos = get_all_active_promotions()
        assert len(active_promos) == 4  # Known exactly from dataset
        for promo in active_promos:
            assert promo["discount_percent"] > 0
            assert promo["discounted_price"] < promo["original_price"]

    def test_order_tracking_lookup(self):
        """Verify order tracking retrieval by tracking code."""
        order = get_order_status(tracking_code="BRJL5544332BR")
        assert order is not None
        assert order["order_id"] == 8
        assert order["customer_name"] == "Ana Carolina Ferreira"
        assert order["status_raw"] == "shipped"
        assert len(order["items"]) > 0


class TestPolicyRetrievalRAG:
    """Tests for policy manual retrieval engine."""

    def test_store_address_query(self):
        """Address queries should return Section 1."""
        results = search_store_policies("Qual o endereço da loja?")
        assert len(results) > 0
        top = results[0]
        assert "Seção 1" in top["section"]
        assert "Rua 14 de Maio, 3200" in top["content"]

    def test_store_hours_query(self):
        """Hours queries should return Section 2."""
        results = search_store_policies("Qual o horário de funcionamento no sábado?")
        assert len(results) > 0
        top = results[0]
        assert "Seção 2" in top["section"]
        assert "09:00" in top["content"]

    def test_return_policy_cdc_query(self):
        """Return and regret queries should return Section 4."""
        results = search_store_policies("Me arrependi da compra, posso devolver pelo CDC?")
        assert len(results) > 0
        top = results[0]
        assert "Seção 4" in top["section"]
        assert "7 (sete) dias" in top["content"]
        assert "Código de Defesa do Consumidor" in top["content"]

    def test_pix_discount_query(self):
        """Payment discount queries should return Section 3."""
        results = search_store_policies("Tem desconto pagando com PIX?")
        assert len(results) > 0
        top = results[0]
        assert "Seção 3" in top["section"]
        assert "5%" in top["content"]


class TestAgentConversations:
    """End-to-end conversational agent response tests."""

    @pytest.fixture
    def agent(self):
        return EmporioAgent()

    def test_agent_answers_violoes_under_1000(self, agent):
        response = agent.chat("Quais opções de violões disponíveis custando até R$1000?")
        assert "Violões" in response or "violão" in response.lower()
        assert "R$" in response
        assert "estoque" in response.lower()

    def test_agent_answers_address(self, agent):
        response = agent.chat("Qual o endereço da loja?")
        assert "Rua 14 de Maio, 3200" in response
        assert "Campo Grande" in response

    def test_agent_answers_takamine_gd20(self, agent):
        response = agent.chat("Quanto custa o Takamine GD20?")
        assert "Takamine GD20" in response
        assert "2.199,00" in response
        assert "estoque" in response.lower()

    def test_agent_answers_return_policy(self, agent):
        response = agent.chat("Me arrependi da minha compra, posso devolver meu pedido?")
        assert "7" in response
        assert "dias" in response
        assert "reembolso" in response.lower() or "devolução" in response.lower()

    def test_agent_handles_out_of_scope(self, agent):
        response = agent.chat("Vocês vendem geladeira?")
        assert "exclusivamente" in response.lower() or "não comercializamos" in response.lower()

# Interaction Transcript 03: Exact Price Inquiry & Expired Promotion Handling

**Scenario:** Customer asks for the price and availability of the Takamine GD20 and questions whether a 12% discount they saw earlier is still valid.  
**Channel:** WhatsApp / Web Text Terminal  
**Tool Invoked:** `get_product_info(product_name_or_id="Takamine GD20")`  

---

### Transcript

**User:**  
> "Quanto custa o Takamine GD20? Vi em um anúncio que tinha 12% de desconto, ainda tá valendo?"

**Empório da Música Assistant:**  
> "Olá! Que máquina de violão! O Takamine GD20 é um dos queridinhos aqui na loja por causa do tampo em cedro maciço e do sustain maravilhoso! 🎸✨
>
> ℹ️ **Nota de Transparência sobre a Promoção:**  
> Consultei o nosso sistema agora: aquela promoção especial com 12% de desconto infelizmente **já se encerrou** (`status: expirada`). Seguindo as diretrizes de transparência da nossa loja, não podemos prometer descontos que já saíram do ar.
>
> Mas temos ótimas notícias sobre o preço de tabela vigente e facilidades de pagamento:
>
> • **Preço de Tabela:** **R$ 2.199,00**  
> • **À vista no PIX (com 5% de desconto imediato):** **R$ 2.089,05** *(economia de mais de R$ 109,00!)*  
> • **Cartão de Crédito:** até **12x de R$ 183,25 SEM JUROS**  
> • **Disponibilidade:** ✅ **Em estoque** (5 unidades disponíveis a pronta entrega)  
>
> **Especificações Rápidas:**  
> • Tampo: Cedro Sólido  
> • Fundo e Laterais: Sapele  
> • Braço: Mogno com cordas de aço (Dreadnought)  
> • Garantia: 90 dias legal (CDC) + garantia de fábrica Takamine.
>
> Quer que eu separe uma unidade para você retirar aqui na loja ou prefere calcular o frete para entrega na sua casa?"

---
**Verification Note:**  
Crucial business test case. In `promotions.csv`, promotion ID 4 for product 95 (Takamine GD20) has `is_active = 0`. The agent did NOT hallucinate the 12% discount; instead, it transparently explained the expiration, presented current table price, calculated the legitimate 5% PIX discount, calculated valid installments, and confirmed real-time stock.

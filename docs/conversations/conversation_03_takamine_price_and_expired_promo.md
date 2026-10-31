# Interaction Transcript 03: Exact Price Inquiry & Expired Promotion Handling

Scenario: Customer asks for the price and availability of the Takamine GD20 and questions whether a 12% discount they saw earlier is still valid.
Channel: WhatsApp / Text Terminal
Tool Invoked: get_product_info(product_name_or_id="Takamine GD20")

---

### Transcript

User:
"Quanto custa o Takamine GD20? Vi em um anúncio que tinha 12% de desconto, ainda tá valendo?"

Empório da Música Assistant:
"Olá! Temos sim todas as informações do Takamine GD20 Dreadnought Natural.

Nota de Transparência sobre a Promoção:
Consultei nosso sistema agora: aquela promoção especial com 12% de desconto infelizmente já se encerrou (status: expirada). Seguindo as políticas da loja, não podemos aplicar descontos fora da vigência.

No entanto, temos o produto disponível com as seguintes condições de tabela:
- Preço de Tabela: R$ 2.199,00
- À vista no PIX (com 5% de desconto): R$ 2.089,05 (economia de R$ 109,95)
- Cartão de Crédito: até 12x de R$ 183,25 sem juros
- Disponibilidade: Em estoque (5 unidades disponíveis para pronta entrega)

Especificações:
- Tampo: Cedro Sólido
- Fundo e Laterais: Sapele
- Braço: Mogno com cordas de aço (formato Dreadnought)
- Garantia: 90 dias legal (CDC) + garantia de fábrica Takamine

Gostaria de reservar uma unidade para retirar na loja ou prefere calcular o frete para entrega?"

---

Verification Note:
In promotions.csv, promotion ID 4 for product 95 (Takamine GD20) has is_active = 0. The agent correctly refused the expired discount, stated the current table price, calculated the legitimate 5% PIX discount, and confirmed real-time stock.

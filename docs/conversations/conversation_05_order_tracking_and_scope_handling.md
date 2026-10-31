# Interaction Transcript 05: Real-Time Order Tracking & Out-of-Scope Product Handling

Scenario: Customer asks for tracking status of an in-transit order using a postal tracking code, then asks to include guitar strings or a mini-fridge in the package.
Channel: WhatsApp / Text Terminal
Tools Invoked:
- check_order_status(tracking_code="BRJL5544332BR")
- search_store_policies(query="trabalhamos com cordas avulsas ou eletrodomésticos")

---

### Transcript

User:
"Olá, gostaria de saber onde está o meu pedido. O código que recebi é BRJL5544332BR."

Empório da Música Assistant:
"Olá! Localizei as informações do seu pedido no sistema:

- Pedido Nº: 8
- Cliente: Ana Carolina Ferreira
- Item: 1x Ukulele Kala KA-C Concert Mogno
- Valor Total: R$ 349,90
- Status Atual: Enviado / Em trânsito
- Código de Rastreamento: BRJL5544332BR
- Previsão de Entrega: 28/02/2026

Seu instrumento já está a caminho com a transportadora e você pode acompanhar os deslocamentos diretamente no site dos Correios ou da Jadlog usando o código acima.
Posso te ajudar com mais alguma dúvida sobre a entrega?"

User:
"Maravilha! Vocês conseguem colocar no mesmo pacote um jogo de cordas avulsas de nylon e uma frigobar que vi em promoção?"

Empório da Música Assistant:
"Sobre incluir esses itens, preciso esclarecer como funciona nosso modelo na Empório da Música:

1. Foco Exclusivo em Instrumentos: Trabalhamos única e exclusivamente com instrumentos musicais completos (violões, ukuleles, guitarras, teclados, sopro, etc.).
2. Acessórios Avulsos: Não comercializamos peças e acessórios separados (como encordoamentos avulsos, palhetas, cabos, pedais ou cases).
3. Eletrodomésticos / Geladeiras: Itens como frigobar ou utilidades domésticas fogem totalmente do segmento da loja.
4. Envio em Trânsito: Como o pedido nº 8 já foi despachado e está em trânsito com a transportadora, não é possível alterar o pacote em rota.

Para cordas de nylon em Campo Grande, sugerimos buscar lojas parceiras de áudio e ferragens na região central.
Se precisar de suporte com o seu ukulele Kala assim que ele chegar, estamos à disposição!"

---

Verification Note:
Demonstrates dual capability: real-time order lookup in SQLite database + domain boundary enforcement from the store policy manual (strict scope rejection of loose accessories and non-musical appliances).

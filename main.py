#!/usr/bin/env python3
"""Interactive Terminal Interface (CLI) for Empório da Música AI Assistant."""

import os
import sys

# Configure UTF-8 stdout/stdin for Windows command prompts
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add repository root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    CYAN = Fore.CYAN
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    MAGENTA = Fore.MAGENTA
    RED = Fore.RED
    BRIGHT = Style.BRIGHT
    RESET = Style.RESET_ALL
except ImportError:
    CYAN = GREEN = YELLOW = MAGENTA = RED = BRIGHT = RESET = ""

from src.agent import EmporioAgent
from src import config


def print_banner(agent: EmporioAgent):
    print(f"\n{CYAN}{'═' * 70}{RESET}")
    print(f"{CYAN}{BRIGHT}   🎸 EMPÓRIO DA MÚSICA — ASSISTENTE VIRTUAL DE ATENDIMENTO 🎶{RESET}")
    print(f"{CYAN}   Rua 14 de Maio, 3200 — Centro, Campo Grande - MS | (67) 3341-4444{RESET}")
    print(f"{CYAN}{'═' * 70}{RESET}")
    print(f"{YELLOW}• Motor Ativo:{RESET} {agent.get_provider_name()}")
    print(f"{YELLOW}• Modo de Operação:{RESET} Atendimento ao Cliente em Tempo Real via Terminal")
    print(f"{CYAN}{'─' * 70}{RESET}")
    print(f"{BRIGHT}Sugestões de perguntas para testar:{RESET}")
    print(f"  {GREEN}[1]{RESET} Quais opções de violões disponíveis custando até R$1000?")
    print(f"  {GREEN}[2]{RESET} Qual o endereço da loja e horário de funcionamento?")
    print(f"  {GREEN}[3]{RESET} Quanto custa o Takamine GD20?")
    print(f"  {GREEN}[4]{RESET} Me arrependi da minha compra, posso devolver meu pedido?")
    print(f"  {GREEN}[5]{RESET} Qual o status do pedido com rastreio BRJL5544332BR?")
    print(f"  {GREEN}[6]{RESET} Vocês vendem geladeira ou corda avulsa de guitarra?")
    print(f"{CYAN}{'─' * 70}{RESET}")
    print(f"Comandos: digite {YELLOW}'sair'{RESET} para encerrar, {YELLOW}'limpar'{RESET} para reiniciar o histórico.")
    print(f"{CYAN}{'═' * 70}{RESET}\n")


def main():
    agent = EmporioAgent()
    print_banner(agent)

    while True:
        try:
            user_input = input(f"{BRIGHT}{GREEN}Você > {RESET}").strip()

            if not user_input:
                continue

            lower_cmd = user_input.lower()
            if lower_cmd in ("sair", "exit", "quit", "q"):
                print(f"\n{CYAN}Empório da Música > Obrigado pelo contato! Que a sua música nunca pare. Até logo! 🎶{RESET}\n")
                break

            if lower_cmd in ("limpar", "clear", "cls", "reset"):
                agent.reset_conversation()
                print(f"\n{YELLOW}✓ Histórico de conversa reiniciado com sucesso.{RESET}\n")
                continue

            if lower_cmd in ("ajuda", "help", "?"):
                print_banner(agent)
                continue

            # Process message
            response = agent.chat(user_input)

            print(f"\n{BRIGHT}{CYAN}Empório da Música >{RESET}")
            print(f"{response}\n")

        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{CYAN}Empório da Música > Até logo! 🎶{RESET}\n")
            break
        except Exception as e:
            print(f"\n{RED}[Erro inesperado]: {e}{RESET}\n")


if __name__ == "__main__":
    main()

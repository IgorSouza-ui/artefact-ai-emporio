#!/usr/bin/env python3
"""Interactive Terminal Interface (CLI) for Empório da Música Assistant."""

import os
import re
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
    WHITE = Fore.WHITE
    BOLD = Style.BRIGHT
    RESET = Style.RESET_ALL
except ImportError:
    CYAN = GREEN = YELLOW = WHITE = BOLD = RESET = ""

from src.agent import EmporioAgent


def format_for_terminal(text: str) -> str:
    """Format markdown for clean terminal display without raw asterisks."""
    if not text:
        return ""

    # Replace **bold** with ANSI bold if supported, otherwise just remove asterisks
    if BOLD:
        formatted = re.sub(r"\*\*(.*?)\*\*", rf"{BOLD}\1{RESET}", text)
        formatted = re.sub(r"~~(.*?)~~", r"\1", formatted)
        formatted = re.sub(r"\*(.*?)\*", r"\1", formatted)
    else:
        formatted = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        formatted = re.sub(r"~~(.*?)~~", r"\1", formatted)
        formatted = re.sub(r"\*(.*?)\*", r"\1", formatted)

    return formatted


def print_banner(agent: EmporioAgent):
    print(f"\n{CYAN}======================================================================{RESET}")
    print(f"{BOLD}  EMPÓRIO DA MÚSICA — ATENDIMENTO AO CLIENTE{RESET}")
    print(f"  Rua 14 de Maio, 3200 — Centro, Campo Grande - MS | (67) 3341-4444")
    print(f"{CYAN}======================================================================{RESET}")
    print(f"Engine ativo: {YELLOW}{agent.get_provider_name()}{RESET}")
    print(f"Digite sua mensagem abaixo (ou 'sair' para encerrar, 'limpar' para reiniciar).")
    print(f"{CYAN}----------------------------------------------------------------------{RESET}\n")


def main():
    agent = EmporioAgent()
    print_banner(agent)

    while True:
        try:
            user_input = input(f"{BOLD}{GREEN}Você > {RESET}").strip()

            if not user_input:
                continue

            lower_cmd = user_input.lower()
            if lower_cmd in ("sair", "exit", "quit", "q"):
                print(f"\n{CYAN}Empório da Música > Obrigado pelo contato! Estamos à disposição. Até logo!{RESET}\n")
                break

            if lower_cmd in ("limpar", "clear", "cls", "reset"):
                agent.reset_conversation()
                print(f"\n{YELLOW}[Histórico de conversa reiniciado]{RESET}\n")
                continue

            if lower_cmd in ("ajuda", "help", "?"):
                print_banner(agent)
                continue

            # Process message
            response = agent.chat(user_input)
            clean_resp = format_for_terminal(response)

            print(f"\n{BOLD}{CYAN}Empório da Música >{RESET}")
            print(f"{clean_resp}\n")

        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{CYAN}Empório da Música > Até logo!{RESET}\n")
            break
        except Exception as e:
            print(f"\n[Erro]: {e}\n")


if __name__ == "__main__":
    main()

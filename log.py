from datetime import datetime

LOG_FILE = "debug_log.txt"

def _write_log(evento, detalhe=""):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {evento}: {detalhe}\n")

def log_redimensionamento(novo_tamanho, origem="manual"):
    _write_log(f"Redimensionamento ({origem})", f"{novo_tamanho.width()}x{novo_tamanho.height()}")

def log_troca_texto(novo_texto):
    _write_log("Troca de Texto", f'"{novo_texto}"')

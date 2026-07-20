import logging
import sys

def setup_logging(level=logging.INFO):
    """Configure le logging pour l'ensemble de l'application."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            # Optionnel : ajouter un fichier de log
            # logging.FileHandler("soc_triage.log")
        ]
    )
    # Réduire le bruit des bibliothèques tierces
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    return logging.getLogger(__name__)
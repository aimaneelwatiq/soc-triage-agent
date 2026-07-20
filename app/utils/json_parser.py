import json
import re
from typing import Dict, Any

def extract_json(content: str) -> Dict[str, Any]:
    """
    Extrait un objet JSON valide du texte brut renvoyé par le LLM.
    Gère :
    1. Les blocs Markdown ```json ... ```
    2. Les blocs Markdown ``` ... ```
    3. Du texte avant ou après le JSON
    """
    if not content:
        raise ValueError("Le contenu du LLM est vide.")

    # 1. Nettoyer les balises Markdown classiques
    cleaned = re.sub(r'```json\s*', '', content)
    cleaned = re.sub(r'```\s*', '', cleaned)
    
    # 2. Essayer de trouver un objet JSON (tout ce qui commence par { et finit par })
    match = re.search(r'(\{.*\})', cleaned, re.DOTALL)
    if not match:
        raise ValueError(f"Aucune structure JSON trouvée dans : {content[:200]}...")

    potential_json = match.group(1)

    # 3. Tentative de parsing
    try:
        return json.loads(potential_json)
    except json.JSONDecodeError as e:
        # Si le JSON est cassé (ex: virgules en trop), on remonte l'erreur pour qu'elle soit loggée
        raise ValueError(f"JSON invalide reçu du LLM: {e}\nContenu extrait: {potential_json[:500]}")
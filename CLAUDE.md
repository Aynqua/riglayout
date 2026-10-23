# CLAUDE.md

Avant toute tâche, lire la documentation technique dans `doc/` plutôt que de relire tout le code :
- `doc/architecture.md` — stack, arborescence, flux de données, conventions de coordonnées
- `doc/codebase_map.md` — fonctions/classes par module
- `doc/guidelines.md` — règles de code
- `doc/todo_roadmap.md` — état, bugs connus, prochaines étapes

Règle : après chaque modification qui change l'architecture, ajoute une fonction majeure, modifie un schéma JSON ou une règle, **mettre à jour les fichiers `doc/` concernés** (et `JSON.md` si le format change) dans la même session.

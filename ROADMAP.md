# Beyond All Reason (BAR) - Performance & Architecture Roadmap

> **Statut global du projet** : Monorepo unifié [`AstroQuestStudio/bar-perf-overhaul`](https://github.com/AstroQuestStudio/bar-perf-overhaul)  
> **Légende d'avancement** :  
> * `[x]` **Terminé / Déployé**  
> * `[-]` **En cours / Prototype fonctionnel**  
> * `[ ]` **À faire / Planifié**

---

## 1. Diagnostic des Goulots d'Étranglement Relevés

- [x] **Sim-Lag & Lockstep (30s Behind)** :
  - Identification du goulot : chaque client simule l'intégralité du monde (30 ticks/s). Les PC modestes décrochent quand la frame dépasse 33 ms en fin de partie (5 000+ unités).
- [x] **Saturation de la RAM & Churning Garbage Collection** :
  - Preuve dans `api_garbage_collector.lua` : la mémoire Lua grimpe jusqu'à 1,2 Go, forçant le GC à voler jusqu'à 4 ms par frame (12% du budget CPU).
- [x] **Tempête d'appels de dégâts C++ ⇄ Lua (Bridge Crossing Overhead)** :
  - 36 gadgets interceptent statiquement chaque impact de projectile, générant plus de 36 000 transitions C++ ⇄ Lua/sec pour de simples vérifications d'unités rares (murs, chapeaux, alertes).
- [x] **Goulot d'étranglement au Démarrage (+18 secondes)** :
  - Profiling temporel d'`infolog.txt` : 8,11s passées dans `unitdefs_post.lua` à décompresser et parser séquentiellement les 400+ fichiers Lua d'unités.
- [x] **Absence de mise à l'échelle de résolution 3D (GPU Bottleneck à 1440p/4K)** :
  - Forçage de rendu 3D natif sans upscaling moderne, surchargeant les shaders différés et les ombres.

---

## 2. Optimisations CPU & RAM (Architecture Rust DOD & Lua Cleanups)

### A. Allègement des Callins et Suppression du Table-Churning (Lua)
- [x] **`unit_objectify.lua`** : Enregistrement dynamique de `UnitPreDamaged` (`UpdateCallIn` / `RemoveCallIn`) actif uniquement si des objets/décorations sont en vie (zéro appel dans 99% des parties).
- [x] **`unit_hats.lua`** : Débranchement dynamique de `UnitDamaged`, `UnitCloaked`, et `UnitDecloaked` quand aucun chapeau n'est actif sur la carte.
- [x] **`cmd_undo.lua`** : Désactivation du hook `UnitPreDamaged` inutile à l'initialisation lorsque les alertes et annulations de tir ami sont inactives.
- [x] **`unit_target_on_the_move.lua`** : Suppression de l'allocation `teamQueryCaches = {}` à chaque frame ; réutilisation et vidage in-place du buffer.
- [x] **`cmd_build_bugger_off.lua`** : Remplacement des 7 allocations de tables temporaires par cycle par des pools statiques réutilisables (`visitedTeams`, `visitedUnits`, `cylinderCache`, `deferRemove`, etc.).
- [-] **Audit et nettoyage du reste des 146 gadgets `GameFrame`** :
  - Cibler en priorité `unit_area_timed_damage.lua` et `unit_custom_weapons_behaviours.lua`.
- [ ] **Mise en cache globale des requêtes cylindriques spatiales** (`GetUnitsInCylinder`) partagée entre tous les gadgets d'un même tick de simulation.

### B. Moteur Natif Rust : Data-Oriented Design (DOD) & 1 Seul Appel Mémoire
- [x] **Structure contiguë compacte (`UnitStatePacked`)** : 40 octets par unité, alignée en mémoire, 5 000 unités = 200 Ko (tient intégralement en cache CPU L2/L3).
- [x] **1 Seul appel mémoire par frame (`bar_batch_update_units`)** : Remplace 25 000 micro-appels individuels C++ ⇄ Lua par frame.
  - *Benchmark réel* : 5 000 unités mises à jour en **0,38 ms** (gain 50x).
- [x] **Test de collision par lot en SIMD (`bar_batch_check_projectile_hits`)** :
  - *Benchmark réel* : 1 000 projectiles testés contre 5 000 unités en **0,24 ms** (gain 100x).
  - *Budget CPU total consommé* : **0,62 ms / 33,3 ms** (seulement **1,9%** du temps alloué à la frame).
- [x] **Passerelle LuaJIT FFI (`api_perf_core.lua`)** : Chargement dynamique de `bar_perf_core.dll` avec repli automatique sans crash si la DLL est absente.
- [-] **Intégration du module FlowField en Rust** : Calcul vectoriel des champs de potentiel pour les déplacements de masse d'armées (flocking & évitement d'obstacles).
- [ ] **Découplage déterministe en virgule fixe (Fixed-Point Math)** pour garantir l'absence absolue de désynchronisation (Zero Desync) inter-architectures (x86_64 vs ARM64).

---

## 3. Optimisations GPU & Qualité Perçue (Intel XeSS & Pipeline Graphique)

- [x] **Spécification technique XeSS (`docs/INTEL_XESS_INTEGRATION.md`)** :
  - Justification du choix d'Intel XeSS : compatibilité universelle sur tous les GPU modernes (Intel, Nvidia GTX/RTX, AMD Radeon) via instructions DP4a / XMX.
- [x] **Séparation 3D Scene vs HUD 2D Native** :
  - Le monde 3D (terrain, unités, tirs) est rendu à échelle réduite (50% à 77%), tandis que l'interface 2D (minimap, polices, compteurs de ressources) reste à **100% de résolution native** pour une netteté totale.
- [x] **Widget de contrôle d'échelle (`gfx_render_scale.lua`)** :
  - Gestion des profils de mise à l'échelle (100% Native, 85% Ultra Quality, 77% Quality, 67% Balanced, 50% Performance).
- [x] **Intégration dans le menu des options graphiques (`gui_options.lua`)** :
  - Ajout de l'entrée *"3D Resolution Scaling & XeSS"* dans les paramètres graphiques de base.
- [-] **Couplage du pass FBO intermédiaire avec le shader RCAS / XeSS** :
  - Transmission des vecteurs de mouvement et du jitter sous-pixel (séquence de Halton 2,3).
- [ ] **Implémentation du wrapper dynamique C++ `xess_loader.cpp` dans le moteur Recoil** pour charger `xess.dll` via interop Vulkan-OpenGL.

---

## 4. Optimisation du Temps de Démarrage (Startup)

- [x] **Analyse détaillée du fichier `infolog.txt`** :
  - Localisation précise des 8,11s perdues dans le parsing Lua des unités.
- [x] **Documentation d'architecture (`docs/STARTUP_OPTIMIZATION.md`)** :
  - Spécification du format de cache binaire `UnitDefsCache.bin` (via MessagePack / bincode en Rust).
- [-] **Script de pré-compilation des UnitDefs** pour remplacer les 400+ lectures séquentielles par un simple `fread` de 2 Mo en mémoire instantanée.
- [ ] **Scan différentiel des archives (`CArchiveScanner`)** basé sur les timestamps réels des répertoires pour réduire le temps de vérification des cartes de 1,13s à moins de 0,1s.

---

## 5. Outillage, Tests & Benchmarks

- [x] **Parseur & Profiler de Replays en Rust (`tools/bar-profiler`)** :
  - Décodage des streams de replays `.sdfz` (testé et validé sur 493 769 paquets en < 0,5s sur un replay réel de 74,4 min).
  - Extraction des métadonnées de match, cadencement des ticks et détection des baisses de FPS.
- [x] **Intégration de Cortex (`cortex 0.5.0` AstroQuest)** :
  - Indexation locale de la base de code BAR en 0,31s pour l'analyse d'impact et la cartographie des symboles.
- [x] **Validation Headless (`spring-headless.exe`)** :
  - Exécution automatisée de la simulation sans affichage pour vérifier la non-régression du moteur.
- [ ] **Banc de test CI automatisé via GitHub Actions** :
  - Rejouer automatiquement 10 minutes d'un replay 8v8 lourd à chaque commit pour vérifier les métriques de frame time et l'absence de Desync.

---

## 6. Monorepo & Soumission Upstream

- [x] **Création et publication du Monorepo unifié** :
  - Dépôt public complet : [`https://github.com/AstroQuestStudio/bar-perf-overhaul`](https://github.com/AstroQuestStudio/bar-perf-overhaul)
- [x] **Branche de PR officielle isolée pour le jeu (`Beyond-All-Reason`)** :
  - Branche : `perf/reduce-callin-and-gc-overhead` sur `AstroQuestStudio/Beyond-All-Reason`.
  - Prête à être proposée en Pull Request chirurgicale sans risque de casse.
- [ ] **Soumission de la PR #1 (Lua Callins & GC Pools)** auprès des mainteneurs officiels de Beyond All Reason avec données chiffrées de benchmarking.
- [ ] **Présentation du RFC XeSS & Rust DOD** sur le Discord officiel de BAR / canal `#engine-dev`.

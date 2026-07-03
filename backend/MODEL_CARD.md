# SSD MobileNet road-damage model

Pathfinder uses the SSD MobileNet model published with the University of Tokyo Sekimoto Lab Road Damage Detector project.

- Local artifact: `trainedModels/ssd_mobilenet_innference_graph.pb`
- SHA-256 prefix used at runtime: `d08aae39abe3`
- Classes: D00, D01, D10, D11, D20, D40, D43, D44
- Source: https://github.com/sekilab/RoadDamageDetector
- Code license: MIT. Dataset images have separate CC BY-SA 4.0 terms.

The model produces evidence for a route heuristic; it does not certify road safety. Performance varies by geography, lighting, camera position, and surface type. Reports with no detection remain visible but contribute a high quality score only after passing image validation.

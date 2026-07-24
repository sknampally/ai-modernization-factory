# Limitations and Future Work

Non-blocking debt (not addressed in 4.2.5):

- dual rule engines still exist
- aimf / CodeStrata naming inconsistency
- no generic assessment-section plugin framework yet
- positive evidence / strengths not implemented
- conclusions artifact writer naming inconsistency (`architecture_conclusions.json`)
- thin agent end-to-end coverage for architecture-enabled assess

Future intelligence packs should reuse the adapter → report-section → HTML/JSON
pattern established here without requiring a large plugin system first.

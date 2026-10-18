# Step 11 - Synthetic cursive generator + dataset prep

## Goal
Build synthetic cursive generator (render from fonts with heavy augmentation: slant, blur, noise, paper texture, perspective, elastic distortion). Prep dataset structure per spec.

## Files
- ml/datasets/synthetic_cursive.py
- ml/datasets/augmentation.py
- ml/data/raw/.gitkeep (structure)

## Notes
- Synthetic pre-trains; real data decides final accuracy
- Store originals and processed separately
MD

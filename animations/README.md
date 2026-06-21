# Qonnect Repeater Explainer

This Manim scene maps Qonnect's matrix-board actions to the physical quantum
repeater workflow: adjacent entanglement generation, quantum-memory storage,
Bell-state measurement, classical heralding/correction, and end-to-end linking.

## Render

```bash
uv sync
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/manim qonnect_explainer.py QonnectRepeaterExplainer
ffmpeg -y -i media/videos/qonnect_explainer/540p15/QonnectRepeaterExplainer.mp4 \
  -filter_complex "[0:v]fps=10,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle" \
  -loop 0 ../assets/qonnect-repeater-explainer.gif
```

The Manim master is 960×540 at 15 fps. FFmpeg produces the optimized 800×450
README GIF. The scene uses plain `Text` objects and does not require LaTeX.

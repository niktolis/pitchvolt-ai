# D2 authoring and rendering guide

## Supported features and what we use

D2 supports reusable styles/classes, diagram composition (layers, scenarios and steps), sequence diagrams, tooltips and links, multiple themes/layout engines, SVG/GIF animation, and SVG/PNG/PDF/PPTX exports. Use features when the relevant architecture viewpoint benefits:
- **Context / deployment**: nested containers and labeled boundaries, meaningful links, differentiated deployed vs planned components; layout with ELK.
- **Dynamic behavior**: `shape: sequence_diagram`; label synchronous, queued and planned traffic precisely.
- **State/process diagrams**: explicit guard conditions and rejection/exception paths.
- **Scenarios / steps**: use multi-board compositions when alternative deployment choices or progressive execution diagrams become genuinely useful.
- **Interactivity**: links/tooltips in standalone exported SVG where a browser allows them; place visible Markdown links adjacent to embedded images because GitHub's image renderer disables SVG interactivity.
- **Animation**: use `d2 --animate-interval=1200 source.d2 output.svg` for diagrams with multiple boards; add only when temporal progression is meaningful.
- **Slide/document exports**: `d2 input.d2 out.pdf` or `d2 input.d2 out.pptx` directly; generated PDF/PPTX uploaded as CI artifacts.

## CI contract

The GitHub Actions workflow `Architecture diagrams` validates each `.d2` source via `d2 validate`, produces linked SVGs, and checks PDF/PPTX production. For **pushes on feature/docs branches**, the workflow commits generated SVGs back into the branch using the built-in GitHub token, while PR runs validate and upload artifacts only.

In Markdown, use relative links:
`![Deployment](rendered/deployment.svg)`
and link to source: `[Editable D2](diagrams/deployment.d2)`.

If the D2 validation or export fails, **do not merge**. Fix source first, rerun, and visually review output. Rendering only proves syntactic validity, not architectural fidelity.

## Local authoring

Install D2 on macOS via `brew install d2`. Then:

```shell
d2 validate docs/architecture/diagrams/deployment.d2
d2 --layout=elk docs/architecture/diagrams/deployment.d2 docs/architecture/rendered/deployment.svg
d2 docs/architecture/diagrams/deployment.d2 deployment.pdf
d2 docs/architecture/diagrams/deployment.d2 deployment.pptx
d2 --watch docs/architecture/diagrams/deployment.d2
```

For new diagrams, prefer stable canonical paths and descriptive naming over numbered copies. Reuse nodes/concepts only through the single documented glossary and reference; do not let generated diagrams become a duplicate maintained source.

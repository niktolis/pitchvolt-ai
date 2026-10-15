# Generated diagram images

This directory receives SVG exports generated directly from ../diagrams/*.d2 by the **Architecture diagrams** GitHub Actions workflow.

Do not edit the SVG outputs by hand. The source-of-truth is the D2 language files. Diagram source changes trigger validation and refreshed SVG rendering; PDF/PPTX presentation exports are available as CI artifacts.

If files are absent during initial review, check the workflow status, then run it again after correcting any D2 compilation errors.

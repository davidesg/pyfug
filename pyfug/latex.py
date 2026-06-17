"""
LaTeX output module for pyfug.

Generates a compilable LaTeX document wrapping multiple figures
in a publication-ready layout, matching the original FUG behavior.
"""

from __future__ import annotations

import subprocess
import shutil
from pathlib import Path
from typing import List, Optional


_LATEX_TEMPLATE = r"""\documentclass[12pt,a4paper]{article}
\usepackage[latin1]{inputenc}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{lscape}
\usepackage{multicol}
\usepackage{setspace}
\newcommand{\est}[2]{\begin{array}[t]{c}
\hspace{-.125in}#1\hspace{-.125in}\vspace{-.13in}\\
\hspace{-.125in}#2\hspace{-.125in}
\end{array}}
\oddsidemargin 0in \textwidth 6.60in     \topmargin -.10in
\headheight 0in \textheight 24.06cm \linespread{1.6}
\pagestyle{empty}
\begin{document}
{landscape_open}
\begin{flushleft}
{figures}
\end{flushleft}
{landscape_close}
\end{document}
"""


def generate_latex(figures: List[str],
                   output_path: str,
                   scale: float = 0.90,
                   landscape: bool = True) -> str:
    """Generate a LaTeX document wrapping figure files.

    Parameters
    ----------
    figures : list of str
        Paths to figure files (PDF, EPS, or PNG).
    output_path : str
        Path for the output .tex file.
    scale : float
        Figure scaling factor (default 0.90 like original FUG).
    landscape : bool
        Whether to use landscape orientation.

    Returns
    -------
    str
        Content of the generated LaTeX file.
    """
    fig_commands = []
    for fig in figures:
        fig_path = Path(fig)
        # Use stem without extension for includegraphics
        stem = fig_path.stem
        ext = fig_path.suffix.lstrip(".")
        fig_commands.append(
            f"\\includegraphics[scale={scale:.2f}]{{{stem}.{ext}}}"
        )

    landscape_open = "\\begin{landscape}" if landscape else ""
    landscape_close = "\\end{landscape}" if landscape else ""

    content = _LATEX_TEMPLATE.format(
        landscape_open=landscape_open,
        figures="\n".join(fig_commands),
        landscape_close=landscape_close,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)

    return content


def compile_latex(tex_path: str,
                  output_dir: Optional[str] = None,
                  clean: bool = True) -> bool:
    """Compile a LaTeX document to PDF using pdflatex.

    Parameters
    ----------
    tex_path : str
        Path to the .tex file.
    output_dir : str, optional
        Output directory for the compiled PDF.
    clean : bool
        If True, remove auxiliary files after compilation.

    Returns
    -------
    bool
        True if compilation succeeded.
    """
    tex_path = Path(tex_path)
    if not tex_path.exists():
        raise FileNotFoundError(f"TeX file not found: {tex_path}")

    working_dir = tex_path.parent

    # Check if pdflatex is available
    if not shutil.which("pdflatex"):
        print("Warning: pdflatex not found. Skipping PDF compilation.")
        return False

    try:
        # Run pdflatex twice for cross-references
        for _ in range(2):
            result = subprocess.run(
                ["pdflatex", "-interaction=batchmode",
                 "-output-directory", str(working_dir),
                 tex_path.name],
                cwd=str(working_dir),
                capture_output=True,
                timeout=60,
            )

        pdf_path = tex_path.with_suffix(".pdf")

        if clean:
            # Remove auxiliary files
            for ext in [".aux", ".log", ".out", ".nav", ".snm", ".toc"]:
                aux = tex_path.with_suffix(ext)
                if aux.exists():
                    aux.unlink()

        return pdf_path.exists()

    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"Error compiling LaTeX: {e}")
        return False

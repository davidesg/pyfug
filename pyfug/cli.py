"""
Command-Line Interface for pyfug.

Maintains backward compatibility with original FUG CLI while
adding Python-style options.
"""

from __future__ import annotations

import sys
import argparse
from pathlib import Path

from pyfug import __version__
from pyfug.io import read_inp
from pyfug.graphics.engine import diffgraph, diffgraph_set


def main():
    """Main entry point for the pyfug CLI."""
    parser = argparse.ArgumentParser(
        prog="pyfug",
        description="Jenkins-Treadway High-Definition Time Series Graphics",
        epilog="Copyright (C) 2024-2025 David E. Guerrero & Arthur B. Treadway",
    )

    parser.add_argument("input", help="Input file (.inp, .csv, .xlsx)")
    parser.add_argument("mode", nargs="?", default="one",
                        choices=["one", "set"],
                        help="Graph mode: 'one' (single) or 'set' (identification set)")

    # Set mode arguments
    parser.add_argument("set_args", nargs="*", default=[],
                        help="For 'set' mode: max_nrdiff max_nadiff")

    # Plot type flags
    parser.add_argument("-a", "--series", action="store_true",
                        help="Plot the time series")
    parser.add_argument("-b", "--acf", action="store_true",
                        help="Plot the ACF/PACF")
    parser.add_argument("-c", "--combined", action="store_true",
                        help="Plot combined series + ACF/PACF")
    parser.add_argument("-d", "--histogram", action="store_true",
                        help="Plot histogram")
    parser.add_argument("-e", "--meandev", action="store_true",
                        help="Plot mean-deviation chart")
    parser.add_argument("-H", "--include-md", action="store_true",
                        help="Include mean-deviation in identification set")

    # Parameters
    parser.add_argument("-l", "--lags", type=int, default=0,
                        help="Number of ACF/PACF lags")
    parser.add_argument("-m", "--md-groups", type=int, default=0,
                        help="Number of obs per group for mean-deviation")
    parser.add_argument("-f", "--cbands", type=float, default=0.0,
                        help="Confidence band half-width for ACF/PACF")
    parser.add_argument("-g", "--npar", type=int, default=0,
                        help="Number of ARMA parameters")

    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output directory")
    parser.add_argument("--format", type=str, default="pdf",
                        choices=["pdf", "png", "svg", "eps"],
                        help="Output format (default: pdf)")
    parser.add_argument("-V", "--version", action="version",
                        version=f"pyfug {__version__}")

    args = parser.parse_args()

    # ── Parse input file ───────────────────────────────────
    input_path = Path(args.input)
    if not input_path.exists():
        # Try with .inp extension
        input_path = input_path.with_suffix(".inp")
        if not input_path.exists():
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)

    # Detect file type and read accordingly
    suffix = input_path.suffix.lower()
    
    if suffix in ('.xlsx', '.xls'):
        try:
            from pyfug.io import read_excel
            # Auto-detect first numeric column
            import pandas as pd
            df_preview = pd.read_excel(str(input_path), nrows=3)
            data_col = 0
            for c in range(df_preview.shape[1]):
                if pd.api.types.is_numeric_dtype(df_preview.iloc[:, c]):
                    data_col = c
                    break
            ser = read_excel(str(input_path), name=input_path.stem, freq=12,
                           column=data_col)
            outname = input_path.stem
        except Exception as e:
            print(f"Error reading Excel file: {e}", file=sys.stderr)
            sys.exit(1)
    elif suffix == '.csv':
        try:
            from pyfug.io import read_csv
            ser = read_csv(str(input_path), name=input_path.stem)
            outname = input_path.stem
        except Exception as e:
            print(f"Error reading CSV file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Try .inp first, then CSV
        try:
            ser = read_inp(str(input_path))
            outname = input_path.stem
        except Exception:
            try:
                from pyfug.io import read_csv
                ser = read_csv(str(input_path), name=input_path.stem)
                outname = input_path.stem
            except Exception as e:
                print(f"Error reading input file: {e}", file=sys.stderr)
                sys.exit(1)

    # ── Parse mode ─────────────────────────────────────────
    mode = args.mode

    # Legacy: "set" with numeric args
    max_nrdiff = 2
    max_nadiff = 1
    if mode == "set" and len(args.set_args) >= 2:
        try:
            max_nrdiff = int(args.set_args[0])
            max_nadiff = int(args.set_args[1])
        except ValueError:
            print("Error: 'set' mode requires two integers: max_nrdiff max_nadiff",
                  file=sys.stderr)
            sys.exit(1)

    # ── Extract parameters from input file if available ────
    boxlam = getattr(ser, "boxlam", 1.0)
    if boxlam == 0.0:
        boxlam = 0.0  # preserve log
    boxm = 0.0
    boxgeom = 0

    # Override with original input file's Box-Cox params
    nrdiff = getattr(ser, "d", 0)
    nadiff = getattr(ser, "ds", 0)
    ifadf = [0] * (ser.freq // 2 + 1) if ser.freq > 1 else None

    # ── Output directory ───────────────────────────────────
    output_dir = args.output or "."

    # ── Determine plot types ───────────────────────────────
    case_a = args.series
    case_b = args.acf
    case_c = args.combined
    case_d = args.histogram
    case_e = args.meandev
    case_h = args.include_md

    # Default: if no flags given, do combined plot
    if not any([case_a, case_b, case_c, case_d, case_e, case_h]):
        case_c = True

    # ── Run ────────────────────────────────────────────────
    print(f"pyfug {__version__}")
    print(f"Input: {input_path}")
    print(f"Mode: {mode}")
    print(f"Series: {ser.name}, nobs={ser.nobs}, freq={ser.freq}")
    print()

    if mode == "one":
        result = diffgraph(
            ser,
            nparma=args.npar,
            boxlam=boxlam,
            boxm=boxm,
            boxgeom=boxgeom,
            nrdiff=nrdiff,
            nadiff=nadiff,
            ifadf=ifadf,
            lags=args.lags,
            cbands=args.cbands,
            m_dt_nog=args.md_groups,
            outname=outname,
            case_a=case_a,
            case_b=case_b,
            case_c=case_c,
            case_d=case_d,
            case_e=case_e,
            case_h=case_h,
            output_dir=output_dir,
        )
        print(f"Generated {len(result['files'])} file(s):")
        for f in result["files"]:
            print(f"  {f}")
    else:
        results = diffgraph_set(
            ser,
            boxlam=boxlam,
            boxm=boxm,
            boxgeom=boxgeom,
            max_nrdiff=max_nrdiff,
            max_nadiff=max_nadiff,
            ifadf=ifadf,
            lags=args.lags,
            cbands=args.cbands,
            m_dt_nog=args.md_groups,
            outname=outname,
            case_a=case_a,
            case_b=case_b,
            case_c=case_c,
            case_d=case_d,
            case_e=case_e,
            case_h=case_h,
            output_dir=output_dir,
        )
        total_files = sum(len(r["files"]) for r in results)
        print(f"Generated {total_files} file(s) across {len(results)} combinations:")
        for r in results:
            for f in r["files"]:
                print(f"  {f}")


if __name__ == "__main__":
    main()

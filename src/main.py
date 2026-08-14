import sys
import argparse
import logging
import pathlib
from src.pipeline import PIIRedactionPipeline

def setup_logging(verbose: bool) -> None:
    """Configures the logging format and level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def main() -> None:
    """Main CLI entrypoint for the PII Redaction Tool."""
    parser = argparse.ArgumentParser(
        description="Redact PII from DOCX documents pseudonymously."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input DOCX document."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path where the redacted output DOCX should be saved."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed debug-level logging."
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output)

    # 1. Validation checks
    if not input_path.exists():
        logging.error("Input file '%s' does not exist.", input_path)
        sys.exit(1)

    if input_path.suffix.lower() != ".docx":
        logging.error("Input file must be a Microsoft Word Document (.docx) file.")
        sys.exit(1)

    if input_path.resolve() == output_path.resolve():
        logging.error("Input path and Output path cannot be the same file.")
        sys.exit(1)

    logging.info("Starting PII Redaction Pipeline.")
    logging.info("Input file:  %s", input_path)
    logging.info("Output file: %s", output_path)

    try:
        # 2. Instantiate and run orchestrator
        pipeline = PIIRedactionPipeline()
        result = pipeline.run(
            input_path=str(input_path),
            output_path=str(output_path)
        )

        # 3. Print execution summary report (ensuring no raw PII leaks)
        print("\n==================================================")
        print("PII REDACTION PIPELINE SUMMARY")
        print("==================================================")
        print(f"Input File:          {result.input_path}")
        print(f"Output File:         {result.output_path}")
        print(f"Segments Processed:  {result.segments_processed}")
        print(f"Candidates Detected: {result.candidates_detected}")
        print(f"Candidates Accepted: {result.candidates_accepted}")
        print(f"Candidates Rejected: {result.candidates_rejected}")
        print("\nPII Entities Redacted by Type:")
        print("------------------------------")
        for pii_type, count in result.counts_by_type.items():
            print(f"{pii_type:15}: {count}")
        print("==================================================\n")

    except Exception as e:
        logging.critical("Pipeline execution failed with exception: %s", str(e), exc_info=args.verbose)
        sys.exit(1)

if __name__ == "__main__":
    main()

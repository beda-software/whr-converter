#!/usr/bin/env python3
"""
FHIR to HL7v2 Converter CLI

Converts FHIR Patient resources to HL7v2 ADT_A01 messages.
"""

import json
import argparse
import sys
from whr_converter.fhir_to_hl7 import FHIRToHL7Converter


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Convert FHIR Patient resources to HL7v2 ADT_A01 messages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fhir_to_hl7_converter.py patient.json
  python fhir_to_hl7_converter.py patient.json -o output.hl7
  python fhir_to_hl7_converter.py patient.json --pretty
        """,
    )

    parser.add_argument("input_file", help="Path to FHIR Patient JSON file")

    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")

    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print the HL7v2 message (adds line breaks)",
    )

    args = parser.parse_args()

    try:
        # Read FHIR patient data
        with open(args.input_file, "r", encoding="utf-8") as f:
            fhir_patient = json.load(f)

        # Validate it's a Patient resource
        if fhir_patient.get("resourceType") != "Patient":
            print(
                "Error: Input file must contain a FHIR Patient resource",
                file=sys.stderr,
            )
            sys.exit(1)

        # Convert to HL7v2
        converter = FHIRToHL7Converter()
        hl7_message = converter.convert_patient(fhir_patient)

        # Format output
        if args.pretty:
            # Add line breaks after each segment
            formatted_message = hl7_message.replace("\r", "\n")
        else:
            formatted_message = hl7_message

        # Output result
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(formatted_message)
            print(f"HL7v2 message written to {args.output}")
        else:
            print(formatted_message)

    except FileNotFoundError:
        print(f"Error: File '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

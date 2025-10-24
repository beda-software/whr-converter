#!/usr/bin/env python3
"""
CLI tool to convert JSON patient data to HL7v2 ADT_A01 messages.
Usage: python json_to_hl7_converter.py <input.json> [output.hl7]
"""

import json
import sys
import argparse
from datetime import datetime
from hl7apy.core import Message, Segment


def map_gender_code(gender_code):
    """Map numeric gender code to HL7v2 format"""
    gender_map = {1: "M", 2: "F", 3: "O", 4: "U"}  # Male  # Female  # Other  # Unknown
    return gender_map.get(gender_code, "U")


def format_hl7_datetime(date_str):
    """Convert ISO date string to HL7v2 datetime format"""
    try:
        # Parse the date string
        if "T" in date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(date_str)

        # Format as YYYYMMDDHHMMSS+/-HHMM
        return dt.strftime("%Y%m%d%H%M%S%z").replace("+", "+").replace("-", "-")
    except:
        # Fallback to current time if parsing fails
        return datetime.now().strftime("%Y%m%d%H%M%S%z")


def format_phone_number(phone):
    """Format phone number for HL7v2"""
    if not phone:
        return ""

    # Remove any non-digit characters except +
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+")

    # If it starts with +61, format as Australian number
    if cleaned.startswith("+61"):
        return f"^{cleaned[3:]}^PRN^PH^^61^61^{cleaned[3:]}"
    elif cleaned.startswith("61") and len(cleaned) > 10:
        return f"^{cleaned[2:]}^PRN^PH^^61^61^{cleaned[2:]}"
    elif cleaned.startswith("0") and len(cleaned) == 10:
        return f"^{cleaned[1:]}^PRN^PH^^61^61^{cleaned[1:]}"
    else:
        return f"^{cleaned}^PRN^PH"


def create_hl7_message(patient_data):
    """Create HL7v2 ADT_A01 message from patient JSON data"""

    # Create MSH Segment
    msg = Message("ADT_A01")
    msg.msh.msh_1 = "|"
    msg.msh.msh_2 = "^~\\&"
    msg.msh.msh_3 = "Beda EMR"
    msg.msh.msh_4 = "The Practice"
    msg.msh.msh_5 = "ViewPoint"
    msg.msh.msh_6 = ""
    msg.msh.msh_7 = format_hl7_datetime(
        patient_data.get("createdDateTime", datetime.now().isoformat())
    )
    msg.msh.msh_8 = ""
    msg.msh.msh_9 = "ADT^A08"
    msg.msh.msh_10 = patient_data.get("id", "")
    msg.msh.msh_11 = "P"
    msg.msh.msh_12 = "2.3.1^AUS&&ISO^AS4700.2&&L"

    # Create EVN Segment
    evn = Segment("EVN")
    evn.evn_1 = "A08"
    evn.evn_2 = format_hl7_datetime(
        patient_data.get("createdDateTime", datetime.now().isoformat())
    )
    evn.evn_3 = ""

    # Create PID Segment
    pid = Segment("PID")
    pid.pid_1 = "1"
    pid.pid_2 = ""
    pid.pid_3 = f"{patient_data.get('id', '')}^^^Local"

    # Patient name
    pid.pid_5.pid_5_1 = patient_data.get("lastName", "") or ""
    pid.pid_5.pid_5_2 = patient_data.get("firstName", "") or ""
    pid.pid_5.pid_5_3 = patient_data.get("middleName", "") or ""
    pid.pid_5.pid_5_4 = patient_data.get("preferredName", "") or ""
    pid.pid_5.pid_5_5 = "Dr" if patient_data.get("titleCode") else ""

    # Date of birth
    dob = patient_data.get("dob", "")
    if dob:
        try:
            dob_dt = datetime.fromisoformat(dob)
            pid.pid_7 = dob_dt.strftime("%Y%m%d%H%M%S")
        except:
            pid.pid_7 = dob.replace("-", "")
    else:
        pid.pid_7 = ""

    # Gender
    pid.pid_8 = map_gender_code(patient_data.get("genderCode"))

    # Race/ethnicity (using ethnicityCode if available)
    pid.pid_10 = f"{patient_data.get('ethnicityCode', '')}^^NHDDV10-000001"

    # Address (placeholder - not in JSON)
    pid.pid_11 = "^^^VIC^^^O"

    # Phone numbers
    phone_parts = []
    if patient_data.get("homePhone"):
        phone_parts.append(format_phone_number(patient_data["homePhone"]))
    if patient_data.get("mobilePhone"):
        phone_parts.append(format_phone_number(patient_data["mobilePhone"]))
    if patient_data.get("workPhone"):
        phone_parts.append(format_phone_number(patient_data["workPhone"]))
    if patient_data.get("email"):
        phone_parts.append(f"^NET^Internet^{patient_data['email']}")

    pid.pid_13 = "~".join(phone_parts) if phone_parts else ""

    # Additional phone (work phone if different from mobile)
    if patient_data.get("workPhone") and patient_data.get(
        "workPhone"
    ) != patient_data.get("mobilePhone"):
        pid.pid_14 = format_phone_number(patient_data["workPhone"])
    else:
        pid.pid_14 = ""

    # Patient account number
    pid.pid_16 = "0"

    # Create PV1 Segment
    pv1 = Segment("PV1")
    pv1.pv1_1 = "1"
    pv1.pv1_2 = "N"
    pv1.pv1_8 = (
        f"{patient_data.get('usualDoctorId', '')}^Doctor^Name^^^Dr^^^AUSHICPR^L^^^UPIN"
    )

    # Add segments to message
    msg.add(evn)
    msg.add(pid)
    msg.add(pv1)

    return msg


def main():
    parser = argparse.ArgumentParser(
        description="Convert JSON patient data to HL7v2 ADT_A01 message"
    )
    parser.add_argument("input_file", help="Input JSON file path")
    parser.add_argument(
        "output_file", nargs="?", help="Output HL7 file path (optional)"
    )
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty print the HL7 message"
    )

    args = parser.parse_args()

    try:
        # Read JSON file
        with open(args.input_file, "r") as f:
            patient_data = json.load(f)

        # Create HL7 message
        hl7_msg = create_hl7_message(patient_data)

        # Convert to ER7 format
        hl7_str = hl7_msg.to_er7()

        # Output
        if args.output_file:
            with open(args.output_file, "w") as f:
                f.write(hl7_str)
            print(f"HL7 message written to {args.output_file}")
        else:
            if args.pretty:
                # Pretty print with line breaks
                lines = hl7_str.split("\r")
                for i, line in enumerate(lines):
                    if line.strip():
                        print(f"Line {i+1}: {line}")
            else:
                print(hl7_str)

    except FileNotFoundError:
        print(f"Error: File '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{args.input_file}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
FHIR to HL7v2 Converter CLI

Converts FHIR Patient resources to HL7v2 ADT_A01 messages.
"""

import json
import argparse
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from hl7apy.core import Message, Segment


class FHIRToHL7Converter:
    """Converts FHIR Patient resources to HL7v2 ADT_A01 messages."""
    
    def __init__(self):
        self.message_type = "ADT_A01"
        self.sending_app = "FHIR Converter"
        self.sending_facility = "FHIR System"
        self.receiving_app = "HL7 System"
        self.receiving_facility = "HL7 Facility"
    
    def convert_patient(self, fhir_patient: Dict[str, Any]) -> str:
        """
        Convert FHIR Patient resource to HL7v2 ADT_A01 message.
        
        Args:
            fhir_patient: FHIR Patient resource as dictionary
            
        Returns:
            HL7v2 message as string
        """
        try:
            # Create the main message
            msg = Message(self.message_type)
            
            # Create segments
            self._create_msh_segment(msg, fhir_patient)
            self._create_evn_segment(msg)
            self._create_pid_segment(msg, fhir_patient)
            self._create_pv1_segment(msg)
            
            return msg.to_er7()
            
        except Exception as e:
            raise ValueError(f"Error converting FHIR patient to HL7v2: {str(e)}")
    
    def _create_msh_segment(self, msg: Message, fhir_patient: Dict[str, Any]) -> None:
        """Create MSH (Message Header) segment."""
        msg.msh.msh_1 = "|"
        msg.msh.msh_2 = "^~\\&"
        msg.msh.msh_3 = self.sending_app
        msg.msh.msh_4 = self.sending_facility
        msg.msh.msh_5 = self.receiving_app
        msg.msh.msh_6 = self.receiving_facility
        msg.msh.msh_7 = datetime.now().strftime("%Y%m%d%H%M%S%z")
        msg.msh.msh_8 = ""
        msg.msh.msh_9 = "ADT^A08"
        
        # Use IHI as control ID if available
        patient_id = self._get_patient_identifier(fhir_patient)
        msg.msh.msh_10 = patient_id
        msg.msh.msh_11 = "P"
        msg.msh.msh_12 = "2.3.1^AUS&&ISO^AS4700.2&&L"
    
    def _create_evn_segment(self, msg: Message) -> None:
        """Create EVN (Event Type) segment."""
        evn = Segment("EVN")
        evn.evn_1 = "A08"  # Update patient information
        evn.evn_2 = datetime.now().strftime("%Y%m%d%H%M%S")
        evn.evn_3 = ""
        msg.add(evn)
    
    def _create_pid_segment(self, msg: Message, fhir_patient: Dict[str, Any]) -> None:
        """Create PID (Patient Identification) segment."""
        pid = Segment("PID")
        
        # Set ID (1)
        patient_id = self._get_patient_identifier(fhir_patient)
        pid.pid_1 = "1"
        pid.pid_2 = ""
        pid.pid_3 = f"{patient_id}^^{self._get_ihi_system()}^Local"
        
        # Patient name (5)
        name = self._get_patient_name(fhir_patient)
        if name:
            pid.pid_5.pid_5_1 = name.get('family', '')
            given_names = name.get('given', [])
            if given_names:
                pid.pid_5.pid_5_2 = given_names[0] if len(given_names) > 0 else ''
                pid.pid_5.pid_5_3 = given_names[1] if len(given_names) > 1 else ''
            pid.pid_5.pid_5_5 = name.get('prefix', [''])[0] if name.get('prefix') else ''
        
        # Birth date (7)
        birth_date = fhir_patient.get('birthDate', '')
        if birth_date:
            # Convert YYYY-MM-DD to YYYYMMDDHHMMSS format
            try:
                parsed_date = datetime.strptime(birth_date, "%Y-%m-%d")
                pid.pid_7 = parsed_date.strftime("%Y%m%d000000+1000")
            except ValueError:
                pid.pid_7 = birth_date
        
        # Gender (8)
        gender = fhir_patient.get('gender', '').upper()
        if gender in ['MALE', 'FEMALE']:
            pid.pid_8 = gender[0]  # M or F
        else:
            pid.pid_8 = 'U'  # Unknown
        
        # Race (10) - using Australian terminology
        pid.pid_10 = "9^^NHDDV10-000001"  # Default Australian race code
        
        # Address (11)
        address = self._get_patient_address(fhir_patient)
        if address:
            address_parts = []
            if address.get('line'):
                address_parts.append('^'.join(address['line']))
            else:
                address_parts.append('')
            address_parts.append(address.get('city', ''))
            address_parts.append(address.get('state', ''))
            address_parts.append(address.get('postalCode', ''))
            address_parts.append('')
            address_parts.append('')
            address_parts.append(address.get('country', 'AU'))
            pid.pid_11 = '^'.join(address_parts)
        
        # Phone numbers (13)
        telecom = self._format_telecom(fhir_patient.get('telecom', []))
        if telecom:
            pid.pid_13 = telecom
        
        # Additional phone numbers (14)
        additional_phones = self._get_additional_phones(fhir_patient.get('telecom', []))
        if additional_phones:
            pid.pid_14 = additional_phones
        
        # Marital status (16)
        pid.pid_16 = "0"  # Unknown
        
        msg.add(pid)
    
    def _create_pv1_segment(self, msg: Message) -> None:
        """Create PV1 (Patient Visit) segment."""
        pv1 = Segment("PV1")
        pv1.pv1_1 = "1"  # Patient class
        pv1.pv1_2 = "N"  # Assigned patient location
        pv1.pv1_8 = "FHIR^Converter^System^^^Dr^^^AUSHICPR^L^^^UPIN"
        msg.add(pv1)
    
    def _get_patient_identifier(self, fhir_patient: Dict[str, Any]) -> str:
        """Extract patient identifier, preferring IHI."""
        identifiers = fhir_patient.get('identifier', [])
        
        # Look for IHI first
        for identifier in identifiers:
            if identifier.get('type', {}).get('text') == 'IHI':
                return identifier.get('value', '')
        
        # Fall back to first identifier or patient ID
        if identifiers:
            return identifiers[0].get('value', '')
        
        return fhir_patient.get('id', 'UNKNOWN')
    
    def _get_ihi_system(self) -> str:
        """Get IHI system identifier."""
        return "http://ns.electronichealth.net.au/id/hi/ihi/1.0"
    
    def _get_patient_name(self, fhir_patient: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract patient name from FHIR resource."""
        names = fhir_patient.get('name', [])
        if not names:
            return None
        
        # Prefer 'usual' name, fall back to first name
        for name in names:
            if name.get('use') == 'usual':
                return name
        
        return names[0]
    
    def _get_patient_address(self, fhir_patient: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract patient address from FHIR resource."""
        addresses = fhir_patient.get('address', [])
        if not addresses:
            return None
        
        # Return first address
        return addresses[0]
    
    def _format_telecom(self, telecom_list: List[Dict[str, Any]]) -> str:
        """Format telecom information for HL7v2."""
        if not telecom_list:
            return ""
        
        formatted_contacts = []
        
        for contact in telecom_list:
            system = contact.get('system', '')
            value = contact.get('value', '')
            use = contact.get('use', '')
            
            if not value:
                continue
            
            # Map FHIR telecom use to HL7v2 codes
            hl7_use = self._map_telecom_use(use)
            
            if system == 'phone':
                # Format: number^use^type^country_code^area_code^number^extension
                formatted_contacts.append(f"{value}^{hl7_use}^PH^^61^07^{value}")
            elif system == 'email':
                # Format: email^NET^Internet^email
                formatted_contacts.append(f"{value}^NET^Internet^{value}")
        
        return '~'.join(formatted_contacts)
    
    def _map_telecom_use(self, fhir_use: str) -> str:
        """Map FHIR telecom use to HL7v2 use codes."""
        mapping = {
            'home': 'H',
            'work': 'W',
            'mobile': 'M',
            'temp': 'T',
            'old': 'O'
        }
        return mapping.get(fhir_use, 'PRN')  # Default to PRN (Primary)
    
    def _get_additional_phones(self, telecom_list: List[Dict[str, Any]]) -> str:
        """Get additional phone numbers for PID.14."""
        phone_contacts = []
        
        for contact in telecom_list:
            if contact.get('system') == 'phone' and contact.get('value'):
                use = contact.get('use', '')
                value = contact.get('value', '')
                hl7_use = self._map_telecom_use(use)
                phone_contacts.append(f"{value}^{hl7_use}^PH^^61^07^{value}")
        
        return '~'.join(phone_contacts[1:])  # Skip first phone (already in PID.13)


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
        """
    )
    
    parser.add_argument(
        'input_file',
        help='Path to FHIR Patient JSON file'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: stdout)'
    )
    
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty print the HL7v2 message (adds line breaks)'
    )
    
    args = parser.parse_args()
    
    try:
        # Read FHIR patient data
        with open(args.input_file, 'r', encoding='utf-8') as f:
            fhir_patient = json.load(f)
        
        # Validate it's a Patient resource
        if fhir_patient.get('resourceType') != 'Patient':
            print("Error: Input file must contain a FHIR Patient resource", file=sys.stderr)
            sys.exit(1)
        
        # Convert to HL7v2
        converter = FHIRToHL7Converter()
        hl7_message = converter.convert_patient(fhir_patient)
        
        # Format output
        if args.pretty:
            # Add line breaks after each segment
            formatted_message = hl7_message.replace('\r', '\n')
        else:
            formatted_message = hl7_message
        
        # Output result
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
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
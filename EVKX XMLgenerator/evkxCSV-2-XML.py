#!/usr/bin/env python3
"""
CSV to XML Charging Curve Converter

Converts CSV files containing vehicle charging data to XML format.
Expects CSV files with metadata in first rows and charging curve data below.
"""

import os
import sys
import csv
import re
from pathlib import Path


def find_csv_files():
    """Find all CSV files in the inputFiles directory."""
    input_dir = Path("inputFiles")
    
    if not input_dir.exists():
        print("Creating inputFiles directory...")
        input_dir.mkdir()
        print("Please place your CSV files in the 'inputFiles' directory and run the script again.")
        return []
    
    csv_files = list(input_dir.glob("*.csv"))
    return csv_files


def display_file_menu(csv_files):
    """Display numbered list of CSV files and get user selection."""
    if not csv_files:
        return []
    
    print("\nAvailable CSV files:")
    print("-" * 40)
    for i, file_path in enumerate(csv_files, 1):
        print(f"{i}. {file_path.name}")
    
    print("\nEnter the numbers of files to convert (e.g., '1,3,5' or '1-3' or 'all'):")
    user_input = input("Selection: ").strip().lower()
    
    if user_input == 'all':
        return list(range(len(csv_files)))
    
    selected_indices = []
    
    # Parse comma-separated values and ranges
    parts = user_input.replace(' ', '').split(',')
    for part in parts:
        try:
            if '-' in part:
                # Handle ranges like "1-3"
                start, end = map(int, part.split('-'))
                selected_indices.extend(range(start-1, end))  # Convert to 0-based
            else:
                # Handle single numbers
                selected_indices.append(int(part) - 1)  # Convert to 0-based
        except ValueError:
            print(f"Invalid selection: {part}")
    
    # Filter valid indices
    valid_indices = [i for i in selected_indices if 0 <= i < len(csv_files)]
    return valid_indices


def to_camel_case(text):
    """Convert text to camelCase."""
    if not text:
        return "unknownVehicle"
    
    # Remove special characters and split into words
    words = re.findall(r'\b\w+\b', text)
    if not words:
        return "unknownVehicle"
    
    # First word lowercase, rest capitalized
    camel_case = words[0].lower()
    for word in words[1:]:
        camel_case += word.capitalize()
    
    return camel_case


def get_user_confirmation(prompt, default="y"):
    """Get yes/no confirmation from user."""
    valid_responses = {"y": True, "yes": True, "n": False, "no": False}
    
    while True:
        response = input(f"{prompt} [{default}]: ").strip().lower()
        if not response:
            response = default
        
        if response in valid_responses:
            return valid_responses[response]
        
        print("Please enter 'y' for yes or 'n' for no.")


def confirm_vehicle_details(metadata, csv_filename):
    """Confirm vehicle name and generate output filename."""
    csv_name = metadata.get('name', '').strip()
    
    print(f"\n--- Processing: {csv_filename} ---")
    
    # Confirm vehicle name
    if csv_name:
        print(f"Vehicle name from CSV: '{csv_name}'")
        use_csv_name = get_user_confirmation("Use this name?", "y")
        
        if use_csv_name:
            vehicle_name = csv_name
        else:
            vehicle_name = input("Enter vehicle name: ").strip()
            if not vehicle_name:
                print("No name entered, using CSV name.")
                vehicle_name = csv_name
    else:
        print("No vehicle name found in CSV.")
        vehicle_name = input("Enter vehicle name: ").strip()
        if not vehicle_name:
            vehicle_name = "Unknown Vehicle"
    
    # Generate camelCase filename
    suggested_filename = to_camel_case(vehicle_name)
    print(f"Suggested filename: '{suggested_filename}.xml'")
    
    use_suggested = get_user_confirmation("Use this filename?", "y")
    
    if use_suggested:
        output_filename = suggested_filename
    else:
        custom_filename = input("Enter filename (without .xml): ").strip()
        if custom_filename:
            # Clean the filename to be safe
            output_filename = re.sub(r'[^\w\-_]', '', custom_filename)
        else:
            output_filename = suggested_filename
    
    return vehicle_name, output_filename


def parse_csv_file(file_path):
    """Parse CSV file and extract metadata and charging curve data."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        if not lines:
            return None, None, "File is empty"
        
        # Extract metadata from first few lines
        metadata = {}
        data_start_line = 0
        
        for i, line in enumerate(lines):
            if 'Battery State of Charge' in line or 'SOC' in line:
                data_start_line = i
                break
            
            # Parse metadata lines
            parts = [part.strip() for part in line.split(',')]
            if len(parts) >= 2 and parts[0] and parts[1]:
                # Handle BOM character that might be at the start of the file
                key = parts[0].lstrip('\ufeff')
                metadata[key] = parts[1]
        
        if data_start_line == 0 and len(lines) > 5:
            return None, None, "Could not find charging data header"
        
        # Extract charging curve data
        charging_data = []
        
        try:
            reader = csv.DictReader(lines[data_start_line:])
            row_count = 0
            
            for row in reader:
                try:
                    row_count += 1
                    
                    # Try different possible column names
                    soc_key = None
                    power_key = None
                    time_key = None
                    energy_key = None
                    
                    for key in row.keys():
                        if 'State of Charge' in key or 'SOC' in key:
                            soc_key = key
                        elif 'Charging Speed' in key or 'Power' in key:
                            power_key = key
                        elif 'Time' in key:
                            time_key = key
                        elif 'Energy' in key:
                            energy_key = key
                    
                    if not all([soc_key, power_key, time_key, energy_key]):
                        if row_count == 1:  # Only warn on first row
                            print(f"Warning: Could not identify all required columns in {file_path.name}")
                        continue
                    
                    # Clean up the data
                    soc_str = str(row[soc_key]).replace('%', '').strip()
                    if not soc_str:
                        continue
                        
                    soc = int(float(soc_str))
                    power = int(float(row[power_key]))
                    time = float(row[time_key])
                    energy = float(row[energy_key])
                    
                    charging_data.append({
                        'soc': soc,
                        'power': power,
                        'time': time,
                        'energy': energy
                    })
                    
                except (ValueError, KeyError, TypeError) as e:
                    # Skip invalid rows silently (common in CSV files)
                    continue
            
            if not charging_data:
                return None, None, "No valid charging data found"
                
        except Exception as e:
            return None, None, f"Error reading charging data: {str(e)}"
        
        return metadata, charging_data, None
        
    except FileNotFoundError:
        return None, None, "File not found"
    except PermissionError:
        return None, None, "Permission denied reading file"
    except Exception as e:
        return None, None, f"Unexpected error reading file: {str(e)}"


def create_xml_content(metadata, charging_data, vehicle_name):
    """Create XML content from metadata and charging data."""
    # Get range and speed from metadata with defaults
    range_miles = metadata.get('range_miles', '0')
    range_speed = metadata.get('range_speed_mph', '70')
    
    xml_lines = ['<?xml version="1.0" ?>']
    xml_lines.append('<vehicle>')
    xml_lines.append('  <metadata>')
    xml_lines.append(f'    <name>{vehicle_name}</name>')
    xml_lines.append(f'    <range_miles>{range_miles}</range_miles>')
    xml_lines.append(f'    <range_speed_mph>{range_speed}</range_speed_mph>')
    xml_lines.append('  </metadata>')
    xml_lines.append('  <charging_curve unit_time="minutes" unit_power="kW" unit_energy="kWh">')
    
    # Add charging curve points
    for point in charging_data:
        xml_lines.append(f'    <point soc="{point["soc"]}" power="{point["power"]}" '
                        f'time="{point["time"]:.2f}" energy="{point["energy"]}"/>')
    
    xml_lines.append('  </charging_curve>')
    xml_lines.append('</vehicle>')
    
    return '\n'.join(xml_lines)


def ensure_output_directory():
    """Ensure the outputFiles directory exists."""
    output_dir = Path("outputFiles")
    if not output_dir.exists():
        print("Creating outputFiles directory...")
        output_dir.mkdir()
    return output_dir


def convert_files(csv_files, selected_indices):
    """Convert selected CSV files to XML."""
    output_dir = ensure_output_directory()
    converted_count = 0
    failed_count = 0
    
    for index in selected_indices:
        if index >= len(csv_files):
            continue
            
        csv_file = csv_files[index]
        
        try:
            # Parse CSV
            metadata, charging_data, error = parse_csv_file(csv_file)
            
            if error:
                print(f"\n❌ Failed to process {csv_file.name}: {error}")
                failed_count += 1
                continue
            
            if not charging_data:
                print(f"\n❌ No charging data found in {csv_file.name}")
                failed_count += 1
                continue
            
            # Get user confirmation for vehicle details
            vehicle_name, output_filename = confirm_vehicle_details(metadata, csv_file.name)
            
            # Create XML content
            xml_content = create_xml_content(metadata, charging_data, vehicle_name)
            
            # Create output path
            output_path = output_dir / f"{output_filename}.xml"
            
            # Check if file already exists
            if output_path.exists():
                overwrite = get_user_confirmation(f"File '{output_path.name}' already exists. Overwrite?", "n")
                if not overwrite:
                    print(f"Skipped {csv_file.name}")
                    continue
            
            # Write XML file
            with open(output_path, 'w', encoding='utf-8') as xml_file:
                xml_file.write(xml_content)
            
            print(f"✅ Created: {output_path.name} ({len(charging_data)} data points)")
            converted_count += 1
            
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error processing {csv_file.name}: {str(e)}")
            failed_count += 1
    
    return converted_count, failed_count


def main():
    """Main function."""
    print("CSV to XML Charging Curve Converter")
    print("=" * 40)
    
    try:
        # Find CSV files
        csv_files = find_csv_files()
        
        if not csv_files:
            print("No CSV files found in inputFiles directory.")
            return
        
        # Display menu and get selection
        selected_indices = display_file_menu(csv_files)
        
        if not selected_indices:
            print("No files selected.")
            return
        
        print(f"\nSelected {len(selected_indices)} file(s) for conversion.")
        proceed = get_user_confirmation("Proceed with conversion?", "y")
        
        if not proceed:
            print("Conversion cancelled.")
            return
        
        # Convert files
        converted_count, failed_count = convert_files(csv_files, selected_indices)
        
        # Summary
        print(f"\n" + "=" * 40)
        print(f"Conversion complete!")
        print(f"✅ Successfully converted: {converted_count} file(s)")
        if failed_count > 0:
            print(f"❌ Failed to convert: {failed_count} file(s)")
        print(f"XML files saved to outputFiles directory.")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print("Please check your CSV files and try again.")
        return


if __name__ == "__main__":
    main()
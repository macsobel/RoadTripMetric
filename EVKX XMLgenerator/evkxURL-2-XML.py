#!/usr/bin/env python3
"""
URL to XML Charging Curve Converter

Converts vehicle charging data from EVKX.net URLs to XML format.
Can also process CSV files as a fallback option.
"""

import os
import sys
import csv
import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def get_user_input_method():
    """Ask user whether to use URL or CSV file input."""
    print("Choose input method:")
    print("1. Scrape from URL (EVKX.net)")
    print("2. Process CSV files")
    
    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice in ['1', '2']:
            return choice
        print("Please enter '1' for URL or '2' for CSV files.")


def get_url_from_user():
    """Get and validate URL from user."""
    while True:
        url = input("Enter the EVKX.net charging curve URL: ").strip()
        
        if not url:
            print("Please enter a URL.")
            continue
            
        # Basic URL validation
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                print("Please enter a valid URL (including http:// or https://).")
                continue
                
            if 'evkx.net' not in parsed.netloc.lower():
                print("Warning: This script is designed for EVKX.net URLs.")
                proceed = get_user_confirmation("Continue anyway?", "n")
                if not proceed:
                    continue
                    
            return url
            
        except Exception:
            print("Invalid URL format. Please try again.")


def scrape_charging_data(url):
    """Scrape charging curve data from EVKX.net URL."""
    try:
        print(f"Fetching data from: {url}")
        
        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract vehicle name from title or h1
        vehicle_name = "Unknown Vehicle"
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text()
            # Extract vehicle name from title (usually before "charging curve")
            match = re.search(r'^(.+?)\s+charging curve', title_text, re.IGNORECASE)
            if match:
                vehicle_name = match.group(1).strip()
        
        # Look for h1 tag as alternative
        if vehicle_name == "Unknown Vehicle":
            h1_tag = soup.find('h1')
            if h1_tag:
                h1_text = h1_tag.get_text()
                match = re.search(r'^(.+?)\s+charging curve', h1_text, re.IGNORECASE)
                if match:
                    vehicle_name = match.group(1).strip()
        
        # Extract metadata from the page
        metadata = {'name': vehicle_name}
        
        # Look for range information in the content
        # This might be in various formats on different pages
        page_text = soup.get_text()
        
        # Try to find range information
        range_match = re.search(r'(\d+)\s*(?:km|mi|miles)', page_text, re.IGNORECASE)
        if range_match:
            # This is a rough estimate - you might want to refine this
            metadata['range_miles'] = range_match.group(1)
        else:
            metadata['range_miles'] = '0'
        
        metadata['range_speed_mph'] = '70'  # Default value
        
        # Find the charging data table
        charging_data = []
        
        # Look for the table with SOC, Speed, Time, Energy columns
        tables = soup.find_all('table')
        
        for table in tables:
            # Check if this table has the charging data headers
            headers = []
            header_row = table.find('tr')
            if header_row:
                th_tags = header_row.find_all(['th', 'td'])
                headers = [th.get_text().strip() for th in th_tags]
                
                # Check if this looks like the charging data table
                if any('soc' in h.lower() for h in headers) and any('speed' in h.lower() for h in headers):
                    print("Found charging data table!")
                    
                    # Process all rows except the header
                    rows = table.find_all('tr')[1:]  # Skip header row
                    
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 4:
                            try:
                                # Extract data from cells
                                soc_text = cells[0].get_text().strip().replace('%', '')
                                speed_text = cells[1].get_text().strip().replace('kW', '')
                                time_text = cells[2].get_text().strip()
                                energy_text = cells[3].get_text().strip().replace('kWh', '')
                                
                                # Skip empty rows
                                if not soc_text or not speed_text:
                                    continue
                                
                                soc = int(float(soc_text))
                                power = int(float(speed_text))
                                energy = float(energy_text)
                                
                                # Convert time from HH:MM:SS to decimal minutes
                                time_minutes = parse_time_to_minutes(time_text)
                                
                                charging_data.append({
                                    'soc': soc,
                                    'power': power,
                                    'time': time_minutes,
                                    'energy': energy
                                })
                                
                            except (ValueError, IndexError) as e:
                                # Skip invalid rows
                                continue
                    
                    break  # Found the data table, stop looking
        
        if not charging_data:
            return None, None, "No charging data table found on the page"
        
        print(f"Successfully extracted {len(charging_data)} data points")
        return metadata, charging_data, None
        
    except requests.RequestException as e:
        return None, None, f"Error fetching URL: {str(e)}"
    except Exception as e:
        return None, None, f"Error parsing webpage: {str(e)}"


def parse_time_to_minutes(time_str):
    """Convert time string (HH:MM:SS or MM:SS) to decimal minutes."""
    time_str = time_str.strip()
    
    # Remove any extra characters and split by ':'
    parts = time_str.split(':')
    
    if len(parts) == 3:  # HH:MM:SS
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        return hours * 60 + minutes + seconds / 60
    elif len(parts) == 2:  # MM:SS
        minutes = int(parts[0])
        seconds = int(parts[1])
        return minutes + seconds / 60
    else:
        # Try to parse as decimal minutes
        return float(time_str)


def find_csv_files():
    """Find all CSV files in the inputFiles directory."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    input_dir = script_dir / "inputFiles"
    
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


def confirm_vehicle_details(metadata, source_name, is_url=False):
    """Confirm vehicle name and generate output filename. If is_url=True, also ask for vehicle range."""
    vehicle_name = metadata.get('name', '').strip()
    
    print(f"\n--- Processing: {source_name} ---")
    
    # Confirm vehicle name
    if vehicle_name and vehicle_name != "Unknown Vehicle":
        print(f"Vehicle name detected: '{vehicle_name}'")
        use_detected_name = get_user_confirmation("Use this name?", "y")
        
        if use_detected_name:
            final_name = vehicle_name
        else:
            final_name = input("Enter vehicle name: ").strip()
            if not final_name:
                print("No name entered, using detected name.")
                final_name = vehicle_name
    else:
        print("No vehicle name detected.")
        final_name = input("Enter vehicle name: ").strip()
        if not final_name:
            final_name = "Unknown Vehicle"
    
    # Ask for vehicle range if processing from URL
    if is_url:
        final_range = input("Enter vehicle range in miles: ").strip()
        
        # Validate and set default if empty
        try:
            if final_range:
                int(final_range)  # Validate it's a number
                metadata['range_miles'] = final_range
            else:
                print("No range entered, using default of 300 miles.")
                metadata['range_miles'] = '300'
        except ValueError:
            print("Invalid range entered, using default of 300 miles.")
            metadata['range_miles'] = '300'
    
    # Generate camelCase filename
    suggested_filename = to_camel_case(final_name)
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
    
    return final_name, output_filename


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
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    output_dir = script_dir / "outputFiles"
    if not output_dir.exists():
        print("Creating outputFiles directory...")
        output_dir.mkdir()
    return output_dir


def process_url():
    """Process a single URL."""
    url = get_url_from_user()
    
    # Scrape data from URL
    metadata, charging_data, error = scrape_charging_data(url)
    
    if error:
        print(f"\n❌ Failed to process URL: {error}")
        return False
    
    if not charging_data:
        print(f"\n❌ No charging data found at URL")
        return False
    
    # Get user confirmation for vehicle details
    vehicle_name, output_filename = confirm_vehicle_details(metadata, url, is_url=True)
    
    # Create XML content
    xml_content = create_xml_content(metadata, charging_data, vehicle_name)
    
    # Ensure output directory exists
    output_dir = ensure_output_directory()
    output_path = output_dir / f"{output_filename}.xml"
    
    # Check if file already exists
    if output_path.exists():
        overwrite = get_user_confirmation(f"File '{output_path.name}' already exists. Overwrite?", "n")
        if not overwrite:
            print(f"Cancelled processing of URL")
            return False
    
    # Write XML file
    with open(output_path, 'w', encoding='utf-8') as xml_file:
        xml_file.write(xml_content)
    
    print(f"✅ Created: {output_path.name} ({len(charging_data)} data points)")
    return True


def convert_csv_files(csv_files, selected_indices):
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
    print("Aaron's Handy URL/CSV to XML Charging Curve Converter")
    print("=" * 45)
    
    try:
        # Check if required libraries are installed
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            print("Required libraries not found!")
            print("Please install them using:")
            print("pip install requests beautifulsoup4")
            return
        
        # Get input method choice
        input_method = get_user_input_method()
        
        if input_method == '1':
            # URL processing
            print("\n--- URL Processing Mode ---")
            success = process_url()
            
            if success:
                print(f"\n" + "=" * 45)
                print(f"✅ Successfully converted URL data!")
                print(f"XML file saved to outputFiles directory.")
            else:
                print(f"\n" + "=" * 45)
                print(f"❌ Failed to convert URL data.")
                
        else:
            # CSV processing
            print("\n--- CSV Processing Mode ---")
            
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
            converted_count, failed_count = convert_csv_files(csv_files, selected_indices)
            
            # Summary
            print(f"\n" + "=" * 45)
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
        print("Please check your input and try again.")
        return


if __name__ == "__main__":
    main()
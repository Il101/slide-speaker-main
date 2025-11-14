#!/usr/bin/env python3
"""
Detailed Pipeline Testing Script
Tests the full pipeline with detailed step-by-step tracking
"""
import requests
import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration
API_URL = "http://localhost:8000"
TEST_FILE = "/Users/iliazarikov/Downloads/Kurs_10 (verschoben).pdf"
USERNAME = "test_user@example.com"
PASSWORD = "TestPass123!"  # Strong password with uppercase, lowercase, digits, special char

# Colors for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text: str):
    """Print a header"""
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(80)}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")


def print_step(step_num: int, title: str):
    """Print a step header"""
    print(f"\n{BOLD}{CYAN}[STEP {step_num}] {title}{RESET}")
    print(f"{CYAN}{'-'*80}{RESET}")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"  {text}")


def register_user(username: str, password: str) -> Dict[str, Any]:
    """Register a new user"""
    try:
        response = requests.post(
            f"{API_URL}/api/auth/register",
            json={"email": username, "password": password}
        )
        if response.status_code == 201:
            return response.json()
        elif response.status_code == 400 and "already registered" in response.text.lower():
            print_info("User already exists, will try to login")
            return {"message": "User exists"}
        else:
            print_warning(f"Registration response: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        print_warning(f"Registration failed: {e}")
        return {}


def login_user(username: str, password: str) -> Optional[str]:
    """Login and get JWT token"""
    try:
        response = requests.post(
            f"{API_URL}/api/auth/login",
            json={"email": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            # Token might be in response or in cookie
            token = data.get("access_token")
            if not token:
                # Try to get from cookies
                cookies = response.cookies
                token = cookies.get("access_token")
            return token
        else:
            print_error(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Login error: {e}")
        return None


def upload_file(token: str, file_path: str) -> Optional[str]:
    """Upload file and return lesson_id"""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'application/pdf')}
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.post(
                f"{API_URL}/upload",
                files=files,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                lesson_id = data.get('lesson_id')
                print_success(f"File uploaded successfully!")
                print_info(f"Lesson ID: {lesson_id}")
                return lesson_id
            else:
                print_error(f"Upload failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return None
    except Exception as e:
        print_error(f"Upload error: {e}")
        return None


def get_lesson_status(token: str, lesson_id: str) -> Optional[Dict[str, Any]]:
    """Get lesson processing status"""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(
            f"{API_URL}/lessons/{lesson_id}/status",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print_warning(f"Status check failed: {response.status_code}")
            return None
    except Exception as e:
        print_warning(f"Status check error: {e}")
        return None


def get_manifest(lesson_id: str) -> Optional[Dict[str, Any]]:
    """Get manifest.json from lesson directory"""
    try:
        manifest_path = Path(f".data/{lesson_id}/manifest.json")
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print_warning(f"Error reading manifest: {e}")
        return None


def analyze_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze manifest completeness"""
    analysis = {
        "total_slides": len(manifest.get("slides", [])),
        "slides_with_elements": 0,
        "slides_with_semantic_map": 0,
        "slides_with_talk_track": 0,
        "slides_with_speaker_notes": 0,
        "slides_with_audio": 0,
        "slides_with_duration": 0,
        "slides_with_cues": 0,
        "slides_with_tts_words": 0,
        "has_timeline": "timeline" in manifest and bool(manifest["timeline"]),
        "has_presentation_context": "presentation_context" in manifest,
        "missing_fields": []
    }
    
    for slide in manifest.get("slides", []):
        if slide.get("elements"):
            analysis["slides_with_elements"] += 1
        if slide.get("semantic_map"):
            analysis["slides_with_semantic_map"] += 1
        if slide.get("talk_track"):
            analysis["slides_with_talk_track"] += 1
        if slide.get("speaker_notes"):
            analysis["slides_with_speaker_notes"] += 1
        if slide.get("audio"):
            analysis["slides_with_audio"] += 1
        if slide.get("duration"):
            analysis["slides_with_duration"] += 1
        if slide.get("cues"):
            analysis["slides_with_cues"] += 1
        if slide.get("tts_words"):
            analysis["slides_with_tts_words"] += 1
    
    # Check for missing fields
    if analysis["slides_with_elements"] < analysis["total_slides"]:
        analysis["missing_fields"].append("elements")
    if analysis["slides_with_semantic_map"] < analysis["total_slides"]:
        analysis["missing_fields"].append("semantic_map")
    if analysis["slides_with_talk_track"] < analysis["total_slides"]:
        analysis["missing_fields"].append("talk_track")
    if analysis["slides_with_speaker_notes"] < analysis["total_slides"]:
        analysis["missing_fields"].append("speaker_notes")
    if analysis["slides_with_audio"] < analysis["total_slides"]:
        analysis["missing_fields"].append("audio")
    if analysis["slides_with_duration"] < analysis["total_slides"]:
        analysis["missing_fields"].append("duration")
    if analysis["slides_with_cues"] < analysis["total_slides"]:
        analysis["missing_fields"].append("cues")
    if not analysis["has_timeline"]:
        analysis["missing_fields"].append("timeline")
    if not analysis["has_presentation_context"]:
        analysis["missing_fields"].append("presentation_context")
    
    return analysis


def print_manifest_analysis(analysis: Dict[str, Any]):
    """Print manifest analysis results"""
    print_header("MANIFEST ANALYSIS")
    
    total = analysis["total_slides"]
    print_info(f"Total Slides: {total}")
    print()
    
    # Check each field
    fields = [
        ("Elements (OCR)", analysis["slides_with_elements"]),
        ("Semantic Map", analysis["slides_with_semantic_map"]),
        ("Talk Track", analysis["slides_with_talk_track"]),
        ("Speaker Notes", analysis["slides_with_speaker_notes"]),
        ("Audio Files", analysis["slides_with_audio"]),
        ("Duration", analysis["slides_with_duration"]),
        ("Visual Cues", analysis["slides_with_cues"]),
        ("TTS Words", analysis["slides_with_tts_words"]),
    ]
    
    for field_name, count in fields:
        percentage = (count / total * 100) if total > 0 else 0
        if count == total:
            print_success(f"{field_name}: {count}/{total} ({percentage:.0f}%)")
        elif count > 0:
            print_warning(f"{field_name}: {count}/{total} ({percentage:.0f}%)")
        else:
            print_error(f"{field_name}: {count}/{total} ({percentage:.0f}%)")
    
    print()
    if analysis["has_timeline"]:
        print_success("Timeline: Present")
    else:
        print_error("Timeline: Missing")
    
    if analysis["has_presentation_context"]:
        print_success("Presentation Context: Present")
    else:
        print_error("Presentation Context: Missing")
    
    print()
    if not analysis["missing_fields"]:
        print_success("✓ All fields are complete!")
    else:
        print_warning(f"Missing or incomplete fields: {', '.join(analysis['missing_fields'])}")


def print_pipeline_stage_details(manifest: Dict[str, Any], stage_name: str):
    """Print details for specific pipeline stage"""
    print(f"\n{BOLD}Stage: {stage_name}{RESET}")
    
    metadata = manifest.get("metadata", {})
    current_stage = metadata.get("stage", "unknown")
    
    if stage_name.lower() in current_stage.lower():
        print_success(f"Current stage: {current_stage}")
    else:
        print_info(f"Current stage: {current_stage}")
    
    # Print relevant data based on stage
    slides = manifest.get("slides", [])
    if slides:
        sample_slide = slides[0]
        
        if "ingest" in stage_name.lower() or "ocr" in stage_name.lower():
            if sample_slide.get("elements"):
                print_success(f"  ✓ Elements extracted: {len(sample_slide['elements'])} elements in slide 1")
            else:
                print_warning("  ⚠ No elements extracted yet")
        
        if "plan" in stage_name.lower() or "semantic" in stage_name.lower():
            if sample_slide.get("semantic_map"):
                print_success("  ✓ Semantic map created")
            if sample_slide.get("talk_track"):
                print_success(f"  ✓ Talk track generated: {len(sample_slide['talk_track'])} segments")
            if sample_slide.get("speaker_notes"):
                preview = sample_slide['speaker_notes'][:100]
                print_success(f"  ✓ Speaker notes: {preview}...")
        
        if "tts" in stage_name.lower():
            if sample_slide.get("audio"):
                print_success(f"  ✓ Audio file: {sample_slide['audio']}")
            if sample_slide.get("duration"):
                print_success(f"  ✓ Duration: {sample_slide['duration']:.2f}s")
        
        if "cue" in stage_name.lower() or "visual" in stage_name.lower():
            if sample_slide.get("cues"):
                print_success(f"  ✓ Visual cues: {len(sample_slide['cues'])} cues")


def monitor_pipeline(token: str, lesson_id: str, max_wait: int = 600):
    """Monitor pipeline execution in detail"""
    print_header("MONITORING PIPELINE EXECUTION")
    
    start_time = time.time()
    last_stage = None
    last_progress = None
    stage_start_time = {}
    
    while True:
        elapsed = time.time() - start_time
        
        if elapsed > max_wait:
            print_error(f"Timeout after {max_wait} seconds")
            break
        
        # Get status from API
        status = get_lesson_status(token, lesson_id)
        if status:
            current_status = status.get("status")
            current_stage = status.get("stage", "unknown")
            current_progress = status.get("progress", 0)
            message = status.get("message", "")
            
            # Track stage changes
            if current_stage != last_stage:
                if last_stage and last_stage in stage_start_time:
                    stage_duration = time.time() - stage_start_time[last_stage]
                    print_info(f"Stage '{last_stage}' completed in {stage_duration:.1f}s")
                
                print(f"\n{BOLD}[{elapsed:.1f}s] Stage: {current_stage}{RESET}")
                stage_start_time[current_stage] = time.time()
                last_stage = current_stage
            
            # Track progress changes
            if current_progress != last_progress:
                print_info(f"Progress: {current_progress}% - {message}")
                last_progress = current_progress
            
            # Check manifest
            manifest = get_manifest(lesson_id)
            if manifest:
                print_pipeline_stage_details(manifest, current_stage)
            
            # Check if completed or failed
            if current_status == "completed":
                total_time = time.time() - start_time
                print_success(f"\n✓ Pipeline completed in {total_time:.1f}s")
                break
            elif current_status == "failed":
                print_error(f"\n✗ Pipeline failed: {message}")
                break
        
        time.sleep(2)  # Poll every 2 seconds
    
    return manifest


def main():
    """Main test function"""
    print_header("PIPELINE DETAILED TEST")
    
    # Step 1: Check file
    print_step(1, "Verify Test File")
    if not Path(TEST_FILE).exists():
        print_error(f"File not found: {TEST_FILE}")
        sys.exit(1)
    print_success(f"File found: {TEST_FILE}")
    print_info(f"Size: {Path(TEST_FILE).stat().st_size / (1024*1024):.2f} MB")
    
    # Step 2: Register/Login
    print_step(2, "Authentication")
    register_user(USERNAME, PASSWORD)
    token = login_user(USERNAME, PASSWORD)
    if not token:
        print_error("Authentication failed")
        sys.exit(1)
    print_success("Logged in successfully")
    
    # Step 3: Upload file
    print_step(3, "Upload File")
    lesson_id = upload_file(token, TEST_FILE)
    if not lesson_id:
        print_error("Upload failed")
        sys.exit(1)
    
    # Step 4: Monitor pipeline
    print_step(4, "Monitor Pipeline Execution")
    manifest = monitor_pipeline(token, lesson_id)
    
    # Step 5: Analyze results
    print_step(5, "Analyze Results")
    if manifest:
        analysis = analyze_manifest(manifest)
        print_manifest_analysis(analysis)
        
        # Save detailed manifest for inspection
        output_file = f"manifest_{lesson_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print_success(f"\nManifest saved to: {output_file}")
    else:
        print_error("No manifest available")
    
    print_header("TEST COMPLETED")


if __name__ == "__main__":
    main()

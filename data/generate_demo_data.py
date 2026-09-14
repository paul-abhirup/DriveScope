import os
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def create_demo_scenario(base_path: Path, scenario_id: str, title: str, category: str, hazards: list, expected: str, num_frames: int = 30):
    scenario_dir = base_path / scenario_id
    frames_dir = scenario_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "scenario_id": scenario_id,
        "source": "drivescope_demo_generator",
        "conditions": {
            "weather": "clear" if "001" in scenario_id else "rain",
            "time_of_day": "day" if "001" in scenario_id else "dusk"
        },
        "ego": {"initial_speed_mps": 9.5},
        "hazards": hazards,
        "expected_response": expected,
        "fps": 20,
        "description": f"Demo benchmark scenario: {title} ({category}).",
        "tags": [category, "urban", "benchmark", "demo"],
        "license": "MIT"
    }

    with open(scenario_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    readme_content = f"""# Scenario: {title}

- **ID:** `{scenario_id}`
- **Category:** `{category}`
- **Hazards:** `{hazards}`
- **Expected Action:** `{expected}`
- **Frames:** {num_frames} @ 20 FPS

Designed for validating VLA perception, reasoning alignment, and braking reactions.
"""
    with open(scenario_dir / "README.md", "w") as f:
        f.write(readme_content)

    gt_data = {}

    for idx in range(num_frames):
        # Create a synthetic frame image
        img = Image.new("RGB", (640, 480), color=(30, 35, 45))
        draw = ImageDraw.Draw(img)

        # Draw road perspective
        draw.polygon([(0, 480), (260, 200), (380, 200), (640, 480)], fill=(50, 55, 65))
        # Draw lane marker
        draw.line([(320, 200), (320, 480)], fill=(220, 220, 100), width=3)

        # Draw hazard if in active window
        hazard_active = 10 <= idx <= 22 and len(hazards) > 0
        if hazard_active:
            # Draw hazard indicator
            draw.rectangle([(280, 220), (340, 320)], fill=(200, 60, 60), outline=(255, 255, 255))
            draw.text((290, 260), hazards[0].upper()[:3], fill=(255, 255, 255))
            
            # Ground truth requires braking
            gt_brake = 0.75
            gt_throttle = 0.0
            gt_steer = 0.0
            ttc = max(0.5, round((23 - idx) * 0.2, 2))
            active_hazards = hazards
        else:
            gt_brake = 0.0
            gt_throttle = 0.4
            gt_steer = 0.02 if idx % 4 == 0 else -0.01
            ttc = None
            active_hazards = []

        # Overlay text info
        draw.text((20, 20), f"DriveScope Synthetic Stream: {scenario_id}", fill=(200, 200, 200))
        draw.text((20, 40), f"Frame: {idx:04d} | Speed: 9.5 m/s", fill=(180, 180, 180))

        frame_filename = f"frame_{idx:04d}.jpg"
        img.save(frames_dir / frame_filename, "JPEG", quality=85)

        gt_data[str(idx)] = {
            "action": {
                "steering": round(gt_steer, 3),
                "brake": round(gt_brake, 2),
                "throttle": round(gt_throttle, 2)
            },
            "hazards": active_hazards,
            "ttc_seconds": ttc
        }

    with open(scenario_dir / "ground_truth.json", "w") as f:
        json.dump(gt_data, f, indent=2)


if __name__ == "__main__":
    base = Path("./data/sample/scenarios")
    create_demo_scenario(
        base,
        scenario_id="pedestrian_crossing_001",
        title="Night Pedestrian Crossing",
        category="crossing",
        hazards=["pedestrian"],
        expected="brake",
        num_frames=30
    )
    create_demo_scenario(
        base,
        scenario_id="intersection_unprotected_left_002",
        title="Unprotected Left Turn Conflict",
        category="intersection",
        hazards=["oncoming_vehicle"],
        expected="yield_and_turn",
        num_frames=30
    )
    create_demo_scenario(
        base,
        scenario_id="occluded_cyclist_003",
        title="Occluded Cyclist Emerging from Van",
        category="occlusion",
        hazards=["cyclist"],
        expected="brake_and_swerve",
        num_frames=30
    )

    # Write demo manifest
    manifest_dir = Path("./data/manifests")
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_data = {
        "manifest_version": "1.0.0",
        "description": "DriveScope Curated Baseline Scenario Suite",
        "scenarios": [
            "pedestrian_crossing_001",
            "intersection_unprotected_left_002",
            "occluded_cyclist_003"
        ]
    }
    with open(manifest_dir / "demo_scenarios_manifest.json", "w") as f:
        json.dump(manifest_data, f, indent=2)

    print("Demo scenarios generated successfully!")

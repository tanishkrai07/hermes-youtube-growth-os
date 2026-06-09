#!/usr/bin/env python3
"""Fetch view counts for key competitor videos using yt-dlp."""
import subprocess
import json
import time
import os

OUTPUT_DIR = "/home/ec2-user/workspaces/hermes-youtube-growth-os/outputs"

# Key video IDs to get view counts for (new/latest videos from competitors)
KEY_VIDEOS = [
    # Claire Whitmore - latest videos
    ("UrCnGoHBj5E", "Claire Whitmore", "Your Amlodipine Dose Is Getting Stronger Every Year"),
    ("WuEQDCkZ0LA", "Claire Whitmore", "Your Anxiety And High Blood Pressure Share One Missing Mineral"),
    ("CRMH6PL2W6k", "Claire Whitmore", "Taking Amlodipine, Losartan, or Lisinopril for Blood Pressure"),
    ("_43ErjAKJWU", "Claire Whitmore", "Lisinopril Is Slowly Poisoning Your Kidneys"),
    ("kq-L3ZWpE8c", "Claire Whitmore", "The Only Magnesium Type That Actually Lowers Blood Pressure"),
    ("msrvRuWgr8c", "Claire Whitmore", "Your Vitamin D Deficiency Is Silently Destroying Your Leg Muscles"),
    ("-mLykdTuZbA", "Claire Whitmore", "This Forgotten Morning Habit Finally Destroys Hypertension"),
    
    # Dr. Michael Kent - latest videos
    ("F3phhk_savo", "Dr. Michael Kent", "What Amlodipine Does to Your Body After 5 Years"),
    ("efE27656DnI", "Dr. Michael Kent", "Why Healthy People Still Have High Blood Pressure"),
    ("gsCFaEIkDdc", "Dr. Michael Kent", "How to drink water to avoid getting up at night"),
    ("lvm89a32lHc", "Dr. Michael Kent", "How to Eat Eggs Correctly If You Are Diabetic"),
    ("Y_3k00KY-44", "Dr. Michael Kent", "What's the Best Blood Sugar for Older Adults?"),
    
    # Dr. Waterling - latest
    ("7fBA7AtzEPU", "Dr. Waterling", "BE-FAST Test: Detect a Stroke at Home in 30 Seconds"),
    ("TH95KRLlXXo", "Dr. Waterling", "7 Days Before a Stroke Your Body Sends These 5 Warnings"),
    
    # Dr. Franklin - latest
    ("IkmdX23vNdg", "Dr. Franklin", "Neurologist Warns If Your NAILS Look Like THIS After 60"),
    
    # Dr. James Hargrove - latest
    ("rEC-3yyL5QQ", "Dr. James Hargrove", "4 Vitamins Seniors Take Daily Are SILENTLY Causing Stroke After 65"),
    ("mer4cQJp-s4", "Dr. James Hargrove", "If Your Legs Tingle Burn or Go Numb After 60"),
    ("z8bU01_ynbo", "Dr. James Hargrove", "Cardiologist WARNS: NEVER Take B12 With THESE 2 Medications After 60!"),
    
    # Doctor Christopher Carter - latest
    ("KZNLGMwshXU", "Doctor Christopher Carter", "Over 60? Cardiologist warns One of These 5 Pills Could Trigger a Heart Attack"),
    ("Qvo63LmUmH0", "Doctor Christopher Carter", "6 Medicines That Skyrocket Heart Attack Risk After 60!"),
    
    # Dr. James Cross - latest
    ("3WfRQrZXVKI", "Dr. James Cross", "THIS 1 Simple Movement Drains Swollen Legs & Ankles Fast!"),
    ("P5QQzv7vct8", "Dr. James Cross", "Swollen Ankles After 60? It's Not Your Heart — It's Your Lymph"),
    
    # Doctor Becker - latest microplastics
    ("Tjkb8oKHCjE", "Doctor Becker", "Plastic Found INSIDE Your Body's Cells"),
    
    # New competitors
    ("P1I8rnTi-U8", "Dr. Michael Carter (NEW)", "5 Common Medications That May DAMAGE Your Heart Seniors Must Know"),
    ("aVnGaA3hkrk", "Claire Whitmore", "Blood Pressure Spikes at Home? Do These 2 Things Immediately - search result"),
]

def get_video_info(video_id):
    """Get video info including view count."""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", url],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout)
        return {
            "view_count": data.get("view_count", 0),
            "like_count": data.get("like_count", 0),
            "upload_date": data.get("upload_date", ""),
            "duration": data.get("duration", 0),
            "channel": data.get("channel", ""),
            "channel_id": data.get("channel_id", ""),
            "title": data.get("title", ""),
        }
    except Exception as e:
        return {"error": str(e)}

results = []
for video_id, expected_channel, title_prefix in KEY_VIDEOS:
    info = get_video_info(video_id)
    if "error" not in info:
        results.append({
            "video_id": video_id,
            "expected_channel": expected_channel,
            "actual_channel": info.get("channel", ""),
            "title": info.get("title", title_prefix)[:100],
            "views": info.get("view_count", 0),
            "likes": info.get("like_count", 0),
            "upload_date": info.get("upload_date", ""),
            "duration_sec": info.get("duration", 0),
            "url": f"https://www.youtube.com/watch?v={video_id}"
        })
        print(f"[{info.get('view_count', 0):>10,} views] {info.get('title', title_prefix)[:70]}")
        print(f"           Channel: {info.get('channel', '?')[:40]} | Date: {info.get('upload_date', '?')} | Duration: {info.get('duration', 0)}s")
        print()
    else:
        print(f"[ERROR] {video_id}: {info['error'][:80]}")
        print()
    time.sleep(0.5)

with open(os.path.join(OUTPUT_DIR, "video_counts.json"), "w") as f:
    json.dump(results, f, indent=2)

print(f"\nTotal videos with view counts: {len(results)}")
print("Saved to outputs/video_counts.json")

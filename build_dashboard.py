#!/usr/bin/env python3
"""Build the 55Places content dashboard HTML from markdown source files."""

import os
import re
import json
import html

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read_md(path):
    """Read a markdown file and return its content."""
    full = os.path.join(BASE, path)
    if os.path.exists(full):
        with open(full, 'r') as f:
            return f.read()
    return ""

def extract_posts_from_md(content, platform):
    """Extract individual post variations from a markdown file."""
    posts = []
    # Split by h2 or h3 variation headers
    sections = re.split(r'(?:^|\n)##\s+(?!#)', content)
    if len(sections) <= 1:
        sections = re.split(r'(?:^|\n)###\s+', content)

    for section in sections[1:]:  # Skip the preamble
        lines = section.strip().split('\n')
        title = lines[0].strip().rstrip('#').strip()
        body = '\n'.join(lines[1:]).strip()

        # Extract persona
        persona_match = re.search(r'\*\*Target Persona:\*\*\s*(.+)', body)
        persona = persona_match.group(1).strip() if persona_match else ""

        # Extract the actual post text (between --- markers)
        text_match = re.search(r'---\s*\n(.*?)\n---', body, re.DOTALL)
        post_text = text_match.group(1).strip() if text_match else ""

        # If no text between --- markers, try to get substantial text
        if not post_text or len(post_text) < 50:
            # Look for text blocks that aren't metadata
            text_lines = []
            in_text = False
            for line in lines[1:]:
                stripped = line.strip()
                if stripped == '---':
                    if in_text:
                        break
                    in_text = True
                    continue
                if in_text and stripped and not stripped.startswith('**') :
                    text_lines.append(stripped)
                elif in_text and stripped.startswith('**') and not any(k in stripped for k in ['Target', 'Hashtag', 'Content format', 'Best posting', 'Suggested visual', 'Engagement', 'Risk note', 'Campaign', 'Placement', 'Targeting', 'Creative', 'A/B']):
                    text_lines.append(stripped)
            if text_lines:
                post_text = '\n'.join(text_lines)

        # Extract hashtags
        hash_match = re.search(r'\*\*Hashtags?:\*\*\s*\n?(.+?)(?:\n\*\*|\n\n|$)', body, re.DOTALL)
        hashtags = hash_match.group(1).strip() if hash_match else ""

        # For Reddit, extract the title
        reddit_title = ""
        rt_match = re.search(r'\*\*Title:\*\*\s*(.+)', body)
        if rt_match:
            reddit_title = rt_match.group(1).strip()

        if post_text and len(post_text) > 30:
            posts.append({
                'title': reddit_title if reddit_title else title,
                'persona': persona,
                'text': post_text,
                'hashtags': hashtags,
                'platform': platform,
            })
    return posts

def extract_ads_from_md(content):
    """Extract ad variations from an ad copy markdown file."""
    ads = []
    sections = re.split(r'(?:^|\n)##\s+(?!#)', content)
    if len(sections) <= 1:
        sections = re.split(r'(?:^|\n)###\s+', content)
    for section in sections[1:]:
        lines = section.strip().split('\n')
        title = lines[0].strip().rstrip('#').strip()
        body = '\n'.join(lines[1:]).strip()

        persona_match = re.search(r'\*\*Target Persona:\*\*\s*(.+)', body)
        persona = persona_match.group(1).strip() if persona_match else ""

        primary_match = re.search(r'\*\*Primary Text:\*\*\s*\n(.*?)(?:\n\*\*Headline|\n---)', body, re.DOTALL)
        primary_text = primary_match.group(1).strip() if primary_match else ""

        headline_match = re.search(r'\*\*Headline:\*\*\s*(.+)', body)
        headline = headline_match.group(1).strip() if headline_match else ""

        desc_match = re.search(r'\*\*Description:\*\*\s*(.+)', body)
        description = desc_match.group(1).strip() if desc_match else ""

        cta_match = re.search(r'\*\*CTA Button:\*\*\s*(.+)', body)
        cta = cta_match.group(1).strip() if cta_match else ""

        objective_match = re.search(r'\*\*Campaign Objective:\*\*\s*(.+)', body)
        objective = objective_match.group(1).strip() if objective_match else ""

        if primary_text or headline:
            ads.append({
                'title': title,
                'persona': persona,
                'primary_text': primary_text,
                'headline': headline,
                'description': description,
                'cta': cta,
                'objective': objective,
                'platform': 'facebook',
            })
    return ads

def extract_video_production(content):
    """Extract video production info."""
    format_match = re.search(r'\*\*Recommended Format:\*\*\s*(.+)', content)
    tool_match = re.search(r'\*\*Recommended Tool:\*\*\s*(.+)', content)
    runtime_match = re.search(r'\*\*(?:Total )?Runtime(?: Target)?:\*\*\s*(.+)', content)
    music_match = re.search(r'\*\*Music Direction:\*\*\s*(.+)', content)
    persona_match = re.search(r'\*\*Target Persona:\*\*\s*(.+)', content)

    # Extract production table rows
    table_rows = re.findall(r'\|\s*(\d[\d:.-]*\s*[–-]?\s*\d*[:.]?\d*s?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|', content)

    return {
        'format': format_match.group(1).strip() if format_match else "",
        'tool': tool_match.group(1).strip() if tool_match else "",
        'runtime': runtime_match.group(1).strip() if runtime_match else "",
        'music': music_match.group(1).strip() if music_match else "",
        'persona': persona_match.group(1).strip() if persona_match else "",
        'table_rows': table_rows,
        'full_content': content,
    }

# ============================================================
# GATHER ALL CONTENT
# ============================================================

all_content = {
    'linkedin': [],
    'instagram': [],
    'reddit': [],
    'facebook': [],  # ads
    'video': [],
}

# Social copy
social_dir = "social-copy"
for fname in sorted(os.listdir(os.path.join(BASE, social_dir))):
    if not fname.endswith('.md'):
        continue
    content = read_md(os.path.join(social_dir, fname))
    topic = fname.replace('.md', '')

    if fname.startswith('linkedin-'):
        posts = extract_posts_from_md(content, 'linkedin')
        # Derive topic name from filename
        topic_name = fname.replace('linkedin-', '').replace('.md', '').replace('-', ' ').title()
        for p in posts:
            p['topic'] = topic_name
            p['source_file'] = f"social-copy/{fname}"
        all_content['linkedin'].extend(posts)

    elif fname.startswith('instagram-'):
        posts = extract_posts_from_md(content, 'instagram')
        topic_name = fname.replace('instagram-', '').replace('.md', '').replace('-', ' ').title()
        for p in posts:
            p['topic'] = topic_name
            p['source_file'] = f"social-copy/{fname}"
        all_content['instagram'].extend(posts)

    elif fname.startswith('reddit-'):
        posts = extract_posts_from_md(content, 'reddit')
        topic_name = fname.replace('reddit-', '').replace('.md', '').replace('-', ' ').title()
        for p in posts:
            p['topic'] = topic_name
            p['source_file'] = f"social-copy/{fname}"
        all_content['reddit'].extend(posts)

# Ad copy
ad_dir = "ad-copy"
for fname in sorted(os.listdir(os.path.join(BASE, ad_dir))):
    if not fname.endswith('.md'):
        continue
    content = read_md(os.path.join(ad_dir, fname))
    topic_name = fname.replace('ads-', '').replace('.md', '').replace('-', ' ').title()
    ads = extract_ads_from_md(content)
    for a in ads:
        a['topic'] = topic_name
        a['source_file'] = f"ad-copy/{fname}"
    all_content['facebook'].extend(ads)

# Video production
video_dir = "video-production"
for fname in sorted(os.listdir(os.path.join(BASE, video_dir))):
    if not fname.endswith('.md'):
        continue
    content = read_md(os.path.join(video_dir, fname))
    topic_name = fname.replace('video-', '').replace('-PRODUCTION.md', '').replace('-', ' ').title()
    info = extract_video_production(content)
    info['topic'] = topic_name
    info['source_file'] = f"video-production/{fname}"
    info['platform'] = 'video'
    all_content['video'].append(info)

# ============================================================
# CALENDAR DATA (from SUMMARY.md)
# ============================================================

calendar_data = [
    # Week 1
    {"day": "Mon", "week": 1, "platform": "instagram", "label": "Pros & Cons Carousel", "persona": "Linda"},
    {"day": "Mon", "week": 1, "platform": "facebook", "label": "Pros & Cons Ad", "persona": "Linda"},
    {"day": "Tue", "week": 1, "platform": "linkedin", "label": "Pros & Cons Thought Leadership", "persona": "Linda"},
    {"day": "Wed", "week": 1, "platform": "instagram", "label": "Day-to-Day Life Reel", "persona": "Diane"},
    {"day": "Wed", "week": 1, "platform": "reddit", "label": "Day-to-Day Experience Share", "persona": "Diane"},
    {"day": "Thu", "week": 1, "platform": "linkedin", "label": "Cost Breakdown Data Post", "persona": "Robert & Carol"},
    {"day": "Thu", "week": 1, "platform": "facebook", "label": "Cost Awareness Ad", "persona": "Robert & Carol"},
    {"day": "Fri", "week": 1, "platform": "instagram", "label": "Tour Checklist Carousel", "persona": "Linda"},
    # Week 2
    {"day": "Mon", "week": 2, "platform": "instagram", "label": "Cost Bold/Provocative", "persona": "Robert & Carol"},
    {"day": "Mon", "week": 2, "platform": "reddit", "label": "Cost Spreadsheet Share", "persona": "Robert & Carol"},
    {"day": "Tue", "week": 2, "platform": "linkedin", "label": "Tour Checklist Story", "persona": "Linda"},
    {"day": "Wed", "week": 2, "platform": "instagram", "label": "What It Really Means Carousel", "persona": "Diane"},
    {"day": "Wed", "week": 2, "platform": "facebook", "label": "Day-to-Day Conversion Ad", "persona": "Diane"},
    {"day": "Thu", "week": 2, "platform": "linkedin", "label": "Day-to-Day Thought Leadership", "persona": "Diane"},
    {"day": "Fri", "week": 2, "platform": "instagram", "label": "Pros & Cons Reel", "persona": "Linda"},
    {"day": "Fri", "week": 2, "platform": "reddit", "label": "Tour Checklist Post", "persona": "Linda"},
    # Week 3
    {"day": "Mon", "week": 3, "platform": "instagram", "label": "Pros & Cons Slideshow Video", "persona": "Linda"},
    {"day": "Mon", "week": 3, "platform": "facebook", "label": "Tour Checklist Conversion Ad", "persona": "Linda"},
    {"day": "Tue", "week": 3, "platform": "linkedin", "label": "What It Really Means Post", "persona": "Diane"},
    {"day": "Wed", "week": 3, "platform": "instagram", "label": "Day-to-Day UGC Video", "persona": "Diane"},
    {"day": "Wed", "week": 3, "platform": "reddit", "label": "What It Really Means Myth-Bust", "persona": "Diane"},
    {"day": "Thu", "week": 3, "platform": "linkedin", "label": "Cost Story-Driven", "persona": "Robert & Carol"},
    {"day": "Thu", "week": 3, "platform": "facebook", "label": "What It Really Means Ad", "persona": "Diane"},
    {"day": "Fri", "week": 3, "platform": "instagram", "label": "Tour Checklist Slideshow", "persona": "Linda"},
    # Week 4
    {"day": "Mon", "week": 4, "platform": "instagram", "label": "What It Really Means Bold", "persona": "Diane"},
    {"day": "Mon", "week": 4, "platform": "facebook", "label": "Pros & Cons Conversion Ad", "persona": "Linda"},
    {"day": "Tue", "week": 4, "platform": "linkedin", "label": "Pros & Cons Data/Proof", "persona": "Linda"},
    {"day": "Tue", "week": 4, "platform": "reddit", "label": "Pros & Cons Experience Share", "persona": "Linda"},
    {"day": "Wed", "week": 4, "platform": "instagram", "label": "Cost Voiceover Video", "persona": "Robert & Carol"},
    {"day": "Wed", "week": 4, "platform": "facebook", "label": "Cost Conversion Ad", "persona": "Robert & Carol"},
    {"day": "Thu", "week": 4, "platform": "linkedin", "label": "Day-to-Day Data/Proof", "persona": "Diane"},
    {"day": "Fri", "week": 4, "platform": "instagram", "label": "Day-to-Day Carousel", "persona": "Diane"},
    {"day": "Fri", "week": 4, "platform": "facebook", "label": "What It Really Means Conv Ad", "persona": "Diane"},
]

# ============================================================
# FILES INDEX
# ============================================================

files_index = {
    "Personas": [
        {"name": "persona-1-linda.md", "desc": "Linda — The Overwhelmed Researcher (full profile, pain points, verbatims)"},
        {"name": "persona-2-diane.md", "desc": "Diane — The Social Butterfly Starting Over (full profile, pain points, verbatims)"},
        {"name": "persona-3-robert-and-carol.md", "desc": "Robert & Carol — The Cautious Planners (full profile, pain points, verbatims)"},
    ],
    "Social Copy": [
        {"name": "linkedin-pros-cons-linda.md", "desc": "3 LinkedIn posts — Pros & Cons (Linda)"},
        {"name": "linkedin-cost-robert-carol.md", "desc": "3 LinkedIn posts — Cost Breakdown (Robert & Carol)"},
        {"name": "linkedin-day-in-life-diane.md", "desc": "3 LinkedIn posts — Day-to-Day Life (Diane)"},
        {"name": "linkedin-tour-checklist-linda.md", "desc": "3 LinkedIn posts — Tour Checklist (Linda)"},
        {"name": "linkedin-what-it-really-means-diane.md", "desc": "3 LinkedIn posts — What It Really Means (Diane)"},
        {"name": "instagram-pros-cons-linda.md", "desc": "3 Instagram captions — Pros & Cons (Linda)"},
        {"name": "instagram-cost-robert-carol.md", "desc": "3 Instagram captions — Cost Breakdown (Robert & Carol)"},
        {"name": "instagram-day-in-life-diane.md", "desc": "3 Instagram captions — Day-to-Day Life (Diane)"},
        {"name": "instagram-tour-checklist-linda.md", "desc": "3 Instagram captions — Tour Checklist (Linda)"},
        {"name": "instagram-what-it-really-means-diane.md", "desc": "3 Instagram captions — What It Really Means (Diane)"},
        {"name": "reddit-pros-cons-linda.md", "desc": "2 Reddit angles — Pros & Cons (Linda)"},
        {"name": "reddit-cost-robert-carol.md", "desc": "2 Reddit angles — Cost Breakdown (Robert & Carol)"},
        {"name": "reddit-day-in-life-diane.md", "desc": "2 Reddit angles — Day-to-Day Life (Diane)"},
        {"name": "reddit-tour-checklist-linda.md", "desc": "2 Reddit angles — Tour Checklist (Linda)"},
        {"name": "reddit-what-it-really-means-diane.md", "desc": "2 Reddit angles — What It Really Means (Diane)"},
    ],
    "Ad Copy": [
        {"name": "ads-pros-cons-linda.md", "desc": "2 FB/IG ads — Pros & Cons (1 Awareness + 1 Conversion)"},
        {"name": "ads-cost-robert-carol.md", "desc": "2 FB/IG ads — Cost Breakdown (1 Awareness + 1 Conversion)"},
        {"name": "ads-day-in-life-diane.md", "desc": "2 FB/IG ads — Day-to-Day Life (1 Awareness + 1 Conversion)"},
        {"name": "ads-tour-checklist-linda.md", "desc": "2 FB/IG ads — Tour Checklist (1 Awareness + 1 Conversion)"},
        {"name": "ads-what-it-really-means-diane.md", "desc": "2 FB/IG ads — What It Really Means (1 Awareness + 1 Conversion)"},
    ],
    "Video Scripts": [
        {"name": "video-pros-cons-linda-PRODUCTION.md", "desc": "Video production sheet — Pros & Cons (Slideshow, CapCut)"},
        {"name": "video-cost-robert-carol-PRODUCTION.md", "desc": "Video production sheet — Cost (Voiceover, HeyGen)"},
        {"name": "video-day-in-life-diane-PRODUCTION.md", "desc": "Video production sheet — Day-to-Day Life (Talking-Head)"},
        {"name": "video-tour-checklist-linda-PRODUCTION.md", "desc": "Video production sheet — Tour Checklist (Slideshow, CapCut)"},
        {"name": "video-what-it-means-diane-PRODUCTION.md", "desc": "Video production sheet — What It Really Means (Talking-Head)"},
    ],
    "Visual Briefs": [
        {"name": "visuals-pros-cons-linda.md", "desc": "3 AI image prompts + 2 text overlay concepts — Pros & Cons"},
        {"name": "visuals-cost-robert-carol.md", "desc": "3 AI image prompts + 2 text overlay concepts — Cost"},
        {"name": "visuals-day-in-life-diane.md", "desc": "3 AI image prompts + 2 text overlay concepts — Day-to-Day Life"},
        {"name": "visuals-tour-checklist-linda.md", "desc": "3 AI image prompts + 2 text overlay concepts — Tour Checklist"},
        {"name": "visuals-what-it-means-diane.md", "desc": "3 AI image prompts + 2 text overlay concepts — What It Really Means"},
    ],
}

# Serialize for JS
content_json = json.dumps(all_content, ensure_ascii=False)
calendar_json = json.dumps(calendar_data, ensure_ascii=False)
files_json = json.dumps(files_index, ensure_ascii=False)

# Count stats
stats = {
    'linkedin': len(all_content['linkedin']),
    'instagram': len(all_content['instagram']),
    'reddit': len(all_content['reddit']),
    'facebook': len(all_content['facebook']),
    'video': len(all_content['video']),
    'total': sum(len(v) for v in all_content.values()),
}

print(f"Content extracted:")
print(f"  LinkedIn: {stats['linkedin']} posts")
print(f"  Instagram: {stats['instagram']} posts")
print(f"  Reddit: {stats['reddit']} posts")
print(f"  Facebook Ads: {stats['facebook']} ads")
print(f"  Videos: {stats['video']} scripts")
print(f"  Total: {stats['total']} pieces")

# Write the JSON data files
with open(os.path.join(BASE, 'dashboard', 'content-data.json'), 'w') as f:
    json.dump({
        'content': all_content,
        'calendar': calendar_data,
        'files': files_index,
        'stats': stats,
    }, f, ensure_ascii=False, indent=2)

print(f"\nData written to dashboard/content-data.json")

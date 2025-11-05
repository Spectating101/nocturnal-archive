#!/usr/bin/env python3
"""Test inference engine on real projects"""
from pathlib import Path
from optiplex.inference import ProjectInferenceEngine
import json

# Test on multiple projects
projects = [
    "/home/phyrexian/Downloads/llm_automation/project_portfolio/Cite-Agent",
    "/home/phyrexian/Downloads/llm_automation/project_portfolio/Simons-Empirical",
    "/home/phyrexian/Downloads/llm_automation/project_portfolio/Molina-Optiplex",
]

for project_path in projects:
    if not Path(project_path).exists():
        continue
    
    print(f"\n{'='*80}")
    print(f"ANALYZING: {Path(project_path).name}")
    print('='*80)
    
    engine = ProjectInferenceEngine(project_path)
    
    # Full analysis
    analysis = engine.analyze_project()
    
    print(f"\n📋 PROJECT TYPE: {analysis['project_type']}")
    print(f"🎯 PURPOSE: {analysis['purpose'][:200]}...")
    print(f"\n🛠️  TECH STACK:")
    print(f"   Languages: {', '.join(analysis['tech_stack']['languages']) or 'Unknown'}")
    print(f"   Frameworks: {', '.join(analysis['tech_stack']['frameworks']) or 'None detected'}")
    
    print(f"\n📊 CURRENT STATE:")
    state = analysis['current_state']
    print(f"   Maturity: {state['maturity']}")
    print(f"   Completeness: {state['completeness_score']*100:.0f}%")
    print(f"   Has Tests: {'✅' if state['has_tests'] else '❌'}")
    print(f"   Has Docs: {'✅' if state['has_docs'] else '❌'}")
    print(f"   Has Deployment: {'✅' if state['has_deployment'] else '❌'}")
    
    print(f"\n🔍 RECENT WORK:")
    recent = analysis['recent_work']
    if recent['recent_commits']:
        print(f"   Last commits:")
        for commit in recent['recent_commits'][:3]:
            print(f"     - {commit}")
        print(f"   Focus area: {recent['last_focus_area'] or 'Unknown'}")
    
    print(f"\n🎯 NEXT STEPS (Inferred):")
    for i, step in enumerate(analysis['next_steps'][:5], 1):
        print(f"   {i}. {step}")
    
    # Generate work plan
    print(f"\n📝 WORK PLAN:")
    plan = engine.generate_work_plan()
    print(f"   Total estimated hours: {plan['estimated_hours']}")
    print(f"   Priority tasks:")
    for task in plan['priority_tasks']:
        priority_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }.get(task['priority'], '⚪')
        print(f"     {priority_emoji} [{task['priority'].upper()}] {task['description']} ({task['estimated_hours']}h)")

print("\n" + "="*80)
print("INFERENCE ENGINE TEST COMPLETE")
print("="*80)



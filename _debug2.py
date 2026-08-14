import sys, json
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\sailor\.codex\skills\stock-signals\scripts")

# Patch to debug
import analyze_signals as asg
orig_analyze = asg.analyze

def debug_analyze(code, timeframe="1d", output_json=False):
    result = orig_analyze(code, timeframe, output_json)
    print(f"DEBUG: resonance={result.get('resonance')}", file=sys.stderr)
    print(f"DEBUG: trend_phase={result.get('trend_phase')}", file=sys.stderr)
    print(f"DEBUG: trade_plan={result.get('trade_plan')}", file=sys.stderr)
    print(f"DEBUG: sr_keys={list(result.get('support_resistance', {}).keys()) if result.get('support_resistance') else None}", file=sys.stderr)
    return result

asg.analyze = debug_analyze
asg.main()

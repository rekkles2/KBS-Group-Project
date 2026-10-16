"""Independently validate delivered SVG values/geometry; optionally render in Chromium.

Rendering is optional tooling, not a dependency of graph generation. Point
--playwright-module at an installed Node playwright package; no install occurs.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

NS = {'s': 'http://www.w3.org/2000/svg'}


def audit_chart(path, expected):
    root = ET.parse(path).getroot()
    texts = root.findall('s:text', NS)
    bars = [r for r in root.findall('s:rect', NS) if r.get('x') == '260']
    if len(texts) != 2 + 2 * len(expected) or len(bars) != len(expected):
        raise ValueError(f'{path}: unexpected chart structure')
    rows = []
    scale = 540 / max(expected.values(), default=1)
    for i, (category, count) in enumerate(sorted(expected.items())):
        label, value = texts[2 + i * 2:4 + i * 2]
        width = float(bars[i].get('width'))
        assert label.text == category, (path, category, label.text)
        assert int(value.text) == count, (path, category, value.text, count)
        assert abs(width - count * scale) <= .00501, (path, category, width)
        assert abs(float(value.get('x')) - 270 - width) <= .01001
        assert float(value.get('x')) + 50 < float(root.get('width'))
        rows.append({'category': category, 'count': count, 'width': width})
    return {'path': str(path), 'total': sum(expected.values()), 'rows': rows,
            'title': texts[0].text, 'caption': texts[1].text,
            'viewBox': root.get('viewBox'), 'all_count_and_geometry_checks_passed': True}


def audit(graph_path, reports):
    graph = json.loads(Path(graph_path).read_text(encoding='utf-8-sig'))
    injected = [e for e in graph['edges'] if e.get('is_poisoned') is True]
    return [audit_chart(Path(reports) / filename, Counter(key(e) for e in injected))
            for filename, key in [
                ('injected_by_relation.svg', lambda e: e['relation']),
                ('injected_by_type.svg', lambda e: e['injection_provenance']['entity_type'])]]


def render(paths, output, module, chromium=None):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    script = r"""
const {chromium}=require(process.argv[1]);
(async()=>{const browser=await chromium.launch({headless:true,...(process.argv[3]?{executablePath:process.argv[3]}:{})});
const page=await browser.newPage({viewport:{width:1000,height:900},deviceScaleFactor:1});
let results=[];
for(const item of JSON.parse(process.argv[2])){
 await page.goto(item.uri); await page.locator('svg').screenshot({path:item.output});
 let boxes=await page.locator('svg text').evaluateAll(es=>es.map(e=>({text:e.textContent,x:e.getBBox().x,y:e.getBBox().y,width:e.getBBox().width,height:e.getBBox().height})));
 results.push({...item,text_boxes:boxes});}
await browser.close();process.stdout.write(JSON.stringify(results));})().catch(e=>{console.error(e);process.exit(1)});
"""
    items = [{'uri': Path(p).resolve().as_uri(),
              'output': str(output / (Path(p).stem + '.png'))} for p in paths]
    result = subprocess.run(['node', '-e', script, str(module), json.dumps(items), str(chromium or '')],
                            check=False, text=True, encoding='utf-8', capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graph', type=Path, required=True)
    parser.add_argument('--reports', type=Path, required=True)
    parser.add_argument('--json', type=Path, required=True)
    parser.add_argument('--screenshots', type=Path)
    parser.add_argument('--playwright-module', type=Path)
    parser.add_argument('--chromium', type=Path)
    args = parser.parse_args()
    results = {'charts': audit(args.graph, args.reports)}
    if args.screenshots:
        if not args.playwright_module:
            parser.error('--screenshots requires --playwright-module')
        results['renders'] = render([c['path'] for c in results['charts']],
                                    args.screenshots, args.playwright_module, args.chromium)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'charts_checked': len(results['charts']), 'screenshot_count': len(results.get('renders', []))}))


if __name__ == '__main__':
    main()

"""Export a snapshot view for renderers without modifying source observations."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.snapshot_visibility import snapshot_view


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graph',type=Path,required=True)
    parser.add_argument('--snapshot',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    graph=json.loads(args.graph.read_text(encoding='utf-8-sig'))
    view=snapshot_view(graph,args.snapshot)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(view,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'snapshot':args.snapshot,'nodes':len(view['nodes']),'edges':len(view['edges'])}))


if __name__=='__main__':main()

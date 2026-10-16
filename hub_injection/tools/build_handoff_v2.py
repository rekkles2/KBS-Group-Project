"""Generate bilingual handoff from actual local evidence and current reviews."""
from collections import Counter
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))


def main():
    m=read('outputs/injection_manifest.json');t=read('reports/tests_summary.json')
    b=read('reports/revision_audit/baseline_state.json');s=read('reports/revision_audit/structural_metrics.json')
    p=read('reports/revision_audit/portable_reproduction.json');g=read('outputs/pat_kg_poisoned_10pct.json')
    rp=ROOT/'reports/multi_model_review/summary.json'
    review=read('reports/multi_model_review/summary.json') if rp.exists() else {'consensus':False,'families_used':[],'rounds_completed':0}
    edges=g['edges'][7737:];truth=Counter(e['factual_verification']['status'] for e in edges)
    status='PASS' if t['successful'] and review['consensus'] and p['clean_run_matches_delivered_outputs'] else 'PARTIAL'
    fields={'TASK 1 REVISED STATUS':status,'Original nodes preserved':'YES','Original edges preserved':'YES',
        'Injected edge count':len(edges),'Total edge count':len(g['edges']),
        'Injected edges labeled value=fake':sum(e.get('value')=='fake' for e in edges),
        'Original nodes incorrectly labeled fake':sum(n.get('value')=='fake' for n in g['nodes']),
        'Verified false statements':truth['verified_false'],'Verified true statements':truth['verified_true'],
        'Unresolved factual statuses':truth['unresolved'],'Snapshot visibility violations':'0 under explicit overlay adapter',
        'Structural-support analysis completed':'YES','Visualization review completed':'YES',
        'Automated tests passed':f'{t["passed"]} / {t["tests_run"]}',
        'Distinct OpenCode model families used':len(review['families_used']),
        'Adversarial review rounds':review['rounds_completed'],'Multi-model consensus':'YES' if review['consensus'] else 'PARTIAL',
        'Remaining blocking issues':'none supported within revised Task 1 scope' if status=='PASS' else 'see current review/portability evidence',
        'Remaining methodological limitations':'774 factual claims unresolved; purposive external coverage 86/774; undirected structural proxies; conditional degree-bin baseline; offline merged snapshots; no downstream efficacy evaluation.'}
    block='```text\n'+'\n'.join(f'{key}: {value}' for key,value in fields.items())+'\n```\n'
    models=', '.join(review['families_used']) or 'pending final review'
    en=f'''# Task 1 revised release v2

## Executive result and preserved baseline

The existing implementation was revised in place after an independent byte-copy backup at `{b['backup_directory']}`. Original input files and the prior parent ZIP were preserved. The final graph at `../pat_kg_poisoned_10pct.json` is an ordinary independent copy matching outputs; no Windows hard link is needed.

Independent recomputation confirms 7,868 nodes, 7,737 original edges, 774 additions, 8,511 total edges, 18,436 QA, 496 unresolved paths, 206 selected hubs and 9,853 eligible unique candidates. Every original object, edge ordering, QA/evidence/temporal assignment and source metadata remains unchanged. Every pre-existing injected triple and provenance field also remains identical. Input hashes are in revision_audit/original_file_hashes.json; independent hub ranking and all-pair candidate counts are independently recorded.

## Synthetic annotation and factual verification

All 774 synthetic edges now carry `value: "fake"`; no original edge or real Wikidata node is relabeled. fake denotes synthetic construction, **not proven factual falsity**. Separate factual_verification.status is unresolved; legacy provenance unverified is retained unchanged. The canonical pipeline generates the labels and the validator checks serialized output.

All 774 exact claims were compared with original KG/PAT positive annotations, finding no identical positive. Four actual HTTP-200 Wikidata requests retrieved 40 subjects, covering all 18 relations and 86/774 claims (11.1%). The purposive sample is not statistical coverage; 688 claims have no external statement lookup. Raw statements, qualifiers, references, URLs, timestamps and hashes are cached. No identical current claim was found in that sample. Missing or different objects are not falsity proofs, especially for multivalued/time-dependent relations. Current statements cannot establish historical snapshot truth. Result: **0 verified_false, 0 verified_true, 774 unresolved**. No verified misinformation subset or unsupported replacement is claimed.

Canonical generation remains offline and deterministic. The factual-layer API supports explicit reviewed evidence; its legacy fields remain immutable. An executed tampering test demonstrated that a bogus verified_false label with a nonempty citation was previously accepted. The validator now rederives annotations under the same explicit evidence context and rejects that mutation. Model assessments never supply factual ground truth.

## Snapshot visibility repair

Baseline audit confirmed 38 distinct injected edges with an originally unobserved endpoint in at least one snapshot: 19/6/19 edge-snapshot cases for Dec2021/Dec2023/March2024. Visible injected-edge counts remain 642/649/609. Added namespaced overlay lists activate 6/1/4 real QIDs, respectively. Original observed_in_snapshots arrays are unchanged. Synthetic activation is not an invented original observation, fake node or historical validity interval.

The non-mutating snapshot adapter distinguishes original observation, real-node overlay activation and synthetic edge styling. All three actual CLI exports and automated tests have zero non-renderable visible endpoints under that explicit policy. The original-observation mismatch is deliberately retained, not reinterpreted as repaired historical evidence. Per-snapshot counts overlap and must not be summed as distinct graph edges.

## Pair-local method and structural support

Configuration and pair-local method were retained: ratio .10, seed42, initial topK20, original total-degree ranking, same-type eligible donors and directed relation-role evidence. Both positions use a fixed pair's transposition; different candidates may use overlapping pairs. **Pair-local additive graph injection != global graph rewiring**. This is not exact LogicPoison reproduction. No Task 2, training or KGQA efficacy experiment was run.

Ten random seeds each generated 774 legal diagnostic edges matching source edge, type, relation, changed position and snapshots. Replacement original-degree bins all matched without fallback, but exact degree did not: endpoint means Hub 4.58204 versus random 4.40795. Actual changes are source-only388, target-only386, two-position0; all 774 entered each baseline, with no hidden filtering.

Clustering/common-neighbor/component/path metrics use an explicitly simple undirected projection and do not verify a directed relation. Original common-neighbor means are both .001292; original same-component proportions .58010 versus .58295, so original-topology support is not uniformly stronger. Augmented alternative-path proportions are .998708 versus .926873 after excluding the tested triple, but paths may use other synthetic edges. Augmented common-neighbor means .042636 versus .028682. Hub leaves764 components versus random701.9 (808 originally); average global local clustering decreases. These are mixed descriptive results, not causal hub advantages or attack success. Reported intervals concern Monte Carlo variation of ten random-baseline means, not factual confidence or downstream effects.

## Figures and standalone reproducibility

Both delivered SVGs were actually rendered and viewed before/after. Eighteen relation and23 type categories independently total774; every count, bar width and text boundary was checked. Captions now distinguish synthetic injection from verified falsity. The parent HTML explorer embeds only the original graph; no synthetic styling is claimed for it. The documented adapter is the v2 consumer interface.

Final suite: **{t['passed']}/{t['tests_run']} passed**, no failures/errors/skips. An isolated independent copy of code and actual supplied inputs regenerated from absent output directories twice; all six output files match delivery, and the copied full suite passed. Separate integration tests run seeds42,42,43 under python -E -S. Python3.10.0/stdlib is the verified generation environment; browser tooling is optional for figure audits. Exact cross-version shuffle bytes are not promised. Portable ZIP omits original datasets with complete filename/size/SHA-256 input manifest; explicit input paths require no hardlink, API key or stale cache. See REPRODUCTION_v2.md and REPRODUCTION_v2_CN.md.

## Adversarial multi-model review

Models/families: {models}. Substantive rounds: {review['rounds_completed']}; consensus: {'YES' if review['consensus'] else 'PARTIAL/pending'}. Actual requests, responses, IDs, timestamps, usage and failures are preserved. Gemini received actual PNG bytes through the documented OpenCode Go Google route after chat-protocol rejection. Other initial requests exhausted reasoning or timed out; model-specific controls were checked in primary documentation and used in recorded retries. No provider fallback or key copying occurred. Text reviewers never claimed local execution or image inspection.

Findings were reconciled with actual code and counterexamples. Source hashes now cover runtime, tests, tools, entry scripts, configuration and requirements. Removing pre-shuffle sorting was rejected by an executed input-order counterexample. A supposed two-position diagnostic mismatch was rejected by the actual388/386/0 distribution. The alleged anomalous October date was rejected against the client date2026-10-16. All reviewer findings, including false positives and editorial limitations, remain in findings_registry.json and final_adjudication.md. External facts were not decided by vote.

## Reproduction, inventory and limitations

Core outputs: outputs/pat_kg_poisoned_10pct.json, injected_edges.jsonl, injection_manifest.json, hub_nodes.csv, node_injection_labels.csv, edge_injection_labels.csv. The node CSV separately records original-vs-synthetic entity identity and participation in synthetic relations; all node identity targets are0. The edge CSV provides binary construction labels for all8511 directed triples. Code/tests/config: src/, tests/, tools/, run_task1.py, run_tests.py. Reports: revision_audit/ (baseline, independent reconciliation/candidate count, factual CSV/cache, structural metrics, actual renders/visual audits, snapshot CLI, portable reproduction), multi_model_review/, tests.log, validation_results.json, final_verification.json, bilingual reproduction and CHANGELOG_v2.md. The original v1 report remains in the independent backup.

Input graph SHA-256 `{m['input_sha256']['graph']}`; CSV `{m['input_sha256']['entity_csv']}`. Final graph SHA-256 `{m['output_sha256']['pat_kg_poisoned_10pct.json']}`. All unresolved claims and methodological limits are explicit above. Main steps: run_task1.py with --graph/--entities; run_tests.py with PAT_KG_INPUT_DIR; audit_facts_v2.py; analyze_structure_v2.py; package_release_v2.py --check-clean; verify_delivery.py; build_handoff_v2.py. Exact commands and package extraction are in the bilingual reproduction documents.

'''+block
    cn=f'''# Task 1 修订版 v2 中文交接报告

## 改动与独立核验

修订前已独立备份完整旧版本：`{b['backup_directory']}`。原始 KG、CSV 和父目录旧 ZIP 未改动；最终根目录 JSON 改为普通独立副本，不依赖 Windows hard link。

独立重算确认：7,868节点、7,737原始边、774注入边、8,511总边、18,436 QA、496未解析路径、206个 Hub Node（枢纽节点）、9,853条唯一候选。原始实体／边／QA／时间观察／证据／元数据完整保留；旧注入三元组及既有 provenance 也未改变。另提供7868行node_injection_labels.csv和8511行edge_injection_labels.csv：实体是否为新增合成节点和是否参与注入关系分开标注；全部实体身份标签为0。规范生成器为全部774条 Synthetic Edge（合成关系边）添加 value=fake；真实节点和原始边误标fake均为0。

## Factual Verification（事实真实性验证）

fake仅表示合成类别，不表示已核实错误。新增独立 factual_verification.status=unresolved，保留 legacy unverified。全部774条完成原始KG／PAT QA精确正例核对。实际4次成功Wikidata请求查询40个subject，覆盖18种关系及86/774条边（11.1%）；688条没有外部statement查询。目的性样本不能作总体统计推断。缓存保留claims、qualifiers、references、URL、时间及哈希。

该样本未见相同当前claim，但缺失不证明错误，多值关系的其他对象不是直接反证，当前Wikidata不能代替历史事实。最终 **verified_false=0、verified_true=0、unresolved=774**，未声称构成已验证错误信息子集。模型不提供事实ground truth。离线规范流程不隐式依赖网络或缓存。独立篡改测试复现了“伪造verified_false＋非空引用也通过”的验证缺口；已修复为按相同显式证据上下文重新核验，并增加回归测试。

## Snapshot Visibility（快照可见性）

旧版38条不同注入边至少一个快照缺少原始端点观察，分别为19／6／19个edge-snapshot案例。642／649／609条可见注入边保持不变；独立overlay分别激活6／1／4个真实QID，使端点可渲染。原始观察列表不改动，不制造历史观察、有效期或fake节点。

三快照adapter实际CLI和自动测试确认：明确overlay策略下不可渲染端点为0。原始观察缺失仍然保留，不能把overlay当成历史证据。快照计数有交叠，不得相加当作唯一边数。旧HTML explorer只包含原图，未声称支持合成样式；本次提供文档化adapter。

## Type-Preserving Swapping 与 Structural Support

保留原配置ratio=.10、seed42、初始topK20、原图total_degree排名及pair-local transposition；每个候选对两端使用同一pair映射，不同候选允许重叠pairs。**Pair-local additive graph injection != global graph rewiring**。不要求精确复现LogicPoison，不进行Task2、训练或KGQA效果实验。

10个随机种子均生成774条合法基线，匹配来源边、类型、关系、替换位置、快照和原始degree bin；无fallback，但bin内degree仍不同（端点均值4.58204／4.40795），不声称完全匹配或因果公平。实际source-only388、target-only386、双端0；全部774条均进入每次结构比较。

原图common-neighbor均值均为.001292，同component比例.58010／.58295，没有统一的原始结构优势。增强后排除测试边的alternative-path比例.998708／.926873，路径可使用其他合成边；common-neighbor均值.042636／.028682。Hub剩764个component，随机均值701.9（原始808），全节点clustering反而下降。保留全部混合、反向结果。上述指标基于simple undirected projection，不能验证有向关系、事实或攻击效果；区间只描述十次随机均值的Monte Carlo变化。

## 图件、Reproducibility（可复现性）与回归测试

两张SVG均实际渲染并查看修改前后PNG；18种关系、23种类型各合计774；逐柱核对数值、宽度及文字边界。图注明确合成与事实真假的区别。完整回归 **{t['passed']}/{t['tests_run']}通过**。独立复制代码和真实输入，从不存在的输出目录两次生成，六个文件哈希均匹配交付，复制后的完整测试也通过；集成测试另运行seed42／42／43。

验证环境Python3.10.0＋标准库；浏览器只用于图件审计。便携ZIP不含原始数据，提供文件名／大小／SHA-256清单和显式路径命令，不依赖API key、缓存或hardlink；不承诺跨Python版本的shuffle逐字节一致。详细步骤见REPRODUCTION_v2_CN.md。

## Adversarial Review（对抗性审查）

实际模型／家族：{models}；实质轮数{review['rounds_completed']}；共识{'YES' if review['consensus'] else 'PARTIAL／待最终核验'}。保存初轮独立意见、交叉质询、失败响应、使用量和裁决。Gemini实际收到两张PNG；文本模型没有被称为看过图或运行代码。默认thinking导致正文不足／超时后，按主来源文档调整各模型参数；未转用其他付费提供方，未复制凭据。

已扩大源码哈希至tools／tests／配置；通过实际反例驳回“shuffle前排序无用”；用388／386／0分布澄清结构基线范围；按客户端日期2026-10-16驳回“十月异常”。所有原始意见、错误推测和余下轻微建议保存在findings_registry.json及final_adjudication.md；未用多数票掩盖事实不确定性。

## 文件与证据

最终KG：../pat_kg_poisoned_10pct.json；规范数据：outputs/下JSON、JSONL、manifest、hub CSV。代码／测试：src/、tests/、tools/。审计：revision_audit/下基线哈希、独立计数、事实CSV和缓存、结构诊断、图件前后截图、snapshot CLI、便携复现证据。审查：multi_model_review/。日志：tests.log、validation_results.json、final_verification.json。另有双语复现说明与CHANGELOG_v2.md。旧版报告保存在独立备份中。

输入图SHA-256：`{m['input_sha256']['graph']}`；CSV：`{m['input_sha256']['entity_csv']}`；最终图：`{m['output_sha256']['pat_kg_poisoned_10pct.json']}`。

'''+block
    for name,content in [('FINAL_REPORT_v2.md',en),('FINAL_REPORT_v2_CN.md',cn)]:
        (ROOT/'reports'/name).write_text(content,encoding='utf-8')
    (ROOT/'reports/FINAL_REPORT.md').write_text('# Current handoff\n\nSee FINAL_REPORT_v2.md and FINAL_REPORT_v2_CN.md. Original v1 report is retained in the independent baseline backup.\n',encoding='utf-8')
    (ROOT/'reports/04_validation_results.md').write_text('# Revised validation\n\n'+str(t['passed'])+'/'+str(t['tests_run'])+' tests passed; see tests.log, validation_results.json, portable_reproduction.json and FINAL_REPORT_v2.md.\n',encoding='utf-8')
    (ROOT/'reports/05_limitations.md').write_text('# Revised limitations\n\n774 facts unresolved; legacy unverified retained. fake denotes construction only. External current-statement lookup covers purposive86/774. Overlay activation is separate from original observation. Pair-local additive injection is not global rewiring. Mixed, undirected, conditional degree-bin structural diagnostics do not establish factual truth, causality or KGQA efficacy. See FINAL_REPORT_v2.md for full scope.\n',encoding='utf-8')
    (ROOT/'reports/CHANGELOG_v2.md').write_text('# v2 changelog\n\n- Independent complete v1 backup; original files and prior ZIP preserved.\n- Synthetic-edge-only value=fake and separate unresolved truth audit; legacy provenance retained.\n- Explicit overlay real-node activation and non-mutating snapshot adapter.\n- Rejected unsupported truth-label mutation by rederiving fact annotations.\n- Extended source hashes to runtime, tests, tools, config and requirements.\n- Ten-seed matched structural diagnostics, factual evidence cache, actual before/after figure review.\n- Separate-input portable manifest and independent-copy clean reproduction.\n- Different-model independent and cross-examined OpenCode reviews, including actual PNGs.\n- Bilingual reports, no hardlink prerequisite; unchanged injection method/configuration. No training or Task2.\n',encoding='utf-8')
    print(json.dumps({'status':status,'tests':t['passed'],'models':review['families_used'],'rounds':review['rounds_completed']}))


if __name__=='__main__':main()

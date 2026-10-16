# Primary-source method boundaries

Sources retrieved with Exa Search and Exa Fetch on 2026-10-16 (Asia/Seoul task date). Ten results were requested across two targeted searches; primary paper and API documentation pages were checked. This was a focused implementation check, not an exhaustive literature review.

- [LogicPoison paper](https://arxiv.org/html/2604.02954), Sections 3, 4.1 and cyclic-permutation/corpus-rewriting paragraphs: the paper attacks a corpus before graph extraction, estimates global hubs from within-type document frequency, includes query-centric entities, and applies a type-preserving cyclic bijection to mentions. Our implementation instead uses explicit graph degree, pair-local transpositions and additive graph edges. It retains original paths and therefore does not reproduce the paper's rewiring or establish downstream attack efficacy.
- [PAT-Questions paper](https://arxiv.org/html/2402.11034v2), dataset-construction and answer-updating sections: benchmark answers are generated/refreshed with Wikidata and SPARQL. In this project the local source metadata defines snapshots as annotation observations. Projected edges do not reconstruct statement qualifiers, historical intervals or the temporal ordering needed by every QA template.
- [OpenCode Go documentation](https://opencode.ai/docs/go/): consulted for the configured service boundary. The existing local helper supplies the actual base URL, model, request headers and credential lookup. Successful inference, returned text and usage are checked in the saved implementation/review response artifacts; model-list availability alone is not used as execution evidence.
- [Kimi K2.6 provider documentation](https://platform.kimi.ai/docs/guide/kimi-k2-6-quickstart): documents `thinking: {"type": "disabled"}` for requests that require a direct final response. The task-local OpenCode client supports that request parameter. Its acceptance by the configured OpenCode proxy is established only by the recorded live response, not assumed from Moonshot documentation.

## Access and integration limits

The referenced ChatGPT conversation could not be read because no `read_thread` tool was available in this execution. The supplied detailed Task 1 specification and actual local files govern the implementation. No claims are made about unseen conversation contents.

The available Manus tools create research, slides, websites, video or mobile-app jobs; they cannot edit or validate this local graph. No `get_status` tool was exposed to collect asynchronous jobs. No Manus job was launched. Ace Knowledge Graph can illustrate a bounded non-personal methodology graph; it is not used as the canonical PAT-KG data processor or factual verifier. DevSpace was not invoked.

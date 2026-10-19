# StatPro Context Map

| Bounded context | Glossary | Owns |
|---|---|---|
| Shared Data | [`CONTEXT.md`](CONTEXT.md) | Dataset, Worksheet, content identity, shared provenance vocabulary |
| Statistical Analysis | [`src/statpro/analyses/CONTEXT.md`](src/statpro/analyses/CONTEXT.md) | Analysis definitions, analysis runs, statistical results and diagnostics |
| FMEA | [`src/statpro/fmea/CONTEXT.md`](src/statpro/fmea/CONTEXT.md) | FMEA studies, failure analyses, risk ratings, recommended actions and approvals |

## Relationships

- Statistical Analysis consumes immutable Dataset or Worksheet Revision values and records their digests.
- FMEA may cite a Dataset, Worksheet Revision, Analysis Run, or Result Bundle only through an immutable Evidence Reference.
- Statistical Analysis does not mutate FMEA studies, ratings, actions, or approvals.
- FMEA does not reinterpret statistical result internals; the Statistical Analysis context owns those meanings.
- Shared Data does not own statistical interpretation or FMEA workflow state.

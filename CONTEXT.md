# StatPro Shared Domain Glossary

| Term | Meaning |
|---|---|
| Project | A versioned workspace containing datasets, analyses, reports, and audit history. |
| Dataset | An immutable imported data snapshot identified by a content digest. |
| Source Digest | SHA-256 identity of the exact imported source bytes. |
| Dataset Digest | SHA-256 identity of normalized typed values and import semantics; source location is excluded. |
| Worksheet | A user-editable tabular view derived from a Dataset or another Worksheet. |
| Worksheet Revision | An immutable Worksheet state produced by an edit or transformation and linked to its parent digest. |
| Variable | A typed worksheet column: numeric, categorical, text, date-time, or logical. |
| Missing Value | An explicitly absent cell represented independently from zero, false, and empty text. |
| Provenance | The sources, transformations, versions, parameters, and digests that explain how an artifact was produced. |
| Evidence Reference | An immutable identifier or digest linking one context to evidence owned by another context. |

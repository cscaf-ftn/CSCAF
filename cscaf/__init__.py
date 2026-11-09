"""CSCAF: Cyber Security Curriculum Alignment Framework.

- `cscaf.study`: every parameter of the study, read once from `config.yaml`;
- `cscaf.storage`: the SQLite database, one repository per part of the schema;
- `cscaf.framework`: the reference framework (ECSF v1);
- `cscaf.text`: preprocessing, sentence segmentation, embeddings and the English check;
- `cscaf.translation`: machine translation of the lines that are not in English;
- `cscaf.loading`: the loaders of the notebooks of `data_load/`;
- `cscaf.calibration`: the calibration of the matching threshold (Section 3.4 of the paper);
- `cscaf.measures`: the measures of Table 2 of the paper and the analyses of Section 4;
- `cscaf.figures`: the figures of the paper.
"""

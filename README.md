# CSCAF: Cyber Security Curriculum Alignment Framework

CSCAF measures how well cybersecurity curricula and job advertisements align with the twelve role profiles of the
European Cybersecurity Skills Framework (ECSF). It works in two directions: from a curriculum to the roles it covers,
and from the advertisements of an employer to a message for the curriculum of its country.

## Paper

This repository accompanies the paper

> "Talking Through a Framework: A Calibrated Method for Two-Way Alignment of Cybersecurity Curricula and Job
> Advertisements with the European Cybersecurity Skills Framework". Submitted to *Computers* (MDPI), 2026.

## Repository structure

```text
cscaf/             the method: measures, threshold calibration, text processing, loaders, figures
config.yaml        every parameter of the study (threshold, seed, models)
data_load/         builds the database from raw_data
methodology/       Section 3 of the paper
results/           Section 4 of the paper
reproduce_all.ipynb  runs every notebook in order and compares every number with the paper
paper_checks/      the values printed in the paper, compared with the records in output/ by reproduce_all
requirements.txt   the versions of the packages
```

## Notebooks

| Notebook | Paper | Figures | Tables |
|---|---|---|---|
| `methodology/01_reference_framework.ipynb` | 3.1 Reference Framework | | |
| `methodology/02_data.ipynb` | 3.2 Data | | Table 1, Table S1 |
| `methodology/03_text_processing.ipynb` | 3.3 Text Processing | | |
| `methodology/04_threshold_calibration.ipynb` | 3.4 Calibration of the Matching Threshold | Figure 2 | Table S2 |
| `results/05_role_level_results.ipynb` | 4.1 Role-Level Results | Figures 3-5 | Table 3, Table S3 |
| `results/06_curriculum_update.ipynb` | 4.2 Curriculum Update | Figures 6-7 | Tables 4-5 |
| `results/07_employer_demand.ipynb` | 4.3 Employer Demand | Figure 8 | Tables 6-7, Table S4 |

Each notebook is run from its own folder. It writes the numbers it reports to `output/` and its figures to
`figures/` of that folder. All parameters are read from `config.yaml`.

The saved outputs and figures show the results of the paper. Advertisers appear only by the codes of the paper.

## Data

The folder `raw_data/` and the database built from it are not part of this repository. The data are available from the
authors on reasonable request, as one zip archive.

Unpack the archive so that `raw_data/` lies next to `config.yaml`.

## Reproducing the results

The results were computed with Python 3.12.6.

```text
py -3.12 -m venv venv                 (Linux: python3.12 -m venv venv)
venv\Scripts\activate                (Linux: source venv/bin/activate)
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace reproduce_all.ipynb
```

`reproduce_all.ipynb` checks that `raw_data/` is in place, builds `database/CSCAF_public.db` with the notebooks of
`data_load/` if it does not exist, runs the notebooks of `methodology/` and `results/` in order, and ends with one table:
errors, the numbers that agree with the paper, and the figures written. Building the database needs a CUDA GPU (6 GB
was enough; `device` in `config.yaml`), about one hour and 3 GB of disk, and downloads the two models at the revisions
pinned in `config.yaml`. Computed anew on another GPU, embeddings can differ from the original ones in the last digits
of a float32 value.

## License

The content of this repository, code, results and figures, is licensed under the Creative Commons Attribution 4.0
International License (CC BY 4.0), the license of the paper; see [LICENSE](LICENSE).

The license does not cover third-party material. The ECSF keeps its own terms, see [NOTICE](NOTICE). The raw data are not
part of this repository, and they are not licensed by it.

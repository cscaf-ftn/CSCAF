PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;
CREATE TABLE country (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            is_eu BOOLEAN NOT NULL,
                            is_efta BOOLEAN NOT NULL
                        );
CREATE TABLE run (
    run_id                 TEXT PRIMARY KEY,
    created_at             TEXT NOT NULL,
    segmentation_engine    TEXT,
    segmentation_model     TEXT,
    segmentation_revision  TEXT,
    embedding_model        TEXT NOT NULL,
    embedding_revision     TEXT,
    config_hash            TEXT NOT NULL,
    code_version           TEXT,
    notes                  TEXT
);
CREATE TABLE job_advertisement_snapshot (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at            TEXT    NOT NULL,
    source_file           TEXT    NOT NULL,
    source_sha256         TEXT    NOT NULL UNIQUE,
    source_collection     TEXT,
    n_in_file             INTEGER NOT NULL,
    n_not_eu              INTEGER NOT NULL,
    n_duplicates_removed  INTEGER NOT NULL,
    n_loaded              INTEGER NOT NULL,
    dedup_rule            TEXT    NOT NULL,
    notes                 TEXT
);
CREATE TABLE rf_section (
                            id          INTEGER PRIMARY KEY AUTOINCREMENT,
                            short_name  TEXT NOT NULL UNIQUE,
                            full_name   TEXT NOT NULL
                        );
CREATE TABLE view_rf_sentences (
                            id                  INTEGER,
                            ord                 INTEGER,
                            section             TEXT,
                            sub_section         TEXT,
                            sentence            TEXT,
                            sentence_embedding  BLOB,
                            embedding_dim       INTEGER,
                            embedding_dtype     TEXT,
                            embedding_model     TEXT,
                            rf_sentence_id      INTEGER,
                            section_short_name  TEXT
                        );
CREATE TABLE industry_training (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    code                TEXT    NOT NULL,
    title               TEXT    NOT NULL,
    source_description  TEXT    NOT NULL,
    source_url          TEXT    NOT NULL,
    accessed_date       TEXT    NOT NULL,
    variant             TEXT    NOT NULL,
    sections_taken      TEXT    NOT NULL,
    text                TEXT    NOT NULL,
    notes               TEXT,
    UNIQUE (code, variant),
    CHECK (accessed_date LIKE '____-__-__'),
    CHECK (length(trim(text)) > 0)
);
CREATE TABLE curriculum
(
    id              INTEGER primary key autoincrement,
    curriculum_key  TEXT not null unique,
    university_name TEXT not null,
    faculty_name    text not null,
    programme_name  TEXT not null,
    friendly_name   TEXT not null,
    short_name      TEXT,
    year          INTEGER,
    country       TEXT,
    country_id INTEGER, edition TEXT,
    FOREIGN KEY (country_id) REFERENCES country(id)
);
CREATE TABLE job_advertisement (
    id                              INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id                     INTEGER NOT NULL REFERENCES job_advertisement_snapshot(id),
    job_key                         TEXT    NOT NULL UNIQUE,
    country_id                      INTEGER NOT NULL REFERENCES country(id),
    country                         TEXT    NOT NULL,
    date_posted                     TEXT    NOT NULL,
    date_posted_unix                INTEGER NOT NULL,
    location                        TEXT,
    company                         TEXT    NOT NULL,
    title                           TEXT    NOT NULL,
    title_before_translation        TEXT    NOT NULL,
    description                     TEXT    NOT NULL,
    description_before_translation  TEXT    NOT NULL,
    content_hash                    TEXT    NOT NULL,
    UNIQUE (snapshot_id, content_hash)
);
CREATE TABLE rf_subsection (
                            id             INTEGER PRIMARY KEY AUTOINCREMENT,
                            name           TEXT NOT NULL,
                            rf_section_id  INTEGER NOT NULL,
                            FOREIGN KEY (rf_section_id) REFERENCES rf_section(id),
                            UNIQUE (rf_section_id, name)
                        );
CREATE TABLE rf_sentence (
                            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                            run_id              TEXT NOT NULL REFERENCES run(run_id),
                            sentence            TEXT NOT NULL UNIQUE,
                            sentence_embedding  BLOB,
                            embedding_dim       INTEGER,
                            embedding_dtype     TEXT,
                            embedding_model     TEXT,
                            CHECK ((sentence_embedding IS NULL) = (embedding_dim IS NULL)),
                            CHECK ((sentence_embedding IS NULL) = (embedding_dtype IS NULL)),
                            CHECK ((sentence_embedding IS NULL) = (embedding_model IS NULL))
                        );
CREATE TABLE industry_training_role (
    industry_training_id   INTEGER NOT NULL,
    rf_section_short_name  TEXT    NOT NULL,
    PRIMARY KEY (industry_training_id, rf_section_short_name),
    FOREIGN KEY (industry_training_id) REFERENCES industry_training(id),
    FOREIGN KEY (rf_section_short_name) REFERENCES rf_section(short_name)
);
CREATE TABLE industry_training_sentence (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id                TEXT    NOT NULL,
    ord                   INTEGER NOT NULL,
    industry_training_id  INTEGER NOT NULL,
    sentence              TEXT    NOT NULL,
    sentence_embedding    BLOB,
    embedding_dim         INTEGER,
    embedding_dtype       TEXT,
    embedding_model       TEXT,
    FOREIGN KEY (run_id) REFERENCES run(run_id),
    FOREIGN KEY (industry_training_id) REFERENCES industry_training(id),
    CHECK ((sentence_embedding IS NULL) = (embedding_dim IS NULL)),
    CHECK ((sentence_embedding IS NULL) = (embedding_dtype IS NULL)),
    CHECK ((sentence_embedding IS NULL) = (embedding_model IS NULL)),
    UNIQUE (run_id, industry_training_id, ord),
    UNIQUE (run_id, industry_training_id, sentence)
);
CREATE TABLE "syllabus" (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    curriculum_id   INTEGER NOT NULL,
    curriculum_key  TEXT NOT NULL,
    name            TEXT NOT NULL,
    ects_credits    REAL,
    text            TEXT NOT NULL,
    FOREIGN KEY (curriculum_id) REFERENCES curriculum(id),
    UNIQUE (curriculum_id, name)
);
CREATE TABLE job_advertisement_sentence (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id                TEXT    NOT NULL REFERENCES run(run_id),
    ord                   INTEGER NOT NULL,
    job_advertisement_id  INTEGER NOT NULL REFERENCES job_advertisement(id),
    job_key               TEXT    NOT NULL,
    part                  TEXT    NOT NULL CHECK (part IN ('title', 'description')),
    sentence              TEXT    NOT NULL,
    sentence_embedding    BLOB,
    embedding_dim         INTEGER,
    embedding_dtype       TEXT,
    embedding_model       TEXT,
    CHECK ((sentence_embedding IS NULL) = (embedding_dim IS NULL)),
    CHECK ((sentence_embedding IS NULL) = (embedding_dtype IS NULL)),
    CHECK ((sentence_embedding IS NULL) = (embedding_model IS NULL)),
    UNIQUE (run_id, job_advertisement_id, ord),
    UNIQUE (run_id, job_advertisement_id, sentence)
);
CREATE TABLE rf_subsection_sentence (
                            id                INTEGER PRIMARY KEY AUTOINCREMENT,
                            rf_subsection_id  INTEGER NOT NULL,
                            rf_sentence_id    INTEGER NOT NULL,
                            ord               INTEGER NOT NULL,
                            FOREIGN KEY (rf_subsection_id) REFERENCES rf_subsection(id),
                            FOREIGN KEY (rf_sentence_id) REFERENCES rf_sentence(id),
                            UNIQUE (rf_subsection_id, rf_sentence_id),
                            UNIQUE (rf_subsection_id, ord)
                        );
CREATE TABLE industry_training_rf_similarity_all (
    id                            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id                        TEXT    NOT NULL,
    rf_sentence_id                INTEGER NOT NULL,
    industry_training_sentence_id INTEGER NOT NULL,
    similarity_score              REAL    NOT NULL,
    industry_training_id          INTEGER NOT NULL,
    industry_training_code        TEXT    NOT NULL,
    FOREIGN KEY (run_id) REFERENCES run(run_id),
    FOREIGN KEY (rf_sentence_id) REFERENCES rf_sentence(id),
    FOREIGN KEY (industry_training_sentence_id) REFERENCES industry_training_sentence(id),
    FOREIGN KEY (industry_training_id) REFERENCES industry_training(id),
    UNIQUE (run_id, rf_sentence_id, industry_training_sentence_id),
    CHECK (similarity_score BETWEEN -1.0 AND 1.0)
);
CREATE TABLE industry_training_rf_similarity_top_1 (
    id                            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id                        TEXT    NOT NULL,
    rf_sentence_id                INTEGER NOT NULL,
    industry_training_sentence_id INTEGER NOT NULL,
    similarity_score              REAL    NOT NULL,
    industry_training_id          INTEGER NOT NULL,
    industry_training_code        TEXT    NOT NULL,
    is_primary                    INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (run_id) REFERENCES run(run_id),
    FOREIGN KEY (rf_sentence_id) REFERENCES rf_sentence(id),
    FOREIGN KEY (industry_training_sentence_id) REFERENCES industry_training_sentence(id),
    FOREIGN KEY (industry_training_id) REFERENCES industry_training(id),
    UNIQUE (run_id, rf_sentence_id, industry_training_sentence_id),
    CHECK (similarity_score BETWEEN -1.0 AND 1.0),
    CHECK (is_primary IN (0, 1))
);
CREATE TABLE curriculum_sentence (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id              TEXT NOT NULL REFERENCES run(run_id),
    ord                 INTEGER NOT NULL,
    syllabus_id         INTEGER NOT NULL,
    syllabus_name       TEXT NOT NULL,
    curriculum_key      TEXT NOT NULL,
    sentence            TEXT NOT NULL,
    sentence_embedding  BLOB,
    embedding_dim       INTEGER,
    embedding_dtype     TEXT,
    embedding_model     TEXT,
    FOREIGN KEY (syllabus_id) REFERENCES syllabus(id),
    CHECK ((sentence_embedding IS NULL) = (embedding_dim IS NULL)),
    CHECK ((sentence_embedding IS NULL) = (embedding_dtype IS NULL)),
    CHECK ((sentence_embedding IS NULL) = (embedding_model IS NULL)),
    UNIQUE (run_id, syllabus_id, ord),
    UNIQUE (run_id, syllabus_id, sentence)
);
CREATE TABLE job_advertisement_rf_similarity_all (
    id                             INTEGER PRIMARY KEY AUTOINCREMENT,
    job_advertisement_sentence_id  INTEGER NOT NULL REFERENCES job_advertisement_sentence(id),
    rf_sentence_id                 INTEGER NOT NULL REFERENCES rf_sentence(id),
    similarity_score               REAL    NOT NULL,
    UNIQUE (job_advertisement_sentence_id, rf_sentence_id)
);
CREATE TABLE job_advertisement_rf_similarity_top_1 (
    id                             INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id                         TEXT    NOT NULL REFERENCES run(run_id),
    rf_sentence_id                 INTEGER NOT NULL REFERENCES rf_sentence(id),
    job_advertisement_sentence_id  INTEGER NOT NULL REFERENCES job_advertisement_sentence(id),
    similarity_score               REAL    NOT NULL,
    job_advertisement_id           INTEGER NOT NULL REFERENCES job_advertisement(id),
    job_key                        TEXT    NOT NULL,
    country_id                     INTEGER NOT NULL REFERENCES country(id),
    part                           TEXT    NOT NULL,
    UNIQUE (run_id, job_advertisement_id, rf_sentence_id)
);
CREATE TABLE curriculum_rf_similarity_all (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id                  TEXT    NOT NULL REFERENCES run(run_id),
    rf_sentence_id          INTEGER NOT NULL REFERENCES rf_sentence(id),
    curriculum_sentence_id  INTEGER NOT NULL REFERENCES curriculum_sentence(id),
    similarity_score        REAL    NOT NULL,
    curriculum_id           INTEGER NOT NULL REFERENCES curriculum(id),
    curriculum_key          TEXT    NOT NULL,
    syllabus_id             INTEGER NOT NULL REFERENCES syllabus(id),
    curriculum_syllabus     TEXT    NOT NULL,
    UNIQUE (run_id, rf_sentence_id, curriculum_sentence_id)
);
CREATE TABLE curriculum_rf_similarity_top_1 (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id                  TEXT    NOT NULL REFERENCES run(run_id),
    rf_sentence_id          INTEGER NOT NULL REFERENCES rf_sentence(id),
    curriculum_sentence_id  INTEGER NOT NULL REFERENCES curriculum_sentence(id),
    similarity_score        REAL    NOT NULL,
    curriculum_id           INTEGER NOT NULL REFERENCES curriculum(id),
    curriculum_key          TEXT    NOT NULL,
    syllabus_id             INTEGER NOT NULL REFERENCES syllabus(id),
    curriculum_syllabus     TEXT    NOT NULL,
    is_primary              INTEGER NOT NULL CHECK (is_primary IN (0, 1)),
    UNIQUE (run_id, curriculum_id, rf_sentence_id, curriculum_sentence_id)
);
CREATE TABLE curriculum_syllabus_rf_top_1 (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id                  TEXT    NOT NULL REFERENCES run(run_id),
    rf_sentence_id          INTEGER NOT NULL REFERENCES rf_sentence(id),
    curriculum_sentence_id  INTEGER NOT NULL REFERENCES curriculum_sentence(id),
    similarity_score        REAL    NOT NULL,
    curriculum_id           INTEGER NOT NULL REFERENCES curriculum(id),
    curriculum_key          TEXT    NOT NULL,
    syllabus_id             INTEGER NOT NULL REFERENCES syllabus(id),
    curriculum_syllabus     TEXT    NOT NULL,
    UNIQUE (run_id, syllabus_id, rf_sentence_id)
);
CREATE INDEX idx_curriculum_sentence_curriculum ON curriculum_sentence(run_id, curriculum_key);
CREATE INDEX idx_curriculum_rf_similarity_all_pair
    ON curriculum_rf_similarity_all(run_id, curriculum_id, rf_sentence_id);
CREATE UNIQUE INDEX idx_curriculum_rf_similarity_top_1_primary
    ON curriculum_rf_similarity_top_1(run_id, curriculum_id, rf_sentence_id) WHERE is_primary = 1;
CREATE INDEX idx_job_advertisement_country ON job_advertisement(country_id, date_posted);
CREATE INDEX idx_job_advertisement_rf_similarity_top_1_statement
    ON job_advertisement_rf_similarity_top_1(run_id, rf_sentence_id, country_id);
CREATE INDEX idx_curriculum_syllabus_rf_top_1_curriculum
    ON curriculum_syllabus_rf_top_1(run_id, curriculum_id, rf_sentence_id);
CREATE INDEX idx_rf_subsection_section
                            ON rf_subsection(rf_section_id);
CREATE INDEX idx_rf_subsection_sentence_sentence
                            ON rf_subsection_sentence(rf_sentence_id);
CREATE INDEX idx_view_rf_sentences_sentence
                            ON view_rf_sentences(rf_sentence_id);
CREATE INDEX idx_view_rf_sentences_section
                            ON view_rf_sentences(section_short_name);
CREATE INDEX idx_industry_training_accessed_date
    ON industry_training(accessed_date);
CREATE INDEX idx_industry_training_role_section
    ON industry_training_role(rf_section_short_name);
CREATE INDEX idx_industry_training_sentence_training
    ON industry_training_sentence(run_id, industry_training_id);
CREATE INDEX idx_industry_training_rf_similarity_all_pair
    ON industry_training_rf_similarity_all(run_id, industry_training_id, rf_sentence_id);
CREATE INDEX idx_industry_training_rf_similarity_top_1_primary
    ON industry_training_rf_similarity_top_1(run_id, industry_training_id, is_primary);
COMMIT;

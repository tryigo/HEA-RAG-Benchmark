# HEA RAG benchmark

This dataset contains 100 questions used to compare Qwen3.8-27B in Closed-book and retrieval-augmented generation (RAG) modes for high-entropy alloy research. Questions and reference scoring criteria are provided in the original Chinese.

| Category | Questions |
| --- | ---: |
| A — Fact & Quantitative | 30 |
| B — Mechanism Explanation | 30 |
| C — Cross-literature Synthesis | 20 |
| D — Insufficient Information | 20 |

## Files

- `questions.csv`: question IDs, categories and question text.
- `reference_rubric.json`: reference claims and scoring instructions for each question.
- `sources.json`: bibliographic records cited by the rubric, indexed by source ID.
- `per_question_metrics.csv`: claim counts, citation counts, scores and recorded times for the two evaluated modes; 200 rows in total.
- `summarize.py`: calculates overall and category-level results from the recorded counts.
- `summary_metrics.csv`: output from the script.

Question IDs link the files. CSV files use UTF-8 with a byte-order mark for compatibility with Excel. In the rubric, `scoreable_for_recall` identifies claims included in Recall; `coverage_group` and `group_required` specify grouped criteria. The file also records the exceptions used in scoring.

## Recalculate the results

Run with Python 3.8 or later. No additional packages are required.

```sh
python summarize.py
```

The script writes `summary_metrics.csv`. Precision, Recall, F1, Faithfulness and Hallucination Rate are averaged over questions. Citation Precision is the ratio of pooled valid citations to pooled total citations. Abstention Accuracy is calculated only for category D. A blank question-level Citation Precision means that the response contained no citations; a blank Abstention value means the question is outside category D.

Times are in seconds. `Response_Time_s` is the generation-request time in Closed-book mode and the sum of retrieval and generation-request times in RAG mode. Reported timing summaries describe these recorded estimates.

This release supports recalculation of the paper's summary statistics. It does not include the platform deployment code, model inference pipeline or full-text literature collection.

# HEA RAG benchmark

Working data for a manuscript comparing Qwen3.8-27B in Closed-book and retrieval-augmented generation (RAG) modes. The dataset contains 100 questions and 200 response-level evaluation records. Questions are provided in the original Chinese.

| Category | Questions |
| --- | ---: |
| A — Fact & Quantitative | 30 |
| B — Mechanism Explanation | 30 |
| C — Cross-literature Synthesis | 20 |
| D — Insufficient Information | 20 |

## Files

- `questions.csv`: question IDs, categories and question text.
- `per_question_metrics.csv`: claim counts, citation counts, scores and recorded times for both modes.
- `summarize.py`: recalculates overall and category-level statistics.
- `summary_metrics.csv`: output from the script.

Question IDs link the CSV files. CSV files use UTF-8 with a byte-order mark for compatibility with Excel.

## Recalculate the results

Run with Python 3.8 or later; no additional packages are required.

```sh
python summarize.py
```

The script writes `summary_metrics.csv`. Precision, Recall, F1, Faithfulness and Hallucination Rate are averaged over questions. Citation Precision uses pooled citation counts. Abstention Accuracy is calculated only for category D. A blank Citation Precision means that a response has no citations; a blank Abstention value means that the question is outside category D.

Times are in seconds. Estimated response time is the generation-request time in Closed-book mode and the sum of retrieval and generation-request times in RAG mode.

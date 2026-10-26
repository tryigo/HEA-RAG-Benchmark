#!/usr/bin/env python3
"""Recalculate the manuscript summaries from recorded per-response counts."""

import argparse
import csv
import math
from collections import Counter
from fractions import Fraction
from pathlib import Path
from statistics import mean, median

MODES = ('closed_book', 'rag')
SCOPES = ('ALL', 'A', 'B', 'C', 'D')


def ratio(numerator, denominator):
    return Fraction(int(numerator), int(denominator)) if int(denominator) else None


def response_scores(row):
    precision = ratio(row['N_correct'], row['N_generated'])
    recall = ratio(row['N_covered'], row['N_reference'])
    if precision is None or recall is None:
        raise ValueError('Generated-claim and reference-claim counts must be positive.')
    return {
        'Precision': precision,
        'Recall': recall,
        'F1': 2 * precision * recall / (precision + recall) if precision + recall else Fraction(0),
        'Faithfulness': ratio(row['N_supported'], row['N_generated']),
        'Hallucination_Rate': ratio(row['N_unsupported'], row['N_generated']),
        'Citation_Precision': ratio(row['N_valid_citations'], row['N_all_citations']),
    }


def validate(rows):
    if len(rows) != 200 or Counter(row['Mode'] for row in rows) != {'closed_book': 100, 'rag': 100}:
        raise ValueError('Expected 100 questions in each of the two modes.')
    expected_ids = {'Q%03d' % n for n in range(1, 101)}
    for mode in MODES:
        selected = [row for row in rows if row['Mode'] == mode]
        if {row['Question_ID'] for row in selected} != expected_ids:
            raise ValueError('Question IDs must cover Q001 through Q100 in both modes.')
        if Counter(row['Type'] for row in selected) != {'A': 30, 'B': 30, 'C': 20, 'D': 20}:
            raise ValueError('Unexpected category counts.')
    categories = {}
    for row in rows:
        if row['Model'] != 'qwen3.8:27b':
            raise ValueError('Unexpected model.')
        qid = row['Question_ID']
        if categories.setdefault(qid, row['Type']) != row['Type']:
            raise ValueError('Category differs between modes: ' + qid)
        for key, value in row.items():
            if key.startswith('N_') and int(value) < 0:
                raise ValueError('Negative count: ' + qid)
        for subset, total in [('N_correct', 'N_generated'), ('N_covered', 'N_reference'),
                              ('N_valid_citations', 'N_all_citations')]:
            if int(row[subset]) > int(row[total]):
                raise ValueError('Count exceeds denominator: ' + qid)
        if int(row['N_supported']) + int(row['N_unsupported']) != int(row['N_generated']):
            raise ValueError('Supported and unsupported claims do not partition generated claims: ' + qid)
        for key, value in response_scores(row).items():
            if value is None:
                if row[key] != '':
                    raise ValueError('Expected missing score: ' + qid + ' ' + key)
            elif not math.isclose(float(value), float(row[key]), rel_tol=0, abs_tol=0.00000051):
                raise ValueError('Recorded score differs from counts: ' + qid + ' ' + key)
        allowed = {'0', '1'} if row['Type'] == 'D' else {''}
        if row['Abstention'] not in allowed:
            raise ValueError('Unexpected abstention value: ' + qid)
        generation = float(row['Generation_Time_s'])
        retrieval = float(row['Retrieval_Time_s'] or 0)
        response = float(row['Response_Time_s'])
        if not all(math.isfinite(v) and v >= 0 for v in (generation, retrieval, response)):
            raise ValueError('Invalid recorded time: ' + qid)
        if not math.isclose(generation + retrieval, response, rel_tol=0, abs_tol=0.000002):
            raise ValueError('Response-time components do not match: ' + qid)


def summarize(rows):
    output = []
    for scope in SCOPES:
        for mode in MODES:
            selected = [r for r in rows if r['Mode'] == mode and (scope == 'ALL' or r['Type'] == scope)]
            scores = [response_scores(row) for row in selected]
            record = {'Scope': scope, 'Mode': mode, 'Questions': len(selected)}
            for key in ('Precision', 'Recall', 'F1', 'Faithfulness', 'Hallucination_Rate'):
                record[key] = float(sum((s[key] for s in scores), Fraction(0)) / len(scores))
            valid = sum(int(r['N_valid_citations']) for r in selected)
            total = sum(int(r['N_all_citations']) for r in selected)
            record.update(N_valid_citations=valid, N_all_citations=total,
                          Citation_Precision=valid / total if total else '')
            abstention_rows = [r for r in selected if r['Type'] == 'D']
            record['Abstention_Questions'] = len(abstention_rows)
            record['Abstention_Accuracy'] = (mean(int(r['Abstention']) for r in abstention_rows)
                                              if abstention_rows else '')
            times = [float(r['Response_Time_s']) for r in selected]
            record['Mean_Response_Time_s'] = mean(times)
            record['Median_Response_Time_s'] = median(times)
            output.append(record)
    return output


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=here / 'per_question_metrics.csv')
    parser.add_argument('--output', type=Path, default=here / 'summary_metrics.csv')
    args = parser.parse_args()
    with args.input.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    validate(rows)
    summary = summarize(rows)
    with args.output.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary[0]), lineterminator='\n')
        writer.writeheader()
        for record in summary:
            writer.writerow({k: format(v, '.9f') if isinstance(v, float) else v for k, v in record.items()})
    print('Validated %d responses; wrote %s' % (len(rows), args.output.name))


if __name__ == '__main__':
    main()

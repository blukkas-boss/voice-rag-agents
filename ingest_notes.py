#!/usr/bin/env python3
import sqlite3
import requests
import json
import os
import sys

GOALS_DB = os.path.expanduser('~/.openclaw/workspace/goals/goals.db')
DAILY_DB = os.path.expanduser('~/.openclaw/workspace/daily/daily.db')
API_URL = 'http://localhost:8088/ingest'

def fetch_transcripts(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT message_id, date_utc, duration_s, transcript FROM notes WHERE transcribed=1')
    rows = cur.fetchall()
    conn.close()
    notes = []
    for r in rows:
        notes.append({
            'message_id': r['message_id'],
            'date_utc': r['date_utc'],
            'duration_s': r['duration_s'],
            'transcript': r['transcript']
        })
    return notes

def main():
    goals_notes = fetch_transcripts(GOALS_DB)
    daily_notes = fetch_transcripts(DAILY_DB)
    print(f'Found {len(goals_notes)} goal notes and {len(daily_notes)} daily notes')
    all_notes = goals_notes + daily_notes
    # Prepare documents for ingestion: each note as a separate document
    documents = []
    for note in all_notes:
        text = note['transcript'].strip()
        if not text:
            continue
        # Use a source file name indicating origin and message id
        source = f"voice_note_{'goal' if note['message_id'] < 0 else 'daily'}_{note['message_id']}.md"
        documents.append({
            'text': text,
            'source_file': source
        })
    if not documents:
        print('No non-empty transcripts to ingest')
        return
    # Ingest in batches of, say, 5 documents to avoid huge payload
    batch_size = 5
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        payload = {'documents': batch}
        print(f'Ingesting batch {i//batch_size + 1} ({len(batch)} documents)...')
        resp = requests.post(API_URL, json=payload, timeout=30)
        if resp.status_code != 200:
            print(f'Error: {resp.status_code} {resp.text}')
            sys.exit(1)
        result = resp.json()
        print(f'  Result: run_id={result.get("run_id")} status={result.get("status")}')
        # optionally print report
        report = result.get('report', {})
        if report:
            print(f'    processed={report.get("documents_processed")} chunks={report.get("chunks_created")} embeddings={report.get("embeddings_generated")} upserted={report.get("records_upserted")}')
    print('Ingestion complete.')

if __name__ == '__main__':
    main()

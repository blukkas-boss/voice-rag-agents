#!/usr/bin/env python3
import sqlite3
import requests
import json
import os
import sys

GOALS_DB = os.path.expanduser('~/.openclaw/workspace/goals/goals.db')
DAILY_DB = os.path.expanduser('~/.openclaw/workspace/daily/daily.db')
STATE_FILE = os.path.expanduser('~/.openclaw/workspace/voice_rag_agents/.ingest_state.json')
API_URL = 'http://localhost:8088/ingest'

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {'goals_last_id': 0, 'daily_last_id': 0}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def fetch_new_transcripts(db_path, last_id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Assuming message_id increases; we select where message_id > last_id
    cur.execute('SELECT message_id, date_utc, duration_s, transcript FROM notes WHERE transcribed=1 AND message_id > ? ORDER BY message_id', (last_id,))
    rows = cur.fetchall()
    conn.close()
    notes = []
    max_id = last_id
    for r in rows:
        notes.append({
            'message_id': r['message_id'],
            'date_utc': r['date_utc'],
            'duration_s': r['duration_s'],
            'transcript': r['transcript']
        })
        if r['message_id'] > max_id:
            max_id = r['message_id']
    return notes, max_id

def main():
    state = load_state()
    goals_notes, new_goals_max = fetch_new_transcripts(GOALS_DB, state.get('goals_last_id', 0))
    daily_notes, new_daily_max = fetch_new_transcripts(DAILY_DB, state.get('daily_last_id', 0))
    total_new = len(goals_notes) + len(daily_notes)
    if total_new == 0:
        print('No new transcripts to ingest.')
        return 0
    print(f'Found {len(goals_notes)} new goal notes and {len(daily_notes)} new daily notes')
    documents = []
    for note in goals_notes + daily_notes:
        text = note['transcript'].strip()
        if not text:
            continue
        source = f"voice_note_{'goal' if note['message_id'] < 0 else 'daily'}_{note['message_id']}.md"
        documents.append({
            'text': text,
            'source_file': source
        })
    # Ingest in batches
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
    # Update state
    if goals_notes:
        state['goals_last_id'] = new_goals_max
    if daily_notes:
        state['daily_last_id'] = new_daily_max
    save_state(state)
    print('Incremental ingestion complete.')
    return 0

if __name__ == '__main__':
    sys.exit(main())

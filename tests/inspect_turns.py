import sqlite3

conn = sqlite3.connect("backend/app/finswarm.db")
c = conn.cursor()

c.execute("SELECT turn, speaker, round(sentiment,2), round(conviction,2), factuality_score, cited_source, source_url FROM reliance_master_transcript ORDER BY turn ASC")
rows = c.fetchall()

print(f"=== STORED MASTER 30-TURN DEBATE TRANSCRIPT (Total Turns: {len(rows)}) ===\n")

for r in rows:
    print(f"Turn #{r[0]:2d} | Speaker: {r[1]:32s} | Sentiment: {r[2]:5.2f} | Conviction: {r[3]:4.2f} | Reliability: {r[4]:.2f} | Source: {r[5]}")
    print(f"         URL: {r[6]}\n")

conn.close()

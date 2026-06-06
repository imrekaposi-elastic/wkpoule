import os
import httpx

k = os.environ["ELASTIC_API_KEY"]
h = {"Authorization": f"ApiKey {k}", "Content-Type": "application/json"}
base = "https://o11y.es.ece.kaposi.net:9243"

def count(gte, label):
    q = {
        "size": 0,
        "query": {
            "bool": {
                "filter": [
                    {"term": {"service.name": "wkpoule-frontend"}},
                    {"term": {"agent.name": "rum-js"}},
                    {"range": {"@timestamp": {"gte": gte}}},
                ]
            }
        },
    }
    r = httpx.post(f"{base}/traces-*/_search", headers=h, json=q, verify=False, timeout=30).json()
    total = r["hits"]["total"]
    total = total.get("value", total) if isinstance(total, dict) else total
    print(f"{label}: {total}")

count("2026-06-06T06:00:00Z", "since 06:00 UTC (08:00 CEST)")
count("2026-06-06T04:00:00Z", "since 04:00 UTC (06:00 CEST)")
count("2026-06-06T05:05:00Z", "since 05:05 UTC (07:05 CEST)")

q = {
    "size": 0,
    "query": {
        "bool": {
            "filter": [
                {"term": {"service.name": "wkpoule-frontend"}},
                {"term": {"agent.name": "rum-js"}},
                {"range": {"@timestamp": {"gte": "2026-06-06T04:00:00Z"}}},
            ]
        }
    },
    "aggs": {
        "by_hour": {"date_histogram": {"field": "@timestamp", "fixed_interval": "1h"}},
        "by_ua": {"terms": {"field": "user_agent.original", "size": 8}},
    },
}
r = httpx.post(f"{base}/traces-*/_search", headers=h, json=q, verify=False, timeout=30).json()
print("\nHourly since 06:00 CEST:")
for bkt in r["aggregations"]["by_hour"]["buckets"]:
    print(f"  {bkt['key_as_string']}: {bkt['doc_count']}")
print("\nTop user agents:")
for bkt in r["aggregations"]["by_ua"]["buckets"]:
    print(f"  {bkt['doc_count']}: {bkt['key'][:100]}")

r = httpx.post(
    f"{base}/traces-*/_search",
    headers=h,
    json={
        "size": 1,
        "sort": [{"@timestamp": "desc"}],
        "query": {
            "bool": {
                "filter": [
                    {"term": {"service.name": "wkpoule-frontend"}},
                    {"term": {"agent.name": "rum-js"}},
                ]
            }
        },
    },
    verify=False,
    timeout=30,
).json()
if r["hits"]["hits"]:
    print("\nLatest RUM event:", r["hits"]["hits"][0]["_source"]["@timestamp"])
else:
    print("\nNo RUM events found")

q = {
    "size": 0,
    "query": {
        "bool": {
            "filter": [
                {"term": {"service.name": "wkpoule-frontend"}},
                {"range": {"@timestamp": {"gte": "2026-06-06T04:00:00Z"}}},
            ]
        }
    },
    "aggs": {
        "by_type": {"terms": {"field": "transaction.type", "size": 10, "missing": "no-tx"}},
        "by_event": {"terms": {"field": "processor.event", "size": 10}},
    },
}
r = httpx.post(f"{base}/traces-apm*/_search", headers=h, json=q, verify=False, timeout=30).json()
total = r["hits"]["total"]
total = total.get("value", total) if isinstance(total, dict) else total
print(f"\nAll traces-apm docs since 06:00 CEST: {total}")
print("By transaction.type:", [(x["key"], x["doc_count"]) for x in r["aggregations"]["by_type"]["buckets"]])
print("By processor.event:", [(x["key"], x["doc_count"]) for x in r["aggregations"]["by_event"]["buckets"]])

q = {
    "size": 1,
    "sort": [{"@timestamp": "desc"}],
    "query": {
        "bool": {
            "filter": [
                {"term": {"service.name": "wkpoule-frontend"}},
                {"term": {"transaction.type": "page-load"}},
            ]
        }
    },
}
r = httpx.post(f"{base}/traces-apm*/_search", headers=h, json=q, verify=False, timeout=30).json()
if r["hits"]["hits"]:
    print("\nLast page-load:", r["hits"]["hits"][0]["_source"]["@timestamp"])
else:
    print("\nNo page-load events ever")

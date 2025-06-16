import requests

BASE_URL = "https://api.sekai.best"
REGION = "jp"
EVENTS_JSON_URL = (
    "https://raw.githubusercontent.com/Sekai-World/sekai-master-db-diff/"
    "main/events.json"
)

def fetch_event_list():
    resp = requests.get(EVENTS_JSON_URL)
    resp.raise_for_status()

    data = resp.json()
    if not isinstance(data, list):
        raise ValueError("events.json の中身がリストではありません。")

    event_ids = [e["id"] for e in data if isinstance(e, dict) and "id" in e]
    event_names = [e["name"] for e in data if isinstance(e, dict) and "name" in e]
    print(event_names)
    return event_ids

def fetch_100rank_graph(event_id: int):
    url = f"{BASE_URL}/event/{event_id}/rankings/graph"
    params = {
        "region": REGION,
        "rank": 100,
    }
    print("Requesting URL:", url)
    print("With params:", params)
    resp = requests.get(url, params=params)
    resp.raise_for_status()

    body = resp.json()
    graph_data = body.get("data", {}).get("eventRankings", [])
    return graph_data

if __name__ == "__main__":
    #try:
        event_ids = fetch_event_list()
        if not event_ids:
            print("GitHub 上の events.json からイベント一覧が取得できませんでした。")
            exit(1)
        print(f"取得したイベントID一覧: {event_ids}")
        """
        target_event_id = event_ids[0]
        print(f"→ まず event_id = {target_event_id} を使って 100位グラフを取得します…")
        graph = fetch_100rank_graph(target_event_id)
        if not graph:
            print(f"event_id={target_event_id} の 100位グラフデータが空です。")
        else:
            print(f"event_id={target_event_id} の 100位グラフ取得結果（一部表示）:")
            for entry in graph[:5]:
                ts = entry.get("timestamp")
                rank = entry.get("rank")
                score = entry.get("score")
                print(f"  timestamp={ts}, rank={rank}, score={score}")
    except requests.HTTPError as e:
        print(f"HTTP エラーが発生しました: {e}")
    except Exception as ex:
        print(f"エラー: {ex}")
        """
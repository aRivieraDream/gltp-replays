from typing import Optional, Dict, Any

import json, time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from fastapi_utils.tasks import repeat_every

from maps import get_spreadsheet_maps
from replays import process_unprocessed_replays, get_replay_details, retrieve_replay_data
import jsonutil
from starlette.responses import Response
from starlette.status import HTTP_404_NOT_FOUND

app = FastAPI()

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
STATIC_ROOT = (Path(__file__).parent / "static").resolve()

DATA_DIR = Path("data")
REPLAYS_DIR = DATA_DIR / "replays"
STATS_FILE = DATA_DIR / "replay_stats.json"
URIS_FILE = DATA_DIR / "replay_uris.json"
UNPROCESSED_FILE = DATA_DIR / "unprocessed_replays.json"


@app.on_event("startup")
async def startup():
    # Try to get maps during startup, but don't fail if it times out
    try:
        app.state.maps = await get_spreadsheet_maps()
        print("Successfully loaded maps during startup")
    except Exception as e:
        print(f"Warning: Failed to load maps during startup: {e}")
        print("Application will start with empty maps and retry later")
        app.state.maps = []
    
    DATA_DIR.mkdir(exist_ok=True)
    REPLAYS_DIR.mkdir(exist_ok=True)
    for path, init in [(STATS_FILE, {}), (URIS_FILE, []), (UNPROCESSED_FILE, {})]:
        if not path.exists():
            await jsonutil.write_json(path, init)


@repeat_every(seconds=60, wait_first=True)
async def sync_replays():
    await process_unprocessed_replays(STATS_FILE, UNPROCESSED_FILE, REPLAYS_DIR, app.state.maps)


@repeat_every(seconds=6 * 3600, wait_first=True)
async def refresh_maps():
    try:
        maps = await get_spreadsheet_maps()
        app.state.maps = maps
        print(f"Successfully refreshed maps, loaded {len(maps)} maps")
    except Exception as e:
        print(f"Error refreshing maps: {e}")
        # Keep existing maps if refresh fails
        if not hasattr(app.state, 'maps') or not app.state.maps:
            print("No existing maps available, setting empty list")
            app.state.maps = []


@app.get("/")
async def serve_index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint to verify application status"""
    return {
        "status": "healthy",
        "maps_loaded": len(app.state.maps) if hasattr(app.state, 'maps') else 0,
        "timestamp": time.time()
    }


@app.post("/webhook")
async def github_webhook(request: Request):
    # Verify it's a push event
    event_type = request.headers.get("X-GitHub-Event")
    if event_type != "push":
        raise HTTPException(status_code=400, detail="Not a push event")
    
    # Get the payload
    payload = await request.json()
    
    # Verify it's from the main branch
    ref = payload.get("ref", "")
    if not ref.endswith("/main"):
        raise HTTPException(status_code=400, detail="Not from main branch")
    
    # Write to a file that the host can monitor
    try:
        with open("/app/data/webhook_trigger", "w") as f:
            f.write(str(time.time()))
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger deployment: {str(e)}")


@app.post("/replay")
async def post_replay(payload: dict):
    uuid = payload.get("uuid")
    if not uuid:
        raise HTTPException(400, "Missing 'uuid'")

    # record submission
    uris = await jsonutil.read_json(URIS_FILE)
    uris.append(uuid)
    await jsonutil.write_json(URIS_FILE, uris)

    unproc = await jsonutil.read_json(UNPROCESSED_FILE)
    if uuid not in unproc:
        now = time.time()
        unproc[uuid] = {"first": now, "last": now}
        await jsonutil.write_json(UNPROCESSED_FILE, unproc)

    # try immediate fetch/process
    try:
        replay = await retrieve_replay_data(uuid)
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    if not replay:
        raise HTTPException(404, "Not ready or invalid")

    details = get_replay_details(replay, app.state.maps)
    if not details:
        raise HTTPException(404, "Invalid replay details")

    # save raw replay 
    (REPLAYS_DIR / f"{uuid}.json").write_text(json.dumps(replay))

    # update stats
    stats = await jsonutil.read_json(STATS_FILE)
    stats[uuid] = details
    await jsonutil.write_json(STATS_FILE, stats)

    # remove from unprocessed
    unproc = await jsonutil.read_json(UNPROCESSED_FILE)
    unproc.pop(uuid, None)
    await jsonutil.write_json(UNPROCESSED_FILE, unproc)

    return details


@app.get("/stats")
async def get_stats(
    capping_player_user_id: Optional[str] = Query(None),
    map_id: Optional[str] = Query(None),
    topk: Optional[int] = Query(
        None, ge=1, description="Return top K fastest records per map"
    ),
) -> Dict[str, Any]:
    """
    Fetch stats with optional filters:
      - capping_player_user_id: only include replays by this user
      - map_id: only include replays on this map
      - topk: if set, return up to that many fastest records per map
    """
    stats = await jsonutil.read_json(STATS_FILE)

    # apply capping_player_user_id & map_id filters
    filtered = {
        uid: data
        for uid, data in stats.items()
        if (capping_player_user_id is None
            or data.get("capping_player_user_id") == capping_player_user_id)
        and (map_id is None or data.get("map_id") == map_id)
    }

    if topk is None:
        return filtered

    # group by map_id
    grouped: Dict[str, list[tuple[str, Any]]] = {}
    for uid, data in filtered.items():
        grouped.setdefault(data["map_id"], []).append((uid, data))

    # pick topk by record_time per map
    result: Dict[str, Any] = {}
    for entries in grouped.values():
        top_entries = sorted(
            entries, key=lambda x: x[1].get("record_time", float("inf"))
        )[:topk]
        for uid, data in top_entries:
            result[uid] = data

    return result

@app.get("/GLTP")
@app.get("/GLTP/")
async def redirect_gltp():
    return RedirectResponse(url="/")

@app.get("/{full_path:path}")
async def serve_static_catchall(full_path: str):
    path = (STATIC_ROOT / full_path).resolve()
    if not STATIC_ROOT in path.parents:
        return Response("Forbidden", status_code=403)
    if path.is_file():
        return FileResponse(path)
    return Response("Not Found", status_code=HTTP_404_NOT_FOUND)
# Run
```
docker run -p 8000:8000 \
  -v "$(pwd)/data":/app/data \
  $(docker build -q .)
```

# API Examples

## `POST /replay`: Submit a replay
```
curl -X POST http://localhost:8000/replay \
  -H "Content-Type: application/json" \
  -d '{"uuid":"836a67f6-41dc-49cb-b649-af1a28ce5dec"}'
```

#### Response:
```
{"map_id":"82029","actual_map_id":"82029","preset":null,"map_name":"The Impossible (Portal Edition) 1.0.2","map_author":"Jean Valjean","players":[{"name":"Some Ball 1","user_id":null,"is_red":true},{"name":"MRCOW","user_id":"52d14bd41c0f1b14212793c3","is_red":true},{"name":"Some Ball 3","user_id":null,"is_red":true},{"name":"Some Ball 4","user_id":null,"is_red":true}],"capping_player":"Some Ball 4","capping_player_user_id":null,"record_time":136496,"is_solo":false,"timestamp":1728540169593,"uuid":"836a67f6-41dc-49cb-b649-af1a28ce5dec","caps_to_win":1,"capping_player_quote":"SB NATION, SB LIFE"}
```

#### Side effect:
Saves replay stats item to server


## `GET /stats`: Get all replay stats items
```
curl http://localhost:8000/stats
```

#### Response:
```
{"836a67f6-41dc-49cb-b649-af1a28ce5dec":{"map_id":"82029","actual_map_id":"82029","preset":null,"map_name":"The Impossible (Portal Edition) 1.0.2","map_author":"Jean Valjean","players":[{"name":"Some Ball 1","user_id":null,"is_red":true},{"name":"MRCOW","user_id":"52d14bd41c0f1b14212793c3","is_red":true},{"name":"Some Ball 3","user_id":null,"is_red":true},{"name":"Some Ball 4","user_id":null,"is_red":true}],"capping_player":"Some Ball 4","capping_player_user_id":null,"record_time":136496,"is_solo":false,"timestamp":1728540169593,"uuid":"836a67f6-41dc-49cb-b649-af1a28ce5dec","caps_to_win":1,"capping_player_quote":"SB NATION, SB LIFE"}}
```

### `GET /stats` (Only top 3 records per map)
```
curl "http://localhost:8000/stats?topk=3"
```

### `GET /stats` (filter by User ID)
```
curl "http://localhost:8000/stats?capping_player_user_id=52d14bd41c0f1b14212793c3"
```

### `GET /stats` (filter by Map ID)
```
curl "http://localhost:8000/stats?map_id=82029"
```

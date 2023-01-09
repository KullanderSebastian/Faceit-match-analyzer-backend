from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
import requests
import json


def get_stats_for_game(request, username):
    WIN_WEIGHT = 3
    LOSE_WEIGHT = 1
    KR_WEIGHT = 4

    r = requests.get("https://open.faceit.com/data/v4/players?nickname=" + username, headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + settings.FACEIT_API_KEY
    })

    player_id = r.json()["player_id"]

    r = requests.get("https://api.faceit.com/match/v1/matches/groupByState?userId=" + player_id)

    if "VOTING" in r.json()["payload"]:
        lobby_state = "VOTING"
    if "ONGOING" in r.json()["payload"]:
        lobby_state = "ONGOING"

    match_id = r.json()["payload"][lobby_state][0]["id"]
    players = []
    avatars = []

    for value in r.json()["payload"][lobby_state][0]["teams"]["faction1"]["roster"]:
        players.append(value["id"])
        avatars.append(value["avatar"] if "avatar" in value else "default")

    for value in r.json()["payload"][lobby_state][0]["teams"]["faction2"]["roster"]:
        players.append(value["id"])
        avatars.append(value["avatar"] if "avatar" in value else "default")

    players_stats = {
        "faction1": [],
        "faction2": [],
        "voteable_maps": []
    }

    i = 0
    for id in players:
        r = requests.get("https://api.faceit.com/stats/v1/stats/time/users/" + id + "/games/csgo?page=0&size=200", headers={
            "Content-type": "application/json"
        })

        matches = r.json()
        maps = []
        maps_weighted = {}
        full_weight = 0

        stats = {
            "kills": 0,
            "deaths": 0,
            "hs": 0,
            "games": 0,
            "rounds": 0,
            "wins": 0,
        }

        refined_stats = {}

        elo = 0
        for value in r.json():
            stats["kills"] += int(value["i6"])
            stats["hs"] += int(value["i13"])
            stats["deaths"] += int(value["i8"])
            stats["games"] += 1
            stats["rounds"] += int(value["i12"])
            if value["teamId"] == value["i2"]:
                stats["wins"] += 1

            if elo == 0:
                elo = value["elo"]

        refined_stats["winrate"] = stats["wins"] / stats["games"]
        refined_stats["avg_kills"] = stats["kills"] / stats["games"]
        refined_stats["avg_hs"] = stats["hs"] / stats["kills"]
        refined_stats["kd"] = stats["kills"] / stats["deaths"]
        refined_stats["kr"] = stats["kills"] / stats["rounds"]
        refined_stats["nickname"] = r.json()[0]["nickname"]
        refined_stats["elo"] = elo
        refined_stats["avatar"] = avatars[i]

        for match in matches:
            kr = int(match["i6"]) / int(match["i12"])

            win_weight = WIN_WEIGHT if int(match["i10"]) > 0 else LOSE_WEIGHT
            kr_weight = KR_WEIGHT * kr
            performance_weight = kr_weight

            weight = win_weight + performance_weight

            maps.append({
                "map": match["i1"],
                "wins": match["i10"],
                "matches": 1,
                "kills": match["i6"],
                "rounds": match["i12"],
                "weight": performance_weight + weight,
            })

        for map in maps:
            full_weight += map["weight"]

        for map in maps:
            map["weight"] = (map["weight"] / full_weight) * 100

        refined_stats["maps"] = maps

        if i <= 4:
            players_stats["faction1"].append(refined_stats)
        elif i >= 5:
            players_stats["faction2"].append(refined_stats)
        i = i + 1

    r = requests.get("https://api.faceit.com/match/v2/match/" + match_id, headers={
        "Content-Type": "applicaton/json"
    })

    for mapName in r.json()["payload"]["matchCustom"]["tree"]["map"]["values"]["value"]:
        players_stats["voteable_maps"].append(mapName["guid"])

    return HttpResponse(json.dumps(players_stats))

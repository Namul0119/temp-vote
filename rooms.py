rooms = {}

def create_room(room_code, target_count):
    rooms[room_code] = {
        "target_count": target_count,
        "votes": []
    }

def add_vote(room_code, vote):
    rooms[room_code]["votes"].append(vote)

def is_room_complete(room_code):
    return len(rooms[room_code]["votes"]) >= rooms[room_code]["target_count"]

def get_room_votes(room_code):
    return rooms[room_code]["votes"]

def get_room_status(room_code):
    room = rooms[room_code]
    return len(room["votes"]), room["target_count"]
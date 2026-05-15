def is_duplicate_name(name, votes):

    existing_names = [
        user.get("name", "").strip()
        for user in votes
    ]

    return name in existing_names
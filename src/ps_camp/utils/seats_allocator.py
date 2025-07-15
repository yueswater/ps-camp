def compute_seats(party_votes: dict[str, int], total_seats: int = 34, threshold: float = 0.05) -> dict[str, int]:
    """
    Calculate seat allocation based on Hale-Niemeer maximum balance method and 5% threshold
    Args:
        party_votes: Party ID corresponding votes
        Total_seats: Total seats available (preset 34)
        threshold: Ticket threshold (preset 5%)
    Returns:
        dict[str, int]: Each party wins seats
    """
    total_votes = sum(party_votes.values())
    qualified = {
        pid: votes for pid, votes in party_votes.items()
        if votes / total_votes >= threshold
    }

    quotas = {pid: votes / total_votes * total_seats for pid, votes in qualified.items()}
    seats = {pid: int(quotas[pid]) for pid in quotas}
    remaining = total_seats - sum(seats.values())

    remainders = sorted(
        ((pid, quotas[pid] - seats[pid]) for pid in quotas),
        key=lambda x: (-x[1], -party_votes[x[0]])  # tie-breaker: more raw votes
    )

    for i in range(remaining):
        if i >= len(remainders):
            break  # not enough political parties to allocate
        pid, _ = remainders[i]
        seats[pid] += 1

    return seats

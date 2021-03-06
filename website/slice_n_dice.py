from .models import Player


def make_teams(player_list, fairness_value, team_amount=2):

    all_combinations = sorted_k_partitions(player_list, team_amount)
    # this yields all combinations, so a list of [1,2,3,4] partitioned in two partitions gives us:
    # [(1,), (2, 3, 4)]
    # [(2,), (1, 3, 4)]
    # [(3,), (1, 2, 4)]
    # [(4,), (1, 2, 3)]
    # [(1, 2), (3, 4)]
    # [(1, 3), (2, 4)]
    # [(1, 4), (2, 3)]
    # So now we filter out all the groups with a member difference > 2


    valid_indexes = []
    for i in range(len(all_combinations)):
        if len(all_combinations[i][0]) >= int((len(player_list)/team_amount)):
            valid_indexes.append(i)

    # each skill-diff corresponds to a valid_indexes with the same index
    skill_diff = []
    # look up how many points difference each of them has at valid indexes
    for index in valid_indexes:
        wr_combination = []
        idx_counter = 0
        print(all_combinations[index])
        for team in all_combinations[index]:
            wr_combination.append(0)
            for member in team:
                player = Player.query.filter_by(name=member).first()
                if player.played_matches < 5:
                    wr_combination[idx_counter] += 50  # 50% win-rate with low matches
                else:
                    wr_combination[idx_counter] += int((player.won_matches / player.played_matches) * 100)
            wr_combination[idx_counter] /= len(team)  # mean win-rate of current team
            idx_counter += 1

        # calculate difference between team-win-rates here
        diffs = []
        for i, e in enumerate(wr_combination):
            for j, f in enumerate(wr_combination):
                if i != j:
                    diffs.append(abs(e - f))
        skill_diff.append(sum(diffs)/len(diffs))

    print(skill_diff)
    # also return win-rates!
    most_balanced_team = min(skill_diff)
    most_balanced_team_index = skill_diff.index(most_balanced_team)

    return all_combinations[valid_indexes[most_balanced_team_index]][0], \
           all_combinations[valid_indexes[most_balanced_team_index]][1]


# Taken from SO: https://stackoverflow.com/a/39199937
def sorted_k_partitions(seq, k):
    """Returns a list of all unique k-partitions of `seq`.

    Each partition is a list of parts, and each part is a tuple.

    The parts in each individual partition will be sorted in shortlex
    order (i.e., by length first, then lexicographically).

    The overall list of partitions will then be sorted by the length
    of their first part, the length of their second part, ...,
    the length of their last part, and then lexicographically.
    """
    n = len(seq)
    groups = []  # a list of lists, currently empty

    def generate_partitions(i):
        if i >= n:
            yield list(map(tuple, groups))
        else:
            if n - i > k - len(groups):
                for group in groups:
                    group.append(seq[i])
                    yield from generate_partitions(i + 1)
                    group.pop()

            if len(groups) < k:
                groups.append([seq[i]])
                yield from generate_partitions(i + 1)
                groups.pop()

    result = generate_partitions(0)

    # Sort the parts in each partition in shortlex order
    result = [sorted(ps, key=lambda p: (len(p), p)) for ps in result]
    # Sort partitions by the length of each part, then lexicographically.
    result = sorted(result, key=lambda ps: (*map(len, ps), ps))

    return result

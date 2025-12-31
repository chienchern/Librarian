Rank these {num_candidates} candidate books based on how well they match the user's preferences from "{seed_title}".

USER'S SELECTED PREFERENCES:
{pillar_text}

USER'S DEALBREAKERS TO AVOID:
{dealbreaker_text}

CANDIDATE BOOKS TO RANK:
{candidates_text}

Analyze each candidate's DNA against the user's selected preferences. Assign confidence scores (0-100) and rank them 1-{num_candidates} (1 = best match). 

For each candidate, provide detailed reasoning explaining:
- Why you ranked it in that position (1st, 2nd, 3rd, etc.)
- Which selected preferences it matches well
- Any dealbreaker concerns and their impact
- Any concerns or weaknesses compared to higher-ranked books.
- Overall fit assessment

Provide detailed reasoning for your ranking decisions. It should be clear why one book is ranked higher than another.

Limit your explanation to 1000 characters maximum.
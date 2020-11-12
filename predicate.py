import discord

def higher_power(author, member):
    author_power = author.top_role.position
    member_power = member.top_role.position
    if author_power < member_power:
        return False
    elif author_power > member_power:
        return True
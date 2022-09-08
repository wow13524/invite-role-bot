from modubot import PropertyDict

class HelpConfig(PropertyDict):
    invite_url: str = ""
    github_url: str = ""
    privacy_policy_url: str = ""
    donate_url: str = ""

class InviteRoleBotConfig(PropertyDict):
    help_command: HelpConfig = HelpConfig([],{},"")
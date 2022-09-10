from modubot import PropertyDict

class HelpConfig(PropertyDict):
    invite_url: str = "https://top.gg/bot/480240313525600267"
    github_url: str = "https://github.com/wow13524/invite-role-bot"
    privacy_policy_url: str = "https://gist.github.com/wow13524/63054dd96bd4641104d0924e85f0501e"
    donate_url: str = "https://www.paypal.me/wow13524"

class InviteRoleBotConfig(PropertyDict):
    help_command: HelpConfig = HelpConfig([],{},"")
from typing import Final

VERSION: Final[str] = "v0.1.0"
HELP_SELECT_RAW: Final[dict[str, str]] = {
    "/도움말": "도움말을 출력합니다.",
    "/레포": "깃허브 레포지토리 정보를 출력합니다.",
    "/봇": "봇의 정보를 출력합니다.",
    "/연동": "깃허브 계정을 연동합니다.",
    "/연동해제": "깃허브 계정 연동을 해제합니다.",
    "/유저": "깃허브 유저 정보를 출력합니다.",
    "/핑": "봇의 핑을 출력합니다."
}
HELP_EMBED_RAW: Final[dict[str, str]] = {
    "/도움말": "도움말을 출력합니다.",
    "/레포 `[소속]` `[이름]`": "깃허브 `[소속]`/`[이름]` 레포지토리 정보를 출력합니다.",
    "/봇": "봇의 정보를 출력합니다.",
    "/연동": "토큰을 사용해 깃허브 계정을 연동합니다.",
    "/연동해제": "깃허브 계정 연동을 해제합니다.",
    "/유저 `[아이디]`": "깃허브 `[아이디]` 유저 정보를 출력합니다.",
    "/핑": "봇의 핑을 출력합니다."
}
OPTION_TYPES: Final[dict[int, str]] = {
    1: "SUB_COMMAND",
    2: "SUB_COMMAND_GROUP",
    3: "STRING",
    4: "INTEGER",
    5: "BOOLEAN",
    6: "USER",
    7: "CHANNEL",
    8: "ROLE",
    9: "MENTIONABLE",
    10: "NUMBER",
    11: "ATTACHMENT"
}

"""Roles and the permission table of ``docs/project/app_design_v2.md`` section 4."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    PRESENTER = "presenter"
    EDITOR = "editor"
    VIEWER = "viewer"


class Permission(StrEnum):
    CHAT = "chat"
    SWITCH_MODE = "switch_mode"  # use A0 (no defence); everyone may use BrokerGuard v3
    VIEW_OUTBOX = "view_outbox"
    SEND_REAL_EMAIL = "send_real_email"
    EDIT_SOURCES = "edit_sources"
    VIEW_ALL_CONVERSATIONS = "view_all_conversations"
    MANAGE = "manage"  # users, invites, allowlist, settings, audit


ROLE_LABELS_VI = {
    Role.ADMIN: "Quản trị",
    Role.PRESENTER: "Người trình diễn",
    Role.EDITOR: "Biên soạn",
    Role.VIEWER: "Người xem",
}

_ALL = frozenset(Permission)
PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: _ALL,
    Role.PRESENTER: frozenset({Permission.CHAT, Permission.SWITCH_MODE, Permission.VIEW_OUTBOX,
                               Permission.SEND_REAL_EMAIL}),
    Role.EDITOR: frozenset({Permission.CHAT, Permission.SWITCH_MODE, Permission.VIEW_OUTBOX,
                            Permission.EDIT_SOURCES}),
    Role.VIEWER: frozenset({Permission.CHAT, Permission.VIEW_OUTBOX}),
}


def allowed(role: Role, permission: Permission) -> bool:
    return permission in PERMISSIONS[role]

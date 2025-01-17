# Copyright (C) 2019 The Raphielscape Company LLC.
# Copyright (C) 2018 - 2019 MrYacha
#
# This file is part of SophieBot.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

import re
import time
from importlib import import_module

from aiogram import types
from aiogram.dispatcher.handler import SkipHandler
from telethon import events

from sophie_bot import BOT_USERNAME, DEBUG_MODE, tbot, dp, logger
from sophie_bot.config import get_config_key
from sophie_bot.modules.helper_func.error import report_error
from sophie_bot.modules.helper_func.flood import prevent_flooding

import_module("sophie_bot.modules.helper_func.bount_filter")

ALLOW_F_COMMANDS = get_config_key("allow_forwards_commands")
ALLOW_COMMANDS_FROM_EXC = get_config_key("allow_commands_with_!")
BLOCK_GBANNED_USERS = get_config_key("block_gbanned_users")
RATE_LIMIT = get_config_key("rate_limit")

REGISTRED_COMMANDS = []


def register(cmds=None, f=None, allow_edited=True, allow_kwargs=False, *args, **kwargs):

    if cmds and type(cmds) == str:
        cmds = [cmds]

    register_kwargs = {}

    if cmds:
        if ALLOW_COMMANDS_FROM_EXC:
            regex = r'^[/!]'
        else:
            regex = r'^/'

        if 'not_gbanned' not in kwargs and BLOCK_GBANNED_USERS:
            kwargs['not_gbanned'] = True
        if 'not_forwarded' not in kwargs and ALLOW_F_COMMANDS is False:
            kwargs['not_forwarded'] = True

        for idx, cmd in enumerate(cmds):
            REGISTRED_COMMANDS.append(cmd)
            regex += r"(?i:{0}|{0}@{1})".format(cmd, BOT_USERNAME)

            if 'disable_args' in kwargs:
                del kwargs['disable_args']
                regex += "$"
            else:
                regex += "(?: |$)"

            if not idx == len(cmds) - 1:
                regex += "|"

        register_kwargs['regexp'] = regex

    elif f == 'welcome':
        register_kwargs['content_types'] = types.ContentTypes.NEW_CHAT_MEMBERS

    register_kwargs.update(kwargs)

    def decorator(func):
        async def new_func(message, *args, **def_kwargs):

            if RATE_LIMIT and await prevent_flooding(message, message.text) is False:
                return

            if allow_kwargs is False:
                def_kwargs = dict()
            if DEBUG_MODE:
                logger.debug('[*] Starting {}.'.format(func.__name__))
                start = time.time()
                await func(message, *args, **def_kwargs)
                logger.debug('[*] {} Time: {} sec.'.format(func.__name__, time.time() - start))
            else:
                await func(message, *args, **def_kwargs)
            raise SkipHandler()

        dp.register_message_handler(new_func, *args, **register_kwargs)
        if allow_edited is True:
            dp.register_edited_message_handler(new_func, *args, **register_kwargs)

    return decorator


def t_command(command, arg="", word_arg="", additional="", **kwargs):
    REGISTRED_COMMANDS.append(command)

    def decorator(func):

        if 'forwards' not in kwargs:
            kwargs['forwards'] = ALLOW_F_COMMANDS


        P = '[/!]' if ALLOW_COMMANDS_FROM_EXC else '/'

        if arg is True:
            cmd = "^{P}(?i:{0}|{0}@{1})(?: |$)(.*){2}".format(command, BOT_USERNAME, additional,
                                                              P=P)
        elif word_arg is True:
            cmd = "^{P}(?i:{0}|{0}@{1})(?: |$)(\S*){2}".format(command, BOT_USERNAME, additional,
                                                               P=P)
        else:
            cmd = "^{P}(?i:{0}|{0}@{1})$".format(command, BOT_USERNAME, additional, P=P)

        async def new_func(event, *args, **def_kwargs):
            try:
                await func(event, *args, **def_kwargs)
            except Exception:
                await report_error(event, telethon=True)

        tbot.add_event_handler(new_func, events.NewMessage(incoming=True, pattern=cmd, **kwargs))
        tbot.add_event_handler(new_func, events.MessageEdited(incoming=True, pattern=cmd, **kwargs))
    return decorator


def callback_query_deprecated(data, do_compile=True):
    def decorator(func):
        if do_compile is True:
            tbot.add_event_handler(func, events.CallbackQuery(data=re.compile(data)))
        else:
            tbot.add_event_handler(func, events.CallbackQuery(data=data))
    return decorator


def insurgent():
    def decorator(func):
        tbot.add_event_handler(func, events.NewMessage(incoming=True))
        tbot.add_event_handler(func, events.MessageEdited(incoming=True))
    return decorator


def strict_command(cmd):
    def decorator(func):
        tbot.add_event_handler(func, events.NewMessage(incoming=True, pattern=cmd))
        tbot.add_event_handler(func, events.MessageEdited(incoming=True, pattern=cmd))
    return decorator


def chat_action():
    def decorator(func):
        tbot.add_event_handler(func, events.ChatAction)
    return decorator

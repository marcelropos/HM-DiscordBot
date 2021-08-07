from __future__ import annotations

import importlib
from importlib.util import find_spec
from os import listdir
from os.path import isfile, join

from discord.ext.commands import Context

from core.error.handler.base_handler import BaseHandler

path = "./core/error/handler/"
handlers = [f for f in listdir(path) if isfile(join(path, f))]

for handler in handlers:
    handler = handler.rstrip(".py")
    spec = importlib.util.spec_from_file_location(handler, path + handler + ".py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


async def error_handler(ctx: Context, error: Exception):
    await BaseHandler.handlers(error, ctx).handle()

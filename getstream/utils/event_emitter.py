import asyncio
import logging
from pyee.asyncio import AsyncIOEventEmitter
import inspect


class StreamAsyncIOEventEmitter(AsyncIOEventEmitter):
    """
    AsyncIOEventEmitter with wildcard pattern support for event names.

    Supports patterns like:
    - '*' - matches all events
    - 'prefix.*' - matches events starting with 'prefix.' (single level)
    - 'prefix.**' - matches events starting with 'prefix.' (multiple levels)
    """

    def __init__(self):
        super().__init__()
        self._wildcard_listeners = {}

    def emit(self, event, *args, **kwargs):
        """Override emit to handle wildcard patterns without requiring callers to await.

        This mirrors the interface of ``pyee.AsyncIOEventEmitter.emit`` (i.e. it is
        synchronous) while still supporting asynchronous wildcard listeners.
        Any coroutine wildcard listeners are scheduled on the current loop using
        ``asyncio.create_task`` and errors are routed through the loop's
        exception handler (falling back to logging if none is available).
        """

        # First, attempt to emit the event via the parent implementation.  We
        # need to *safely* handle the special ``error`` event which pyee will
        # raise as a ``PyeeError`` if no explicit ``'error'`` listeners are
        # registered.  We want wildcard listeners (e.g. "*" or "error.*") to
        # count here, so we call the superclass in a try / except block and
        # ignore the error *iff* we have at least one matching wildcard
        # listener.

        try:
            result = super().emit(event, *args, **kwargs)
        except Exception as pyee_exc:
            # Only suppress for the special case described above.
            from pyee.base import PyeeError

            if isinstance(pyee_exc, PyeeError) and event == "error":
                # Always swallow; treat it as normal when using wildcard-only handling.
                logging.getLogger(__name__).debug(
                    "Suppressed PyeeError for unhandled 'error' event"
                )
                result = False
            else:
                # Not the special case → re-raise.
                raise

        loop = self._loop or asyncio.get_event_loop()

        for pattern, listeners in list(self._wildcard_listeners.items()):
            if self._matches_pattern(event, pattern):
                for listener in list(listeners):
                    # Decide whether listener wants the event name.  We use the
                    # heuristic from before: if the listener can accept one
                    # more positional argument than provided (or uses *args),
                    # we prepended the event name; otherwise we forward the
                    # original args unchanged.
                    sig = inspect.signature(listener)
                    positional = [
                        p
                        for p in sig.parameters.values()
                        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                    ]
                    wants_event = len(positional) > len(args) or any(
                        p.kind == p.VAR_POSITIONAL for p in sig.parameters.values()
                    )
                    call_args = (event, *args) if wants_event else args

                    if asyncio.iscoroutinefunction(listener):
                        task = loop.create_task(listener(*call_args, **kwargs))
                        task.add_done_callback(self._handle_task_result)
                    else:
                        try:
                            listener(*call_args, **kwargs)
                        except Exception as exc:
                            self._report_listener_error(loop, exc, event, args, kwargs)

        return result

    def on_wildcard(self, pattern, listener):
        """Register a wildcard event listener"""
        if pattern not in self._wildcard_listeners:
            self._wildcard_listeners[pattern] = []
        self._wildcard_listeners[pattern].append(listener)
        return self

    def remove_wildcard_listener(self, pattern, listener):
        """Remove a specific wildcard listener"""
        if pattern in self._wildcard_listeners:
            try:
                self._wildcard_listeners[pattern].remove(listener)
                if not self._wildcard_listeners[pattern]:
                    del self._wildcard_listeners[pattern]
            except ValueError:
                pass
        return self

    def remove_all_wildcard_listeners(self, pattern=None):
        """Remove all wildcard listeners for a pattern, or all if no pattern specified"""
        if pattern is None:
            self._wildcard_listeners.clear()
        elif pattern in self._wildcard_listeners:
            del self._wildcard_listeners[pattern]
        return self

    def wildcard_listeners(self, pattern=None):
        """Get wildcard listeners for a pattern, or all if no pattern specified"""
        if pattern is None:
            return dict(self._wildcard_listeners)
        return self._wildcard_listeners.get(pattern, []).copy()

    def _matches_pattern(self, event, pattern):
        """Check if an event matches a wildcard pattern"""
        if pattern == "*":
            return True
        elif pattern.endswith("**"):
            # Match multiple levels: 'api.**' matches 'api.user.login'
            prefix = pattern[:-2]
            return event.startswith(prefix)
        elif pattern.endswith("*"):
            # Match single level: 'api.*' matches 'api.user' but not 'api.user.login'
            prefix = pattern[:-1]
            remainder = event[len(prefix) :] if event.startswith(prefix) else ""
            return event.startswith(prefix) and "." not in remainder
        else:
            return event == pattern

    @staticmethod
    def _report_listener_error(loop, exc, event, args, kwargs):
        """Report an exception raised by a wildcard listener.

        Prefer the event loop's exception handler if available; otherwise fall
        back to logging so that the error is not swallowed silently.
        """
        if loop and hasattr(loop, "call_exception_handler"):
            loop.call_exception_handler(
                {
                    "message": "Exception in wildcard event handler",
                    "exception": exc,
                    "event": event,
                    "args": args,
                    "kwargs": kwargs,
                }
            )
        else:
            logging.getLogger(__name__).error(
                "Exception in wildcard event handler: %s", exc, exc_info=exc
            )

    @staticmethod
    def _handle_task_result(task: asyncio.Task):
        """Callback for wildcard listener tasks to surface exceptions."""
        if task.cancelled():
            return
        exc = task.exception()
        if exc:
            logging.getLogger(__name__).error(
                "Exception in async wildcard listener: %s", exc, exc_info=exc
            )

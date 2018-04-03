import sublime
import sublime_plugin
import re
from threading import Timer

def debounce(wait):
    """ Decorator that will postpone a functions
        execution until after wait seconds
        have elapsed since the last time it was invoked. """
    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                fn(*args, **kwargs)
            try:
                debounced.t.cancel()
            except(AttributeError):
                pass
            debounced.t = Timer(wait, call_it)
            debounced.t.start()
        return debounced
    return decorator

phantom_name = 'move_count'

class CountMovesCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        view.erase_phantoms(phantom_name)
        pattern = re.compile("([URFDLB]w?['2]?)")
        html = '<div style="margin-left: 10; color: #7f7c6a; font-style: italic;">({})</div>'
        region = sublime.Region(0, view.size())
        lines = view.lines(region)
        for line in lines:
            text = view.substr(line)
            text = text[:text.index('//')] if '//' in text else text
            text = text[:text.index('#')] if '#' in text else text
            text = text.strip()
            count = len(re.findall(pattern, text))
            if count > 0:
                moves = ('{} move' if count == 1 else '{} moves').format(count)
                view.add_phantom(phantom_name, sublime.Region(line.end(), line.end()), html.format(moves), sublime.LAYOUT_INLINE)

class FewestMovesEventListener(sublime_plugin.EventListener):
    def on_modified(self, view):
        view.erase_phantoms(phantom_name)
        self.calc_moves(view)
    @debounce(.5)
    def calc_moves(self, view):
        if 'source.fm' in view.scope_name(0):
            view.run_command('count_moves')


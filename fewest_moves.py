import sublime
import sublime_plugin
import re
import subprocess as sp
from platform import system
from json import loads
from threading import Timer, Thread
from .move_transformer import normalize

phantom_name_line_end = 'line_move_count'
phantom_name_block = 'total_move_count'

startupinfo = None

if 'windows' in system().lower():
    startupinfo = sp.STARTUPINFO()
    startupinfo.dwFlags |= sp.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = sp.SW_HIDE

def is_fewest_moves(view):
    return 'source.fm' in view.scope_name(0)

def remove_comments(text):
    comment_pattern = re.compile(r'(?://|#).*(?=\n|$)')
    text = re.sub(comment_pattern, '', text)
    return text

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

def get_scramble(view):
    firstLine = view.line(sublime.Region(0, 0))
    scramble = view.substr(firstLine)
    scramble = remove_comments(scramble)
    scramble = normalize(scramble)
    return scramble

def get_skeleton(view):
    sel = view.sel()
    selection = sel[0].begin()
    expanded = view.expand_by_class(selection, sublime.CLASS_EMPTY_LINE)
    skeleton = view.substr(expanded)
    skeleton = remove_comments(skeleton)
    skeleton = normalize(skeleton)
    return skeleton

class CallInsertionFinder(Thread):
    def __init__(self, command, input_str, timeout, callback):
        self.command = command
        self.input_str = input_str
        self.timeout = timeout
        self.callback = callback
        Thread.__init__(self)
    def run(self):
        result = None
        error = None
        try:
            p = sp.Popen(self.command, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, startupinfo=startupinfo)
            result, error = p.communicate(self.input_str.encode(), self.timeout)
            result = result.decode()
            error = error.decode()
        except OSError as e:
            error = e.strerror
        except sp.TimeoutExpired as e:
            p.kill()
            error = 'Timeout of {} seconds has expired.'.format(e.timeout)
        except:
            error = 'Unknown error'
        self.callback(result, error)

class CountMovesCommand(sublime_plugin.TextCommand):

    HTML_TEMPLATE = """
    <body>
        <style>
            html, body {{
                background-color: transparent;
                color: {foreground};
                font-style: {font_style};
                margin: 0;
                padding: 0;
            }}
            body {{
                margin-left: {padding};
            }}
            span {{
                color: color({foreground} blend(var(--foreground) 90%));
                text-decoration: none;
            }}
        </style>
        <span>{text}</span>
    </body>
    """

    def run(self, edit):
        view = self.view
        view.erase_phantoms(phantom_name_line_end)
        view.erase_phantoms(phantom_name_block)
        pattern = re.compile("([URFDLB]w?['2]?)")
        region = sublime.Region(0, view.size())
        lines = view.lines(region)
        lineNumber = 0
        total = 0
        previousLine = None
        for line in lines:
            lineNumber += 1
            text = view.substr(line)
            text = remove_comments(text)
            count = len(re.findall(pattern, text))
            if count > 0:
                moves = ('({} move)' if count == 1 else '({} moves)').format(count)
                view.add_phantom(phantom_name_line_end, sublime.Region(line.end(), line.end()), self.HTML_TEMPLATE.format(foreground='#7f7c6a', font_style='italic', padding=20, text=moves), sublime.LAYOUT_INLINE)
            total += count
            if text == '':
                if lineNumber > 2 and total > 0:
                    moves = ('(total: {} move)' if total == 1 else '(total: {} moves)').format(total)
                    view.add_phantom(phantom_name_block, previousLine, self.HTML_TEMPLATE.format(foreground='#7f7c6a', font_style='italic', padding=0, text=moves), sublime.LAYOUT_BLOCK)
                total = 0
            previousLine = line
        if lineNumber > 2 and total > 0:
            moves = ('(total: {} move)' if total == 1 else '(total: {} moves)').format(total)
            view.add_phantom(phantom_name_block, previousLine, self.HTML_TEMPLATE.format(foreground='#7f7c6a', font_style='italic', padding=0, text=moves), sublime.LAYOUT_BLOCK)
        total = 0
    def is_enabled(self):
        return is_fewest_moves(self.view)

class ShowSolutionCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        self.view.insert(edit, 0, text)
        self.view.set_read_only(True)

class FindInsertionCommand(sublime_plugin.TextCommand):
    running = False
    insertion_finder = 'insertionfinder'

    @property
    def check_cycles(self):
        return [self.insertion_finder] + ['-v', '--json']

    @property
    def find_insertion(self):
        return [self.insertion_finder] + ['-s', '--all-algs']

    def run(self, edit):
        view = self.view
        settings = view.settings()
        scramble = get_scramble(view)
        skeleton = get_skeleton(view)
        input_str = '\n'.join([scramble, skeleton])
        self.insertion_finder = settings.get('insertion_finder', self.insertion_finder)
        try:
            p = sp.Popen(self.check_cycles, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, startupinfo=startupinfo)
        except OSError as e:
            sublime.error_message(e.strerror)
            return
        except:
            sublime.error_message('Some error occurred')
            return
        result, error = p.communicate(input_str.encode())
        if error:
            sublime.error_message(error.decode())
            return
        result = result.decode()
        result = loads(result)
        total_cycles = result['corner_cycles'] + result['edge_cycles'] + result['center_cycles']
        if result['parity']:
            total_cycles += 1
        max_cycles = settings.get('max_cycles', 4)
        if max_cycles != 0 and total_cycles > max_cycles:
            sublime.error_message('Too many cycles: {}'.format(total_cycles))
            return
        command = self.find_insertion[:]
        algs_dir = settings.get('insertion_finder_algs_dir', False)
        if algs_dir is not False:
            command += ['--algs-dir', algs_dir]
        max_threads = settings.get('max_threads', 2)
        command += ['-j' + (str(max_threads) if max_threads != 0 else '')]
        timeout = settings.get('insertion_finder_timeout', 300)
        t = CallInsertionFinder(command, input_str, timeout, self.handle_result)
        self.running = True
        self.show_running(0, 1)
        t.start()

    def show_running(self, i, dir):
        before = i % 8
        after = 7 - before
        dir = -1 if not after else dir
        dir = 1 if not before else dir
        i += dir
        status_key = 'insertion_finder'
        self.view.set_status(status_key, 'Finding insertions [{}={}]'.format(' ' * before, ' ' * after))
        if self.running:
            sublime.set_timeout_async(lambda: self.show_running(i, dir), 100)
        else:
            self.view.erase_status(status_key)

    def handle_result(self, result, error):
        self.running = False
        if error:
            sublime.error_message(error)
            return
        resultView = sublime.active_window().new_file()
        resultView.set_scratch(True)
        resultView.run_command('show_solution', {"text": result})

    def is_enabled(self):
        return is_fewest_moves(self.view)

class FewestMovesEventListener(sublime_plugin.EventListener):
    def on_activated_async(self, view):
        self.run_plugin(view)
    def on_load_async(self, view):
        self.run_plugin(view)
    def on_modified_async(self, view):
        view.erase_phantoms(phantom_name_line_end)
        self.run_plugin(view)
    @debounce(1)
    def run_plugin(self, view):
        if is_fewest_moves(view):
            view.run_command('count_moves')
            view.run_command('draw_scramble')

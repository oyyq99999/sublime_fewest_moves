import sublime
import sublime_plugin
import re
from subprocess import Popen, PIPE, TimeoutExpired
from json import loads
from threading import Timer, Thread
from .move_transformer import normalize

phantom_name = 'move_count'

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
            p = Popen(self.command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            result, error = p.communicate(self.input_str.encode(), self.timeout)
            result = result.decode()
            error = error.decode()
        except OSError as e:
            error = e.strerror
        except TimeoutExpired as e:
            p.kill()
            error = 'Timeout of {} seconds has expired.'.format(e.timeout)
        except:
            error = 'Unknown error'
        self.callback(result, error)

class CountMovesCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        view.erase_phantoms(phantom_name)
        pattern = re.compile("([URFDLB]w?['2]?)")
        htmlLineEnd = '<div style="margin-left: 10; color: #7f7c6a; font-style: italic;">({})</div>'
        htmlBlock = '<div style="color: #7f7c6a; font-style: italic;">({})</div>'
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
                moves = ('{} move' if count == 1 else '{} moves').format(count)
                view.add_phantom(phantom_name, sublime.Region(line.end(), line.end()), htmlLineEnd.format(moves), sublime.LAYOUT_INLINE)
            total += count
            if text == '':
                if lineNumber > 2 and total > 0:
                    moves = ('total: {} move' if total == 1 else 'total: {} moves').format(total)
                    # view.add_phantom(phantom_name, previousLine, htmlBlock.format(moves), sublime.LAYOUT_BLOCK)
                total = 0
            previousLine = line
        if lineNumber > 2 and total > 0:
            moves = ('total: {} move' if total == 1 else 'total: {} moves').format(total)
            # view.add_phantom(phantom_name, previousLine, htmlBlock.format(moves), sublime.LAYOUT_BLOCK)
        total = 0
    def is_enabled(self):
        return 'source.fm' in self.view.scope_name(0)

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
        return [self.insertion_finder] + ['-s', '-t']

    corner_3cycle = ['-a', '3CP-normal']
    edge_3cycle = ['-a', '3EP']
    parity_algs = ['-a', '2C2E']

    def run(self, edit):
        view = self.view
        settings = view.settings()
        scramble = get_scramble(view)
        skeleton = get_skeleton(view)
        input_str = '\n'.join([scramble, skeleton])
        self.insertion_finder = settings.get('insertion_finder', self.insertion_finder)
        try:
            p = Popen(self.check_cycles, stdin=PIPE, stdout=PIPE, stderr=PIPE)
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
        total_cycles = result['corner_cycle_num'] + result['edge_cycle_num']
        max_cycles = view.settings().get('max_cycles', 4)
        if result['parity']:
            total_cycles += 1
        if total_cycles > max_cycles:
            sublime.error_message('Too many cycles: {}'.format(total_cycles))
            return
        command = self.find_insertion[:]
        if result['corner_cycle_num'] > 0:
            command += self.corner_3cycle
        if result['edge_cycle_num'] > 0:
            command += self.edge_3cycle
        if result['parity']:
            command += self.parity_algs
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

class FewestMovesEventListener(sublime_plugin.EventListener):
    def on_activated_async(self, view):
        self.calc_moves(view)
    def on_load_async(self, view):
        self.calc_moves(view)
    def on_modified_async(self, view):
        self.calc_moves(view)
    def calc_moves(self, view):
        view.run_command('count_moves')


import sublime
import sublime_plugin
import random
from .facelet_cube import FaceletCube
from .fewest_moves import is_fewest_moves, get_scramble

class DrawScrambleCommand(sublime_plugin.TextCommand):

    HTML_TEMPLATE = """
    <body>
        <style>
            * {{
                background-color: transparent;
                margin: 0;
                padding: 0;
            }}
            body {{
                background-color: transparent;
            }}
            div {{
                display: block;
            }}
            .scramble {{
                padding-bottom: 3px;
                padding-left: 1px;
                padding-right: 1px;
            }}
            .row {{
                position: relative;
                height: 30px;
                line-height: 1em;
                padding-top: -9px;
                padding-bottom: -2px;
                font-size: 0;
            }}
            .cell {{
                padding-top: -8px;
                padding-bottom: -4px;
                font-size: 30px;
                border: 1px solid black;
            }}
            .gap {{
                color: transparent;
                border: 1px solid transparent;
            }}
            .u {{
                color: {colorU};
            }}
            .f {{
                color: {colorF};
            }}
            .l {{
                color: {colorL};
            }}
            .r {{
                color: {colorR};
            }}
            .b {{
                color: {colorB};
            }}
            .d {{
                color: {colorD};
            }}
        </style>
        <div class="scramble">{rows}</div>
    </body>
    """

    def run(self, edit):
        view = self.view
        settings = view.settings()
        colorU = settings.get('u_face', '#ffffff')
        colorR = settings.get('r_face', '#ff0000')
        colorF = settings.get('f_face', '#00ff00')
        colorD = settings.get('d_face', '#ffff00')
        colorL = settings.get('l_face', '#ff8000')
        colorB = settings.get('b_face', '#0000ff')
        view.erase_phantoms('scramble_state')
        firstLine = view.line(sublime.Region(0, 0))
        scramble = get_scramble(view)
        if scramble == '':
            return

        cube = FaceletCube(scramble)

        FACELETS = 'urfdlb'
        rowTemplate = '<div class="row">{}</div>'
        spanTemplate = '<span class="cell {}">■</span>'
        rows = ''
        for row in range(9):
            spans = ''
            for col in range(12):
                if (row < 3 or row >= 6) and (col < 3 or col >= 6):
                    spans += spanTemplate.format('gap')
                else:
                    if row < 3:
                        idx = cube.state[0][row * 3 + col - 3]
                        spans += spanTemplate.format(FACELETS[idx])
                        continue
                    if row >= 6:
                        idx = cube.state[3][(row - 6) * 3 + col - 3]
                        spans += spanTemplate.format(FACELETS[idx])
                        continue
                    if col < 3:
                        idx = cube.state[4][(row - 3) * 3 + col]
                        spans += spanTemplate.format(FACELETS[idx])
                        continue
                    if col < 6:
                        idx = cube.state[2][(row - 3) * 3 + col - 3]
                        spans += spanTemplate.format(FACELETS[idx])
                        continue
                    if col < 9:
                        idx = cube.state[1][(row - 3) * 3 + col - 6]
                        spans += spanTemplate.format(FACELETS[idx])
                        continue
                    if col < 12:
                        idx = cube.state[5][(row - 3) * 3 + col - 9]
                        spans += spanTemplate.format(FACELETS[idx])
                        continue
            rows += rowTemplate.format(spans)
        view.add_phantom('scramble_state', firstLine, self.HTML_TEMPLATE.format(rows=rows, colorU=colorU, colorR=colorR, colorF=colorF, colorD=colorD, colorL=colorL, colorB=colorB), sublime.LAYOUT_BLOCK)
    def is_enabled(self):
        return is_fewest_moves(self.view)

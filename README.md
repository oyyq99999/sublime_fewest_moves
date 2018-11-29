# sublime_fewest_moves
A Sublime Text 3 plugin for FMC practises

## Usage

 1. Open a new buffer
 2. Set syntax to `Fewest Moves`
 3. Enter scramble on the first line, the plugin will show the scrambled cube state below it
 4. Type your solutions, and make sure there's at least 1 line after first line (i.e. start from line 3), the plugin will calculate move count for each line 1 second after you stop typing
 5. move your cursor to a skeleton and press <kbd>Ctrl</kbd>+<kbd>Alt</kbd>+<kbd>I</kbd>, the plugin will try to call `insertionfinder` command in your system to find insertions for the given scramble and skeleton.

The plugin recognizes `.fm` and `.fmc` as extensions for the syntax.

You can get `insertionfinder` from [here](https://github.com/xuanyan0x7c7/insertionfinder.git).

## Syntax Definition

 - The first line of the file is the scramble sequence
 - The second line of the file is an empty line
 - You may have any number of skeletons, skeletons are **separated by empty line(s)**
 - You may add comments to each line, any content from a `//` or a `#` symbol in a line to end of the line is considered as comments
 - You may have `NISS` operators in your solution, which indicates switch points of normal-scramble sequences and inverse-scramble sequences
 - You may use any WCA notation suitable for a 3x3x3 Cube, like `R L2 F' Bw2 2Rw' x2 y' z [u'] [f2] [d]` and so on

### Example

```
R' U' F U R2 D L2 B2 D2 U B2 L R2 U2 L2 B D R' B F' L' R2 B2 R' U' F

D' L2 # 2x2x2
NISS
B' R2 D2 R' D' R2 // pseudo 2x2x3
NISS
D2 R D R' B

D' L2
NISS
B' R2 D2 R' D' R2
NISS
D' B D B' D' R

D' L2 //comment
NISS
B' R2 D2 R' D' R2
NISS
D' B2 D B2 D'
NISS
R' B' U' B U R B'

D' L2
NISS
B' R2 D2 R' D' R2
NISS
D2 R2 D R2
```


import json
import tkinter as tk
import tkinter.font as font
import random
import pathlib

SCORE_FILE = pathlib.Path(f'{__file__}_score.json')


class SudokoGameBoard(object):
    """
    Basic Suboko Board using tkInter buttons and frames only
    """

    NONE = 0
    EASY = 1
    MEDIUM = 2
    HARD = 3

    class StatLabel(object):
        def __init__(self, parent, font, label, value):
            self._value = value
            self._valueTxt = tk.StringVar(value=f'{value}')
            self._frame = tk.Frame(master=parent, width=100, height=80)
            self._labelLabel = tk.Label(master=self._frame, text=label, font=font)
            self._labelLabel.grid(row=0, column=0)
            self._labelValue = tk.Label(master=self._frame, textvariable=self._valueTxt, font=font)
            self._labelValue.grid(row=0, column=1)

        def grid(self, row, column):
            self._frame.grid(row=row, column=column, padx=8, pady=8)
            return self

        def value(self):
            return self._value

        def increment(self):
            self._value += 1
            self._valueTxt.set(value=f'{self._value}')

    HIGHLIGHT_COLOR = 'green'
    BASE_COLOR = 'white'
    SELECTED_CELL_COLOR = 'aqua'

    def __init__(self, tk_root):
        """
        The sudoko board will be organized by 9 quadrants of 9 cells.
              0  1  2    3  4  5    6  7  8  (col)
            |------------------------------|
          0 |00 01 02 | 03 04 05 | 06 07 08|
          1 |09 10 11 | 12 13 14 | 15 16 17|
          2 |18 19 20 | 21 22 23 | 24 25 26|
           |------------------------------|
          3 |27 28 29 | 30 31 32 | 33 34 35|
          4 |36 37 38 | 39 40 41 | 42 43 44|
          5 |45 46 47 | 48 59 50 | 51 52 53|
           |------------------------------|
          6 |54 55 56 | 57 58 59 | 60 61 62|
          7 |63 64 65 | 66 67 68 | 69 70 71|
          8 |72 73 74 | 75 76 77 | 78 79 80|
        (row)
        """
        self._tk_root = tk_root
        self._current_game_level = SudokoGameBoard.NONE
        # Set the font for the buttons (numbers)
        self._button_font = font.Font(family='Courier', size=18, weight="bold")
        self._label_font = font.Font(family='Helvetica', size=14, weight="bold")

        # Define the main cell frame for the quads
        self._main_frame = tk.Frame(tk_root, width=640, height=480)
        self._main_frame.grid(row=0, column=0, padx=12, pady=12)

        # Create the lower number frame where you can choose a number
        self._number_frame = tk.Frame(tk_root, width=640, height=100)
        self._number_frame.grid(row=1, column=0, padx=12, pady=12)

        self._game_stat = tk.StringVar(value="Select a new game")
        self._misses_tally_frame = tk.Frame(tk_root, width=640, height=40)
        self._misses_tally_frame.grid(row=2, column=0)
        self._misses_tally_text = tk.Label(master=self._misses_tally_frame, textvariable=self._game_stat,
                                           font=self._label_font, foreground="green")
        self._misses_tally_text.pack()

        self._score_frame = tk.Frame(tk_root, width=640, height=160, borderwidth=2, highlightcolor="red", highlightthickness=2)
        self._score_frame.grid(row=3, column=0)

        if SCORE_FILE.is_file():
            score_json = json.loads(SCORE_FILE.read_text(encoding="UTF-8"))
        else:
            score_json = {'easy_w': 0, 'med_w': 0, 'hard_w': 0, 'easy_l': 0, 'med_l': 0, 'hard_l': 0}

        self._easy_wins_stat = self.StatLabel(parent=self._score_frame, font=self._label_font, label="Easy Wins", value=score_json['easy_w']).grid(row=0, column=0)
        self._easy_losses_stat = self.StatLabel(parent=self._score_frame, font=self._label_font, label="Easy Losses", value=score_json['easy_l']).grid(row=0, column=1)
        self._med_wins_stat = self.StatLabel(parent=self._score_frame, font=self._label_font, label="Medium Wins", value=score_json['med_w']).grid(row=1, column=0)
        self._med_losses_stat = self.StatLabel(parent=self._score_frame, font=self._label_font, label="Medium Losses", value=score_json['med_l']).grid(row=1, column=1)
        self._hard_wins_stat = self.StatLabel(parent=self._score_frame, font=self._label_font, label="Hard Wins", value=score_json['hard_w']).grid(row=2, column=0)
        self._hard_losses_stat = self.StatLabel(parent=self._score_frame, font=self._label_font, label="Hard Losses", value=score_json['hard_l']).grid(row=2, column=1)

        # Initialize the menu bar
        self._menu_bar = tk.Menu(tk_root)
        filemenu = tk.Menu(self._menu_bar, tearoff=0)
        filemenu.add_command(label='Easy Game', command=lambda level=SudokoGameBoard.EASY: self.new_game(level))
        filemenu.add_command(label='Intermediate Game', command=lambda level=SudokoGameBoard.MEDIUM: self.new_game(level))
        filemenu.add_command(label='Hard Game', command=lambda level=SudokoGameBoard.HARD: self.new_game(level))
        filemenu.add_separator()

        filemenu.add_command(label='Solve', command=lambda empty_cells=0: self.solve())
        self._menu_bar.add_cascade(label="File", menu=filemenu)
        tk_root.config(menu=self._menu_bar)

        # Manage the ui (buttons and quad frames)
        self._quad_frames = []
        self._number_map = []
        self._cell_map = {}
        self._selected_cell = -1

        # The sudoko board values (0=empty)
        self._values = [0 for n in range(0, 81)]
        self._uncovered = 0
        self._misses = 0
        self._max_allowed_misses = 3

        # Track the quad-to-cell relationships
        self._quad_to_cell_indices = []
        self._cell_to_quad_map = {}
        self._col_to_cell_indices_map = []
        self._row_to_cell_indices_map = []

        for i in range(0, 9):
            # track the quad number to all the cells in the quad
            q = ((i * 3) % 9) + int(i/3)*27
            q_cell_indices = [q+n for n in (0, 1, 2, 9, 10, 11, 18, 19, 20)]
            self._quad_to_cell_indices.append(q_cell_indices)
            for j in q_cell_indices:
                self._cell_to_quad_map[j] = i

            c = i
            c_cell_indices = [c+n for n in range(0, 80, 9)]
            self._col_to_cell_indices_map.append(c_cell_indices)

            r = i * 9
            r_cell_indices = [r+n for n in range(0, 9)]
            self._row_to_cell_indices_map.append(r_cell_indices)

            quad_frame = tk.Frame(self._main_frame, width=200, height=100)
            quad_col = i % 3
            quad_row = int(i / 3)
            quad_frame.grid(column=quad_col, row=quad_row,padx=4, pady=4)

            self._quad_frames.append(quad_frame)
            for cell_row in range(0, 3):
                for cell_col in range(0, 3):
                    q_index = cell_row * 3 + cell_col
                    cell_index = q_cell_indices[q_index]
                    cell = tk.Button(master=quad_frame, text=' ', width=3, height=1,
                                     background=SudokoGameBoard.BASE_COLOR, font=self._button_font,
                                     borderwidth=3,
                                     state=tk.DISABLED,
                                     command=lambda button_index=cell_index: self.on_click_cell(button_index))
                    cell.grid(column=cell_col, row=cell_row)
                    self._cell_map[cell_index] = cell

            number = tk.Button(master=self._number_frame, text=' ', width=3, height=1,
                               background=SudokoGameBoard.BASE_COLOR, font=self._button_font,
                               state=tk.DISABLED,
                               command=lambda button_index=i+1: self.on_click_number(button_index))
            number.grid(column=i, row=0)
            self._number_map.append(number)

    def get_available_numbers(self, cell_index):
        """
        Get the available numbers for a cell_index
        """
        quad, col, row = self.get_cell_mappings(cell_index)
        quad_numbers = [self._values[n] for n in self._quad_to_cell_indices[quad] if self._values[n]>0]
        col_numbers = [self._values[n] for n in self._col_to_cell_indices_map[col] if self._values[n]>0]
        row_numbers = [self._values[n] for n in self._row_to_cell_indices_map[row] if self._values[n]>0]
        available_numbers = [n for n in range(1, 10) if n not in quad_numbers and n not in col_numbers and n not in row_numbers]
        return available_numbers

    def get_cell_mappings(self, cell_index):
        """
        Get the tuple of cell indexes for (quad, column, row) based on the input cell
        :param cell_index: The cell index to calculate the quad, column, and row cell ids
        :return: (quad, column, row)
        """
        quad = self._cell_to_quad_map[cell_index]
        col = cell_index % 9
        row = int(cell_index / 9)
        return quad, col, row

    def on_click_cell(self, cell_index):

        # Collect the cell value, control, etc
        cell_value = self._values[cell_index]
        cell_ctrl = self._cell_map[cell_index]
        cell_uncovered = cell_value > 0

        # Set the current selected cell
        self._selected_cell = cell_index

        # Check if the cell is uncovered or not
        if cell_uncovered:
            # The cell is uncovered. Perform the following:

            # 1. Disable all the available numbers
            for n in range(0, 9):
                number_button = self._number_map[n]
                number_button['bg'] = SudokoGameBoard.BASE_COLOR
                number_button['text'] = ' '
                number_button['state'] = tk.DISABLED

            # 2. Highlight the current cell with 'HIGHLIGHT_COLOR'
            cell_ctrl['bg'] = SudokoGameBoard.HIGHLIGHT_COLOR

            # 3. Reset all the cells following the rules:
            #      Uncovered cells that match the current 'cell_value' will be highlighted with 'HIGHLIGHT_COLOR'
            #      All others will have no highlights
            for n in range(0, 81):
                n_cell_value = self._values[n]
                n_cell_ctrl = self._cell_map[n]
                if n_cell_value == cell_value:
                    n_cell_ctrl['bg'] = SudokoGameBoard.HIGHLIGHT_COLOR
                else:
                    n_cell_ctrl['bg'] = SudokoGameBoard.BASE_COLOR
            pass
        else:
            # The cell is not uncovered. Perform the following:
            # 1. Enable the possible values in the number bar based on the selected cell index
            available_numbers = self.get_available_numbers(cell_index)
            for n in range(0, 9):
                number_button = self._number_map[n]
                number_value = n + 1
                if number_value in available_numbers:
                    number_button['bg'] = SudokoGameBoard.BASE_COLOR
                    number_button['state'] = tk.NORMAL
                    number_button['text'] = f'{number_value}'
                else:
                    number_button['bg'] = SudokoGameBoard.BASE_COLOR
                    number_button['state'] = tk.DISABLED
                    number_button['text'] = ' '

            # 2. Un-highlight all the cells except for the current selected cell
            for n in range(0, 81):
                n_cell_ctrl = self._cell_map[n]
                if n != cell_index:
                    n_cell_ctrl['bg'] = SudokoGameBoard.BASE_COLOR

            # 3. Mark the selected cell by setting the background color
            cell_ctrl['bg'] = SudokoGameBoard.SELECTED_CELL_COLOR

    def populate_board(self, cells_to_show):

        # First randomly create a random sudoko board
        def solve(cell):
            # If there are no more available the `cell`, then we back track
            if cell == 81:
                return True
            available = self.get_available_numbers(cell)
            if len(available) == 0:
                return False
            random.shuffle(available)
            for v in available:
                self._values[cell] = v
                next = cell+1
                while next <= 80 and self._values[next] > 0:
                    next += 1
                if solve(next):
                    return True
                else:
                    self._values[cell] = 0
            return False
        solve(0)

        # Then based on how many cells to show, we will randomly 'hide' cells by
        # making them negative
        cells_to_hide = 81 - cells_to_show
        indices = [n for n in range(0, 81)]
        random.shuffle(indices)
        for n in range(0, cells_to_hide):
            self._values[indices[n]] = -self._values[indices[n]]

        # With the final values for uncovered (>0) and hidden (<0),
        # update all the cell controls
        for n in range(0, 81):
            # Reset the default cell styles
            cell_ctrl = self._cell_map[n]
            cell_ctrl['state'] = tk.NORMAL
            cell_ctrl['fg'] = 'black'

            cell_value = self._values[n]
            if cell_value > 0:
                #
                cell_ctrl['text'] = f'{cell_value}'
                cell_ctrl['bg'] = SudokoGameBoard.BASE_COLOR

            else:
                cell_ctrl['text'] = ' '

    def new_game(self, game_level):

        # Set the selected game level and initialize the title and status text
        self._current_game_level = game_level
        game_level_to_show_cells_map = {
            SudokoGameBoard.EASY: (65, "Easy Game"),
            SudokoGameBoard.MEDIUM: (45, "Medium Game"),
            SudokoGameBoard.HARD: (20, "Hard Game")
        }
        game_level_str = game_level_to_show_cells_map[game_level][1]
        self._tk_root.title(f"Sudoko - {game_level_str}")
        self._game_stat.set("")

        # Create a new sudoko board and reset the state of the game
        show_cells = game_level_to_show_cells_map[game_level][0]
        self.populate_board(show_cells)
        self._uncovered = show_cells
        self._misses = 0

        # Reset the selected cell and number board
        self._selected_cell = -1
        for n in range(0,9):
            number_button = self._number_map[n]
            number_button['bg'] = SudokoGameBoard.BASE_COLOR
            number_button['text'] = ' '
            number_button['state'] = tk.DISABLED

    def on_click_number(self, number_index):

        assert self._selected_cell > 0, "Expected a cell was selected"
        assert self._values[self._selected_cell] < 0, f"Selected cell at {self._selected_cell} expected to be a hidden number"

        selected_cell = self._cell_map[self._selected_cell]

        # Check the hidden value of the current selected cell against the clicked number
        hidden_value = -self._values[self._selected_cell]
        if number_index != hidden_value:
            self._misses += 1
            self._misses_tally_text['fg'] = 'red'
            self._game_stat.set(f"Misses: {'X '*self._misses}")
            selected_cell['text'] = f'{number_index}'
            selected_cell['fg'] = 'red'
            selected_cell['bg'] = SudokoGameBoard.BASE_COLOR

            # Check if we have too many misses
            if self._misses == self._max_allowed_misses:
                self.lose()
            # game over!
            pass
        else:
            # Selected number is correct, perform the following
            # 1. Uncover the number
            selected_cell['text'] = f'{number_index}'
            selected_cell['fg'] = 'black'
            selected_cell['bg'] = SudokoGameBoard.BASE_COLOR

            self._values[self._selected_cell] = number_index
            # 2. Reset the number bar
            for n in range(0, 9):
                number_button = self._number_map[n]
                number_button['bg'] = SudokoGameBoard.BASE_COLOR
                number_button['text'] = ' '
                number_button['state'] = tk.DISABLED
            # 3. Update the uncovered cells count
            self._uncovered += 1

            # 4. Check if we won
            if self._uncovered == 81:
                self.win()

        pass

    def win(self):

        # You won! Set all the cell grids to green, disable them so they can't be clicked anymore
        for n in range(0, 81):
            # Reset the default cell styles
            cell_ctrl = self._cell_map[n]
            cell_ctrl['state'] = tk.DISABLED
            cell_ctrl['fg'] = 'black'
            cell_ctrl['bg'] = SudokoGameBoard.BASE_COLOR

        # Clear the number board
        for n in range(0, 9):
            number_button = self._number_map[n]
            number_button['bg'] = SudokoGameBoard.BASE_COLOR
            number_button['text'] = ' '
            number_button['state'] = tk.DISABLED

        # Set the status to WIN!
        self._game_stat.set("You win!")
        self._misses_tally_text['fg'] = 'green'

        if self._current_game_level == SudokoGameBoard.EASY:
            self._easy_wins_stat.increment()
        elif self._current_game_level == SudokoGameBoard.MEDIUM:
            self._med_wins_stat.increment()
        elif self._current_game_level == SudokoGameBoard.HARD:
            self._hard_wins_stat.increment()
        else:
            assert False
        self.save_scores()

    def lose(self):

        # You won! Set all the cell grids to green, disable them so they can't be clicked anymore
        for n in range(0, 81):
            # Reset the default cell styles
            cell_ctrl = self._cell_map[n]
            cell_ctrl['state'] = tk.DISABLED
            cell_ctrl['fg'] = 'red'
            cell_ctrl['bg'] = SudokoGameBoard.BASE_COLOR

        # Clear the number board
        for n in range(0, 9):
            number_button = self._number_map[n]
            number_button['bg'] = SudokoGameBoard.BASE_COLOR
            number_button['text'] = ' '
            number_button['state'] = tk.DISABLED

        # Set the status to WIN!
        self._game_stat.set("You lost!")
        self._misses_tally_text['fg'] = 'red'

        if self._current_game_level == SudokoGameBoard.EASY:
            self._easy_losses_stat.increment()
        elif self._current_game_level == SudokoGameBoard.MEDIUM:
            self._med_losses_stat.increment()
        elif self._current_game_level == SudokoGameBoard.HARD:
            self._hard_losses_stat.increment()
        else:
            assert False
        self.save_scores()

    def solve(self):
        # Solve the remaining board, but dont update the stat
        for n in range(0, 81):
            # Reset the default cell styles
            cell_ctrl = self._cell_map[n]
            cell_ctrl['state'] = tk.NORMAL
            cell_ctrl['fg'] = 'black'

            if self._values[n] != 0:
                cell_value = abs(self._values[n])
                cell_ctrl['text'] = f'{cell_value}'
                cell_ctrl['bg'] = SudokoGameBoard.BASE_COLOR
                cell_ctrl['fg'] = 'black'
                cell_ctrl['state'] = tk.DISABLED


    def save_scores(self):
        score_json = { 'easy_w': self._easy_wins_stat.value(),
                       'med_w': self._med_wins_stat.value(),
                       'hard_w': self._hard_wins_stat.value(),
                       'easy_l': self._easy_losses_stat.value(),
                       'med_l': self._med_losses_stat.value(),
                       'hard_l': self._hard_losses_stat.value() }

        with SCORE_FILE.open("w") as target:
            json.dump(score_json, target,ensure_ascii=True,indent=2)


if __name__ == '__main__':
    root = tk.Tk()
    root.title("Sudoko")
    sudoko = SudokoGameBoard(root)
    root.mainloop()

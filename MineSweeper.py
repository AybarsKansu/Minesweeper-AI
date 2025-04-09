import tkinter as tk
from tkinter import ttk, messagebox
import random
import time

# Oyun Mantığı: MinesweeperBoard Sınıfı
# Bu sınıf mayın tarlası oyunundaki oyun alanını ve temel işlemleri yönetir.

class MinesweeperBoard:
    def __init__(self, width=10, height=10, num_mines=10):
        # Oyun alanının genişliği, yüksekliği ve mayın sayısı belirlenir.
        self.width = width
        self.height = height
        self.num_mines = num_mines
        self.reset_board()  # Oyun tahtası sıfırlanır

    def reset_board(self):
        # Oyun tahtasını baştan oluşturur.
        # Her hücre için mayın durumu, açılmışlık, bayraklanma ve komşu mayın sayısı tutulur.
        self.grid = [[{'is_mine': False, 'revealed': False, 'flagged': False, 'adjacent_mines': 0}
                      for _ in range(self.width)] for _ in range(self.height)]
        self.revealed_count = 0  # Açılan hücre sayısı sıfırlanır
        self.game_over = False  # Oyun henüz bitmedi
        self.first_move = True  # İlk hamle kontrolü
        self.mines_placed = False  # Mayınların yerleştirilip yerleştirilmediği bilgisi

    def place_mines(self, exclude_row, exclude_col):
        # İlk hamle yapılırken tıklanan hücreyi hariç tutarak mayınları yerleştirir.
        positions = [(i, j) for i in range(self.height) for j in range(self.width)
                     if not (i == exclude_row and j == exclude_col)]
        mine_positions = random.sample(positions, self.num_mines)  # Rastgele mayın pozisyonları seçilir
        for i, j in mine_positions:
            self.grid[i][j]['is_mine'] = True  # Seçilen hücrelere mayın yerleştirilir
        self.calculate_adjacent_mines()  # Her hücre için komşu mayın sayıları hesaplanır

    def calculate_adjacent_mines(self):
        # Her hücre için etrafındaki (komşu) hücrelerde kaç adet mayın bulunduğunu hesaplar.
        for i in range(self.height):
            for j in range(self.width):
                count = 0
                # Hücrenin çevresindeki 8 hücre kontrol edilir (kenar ve köşe durumları için sınırlar ayarlanır)
                for x in range(max(0, i - 1), min(self.height, i + 2)):
                    for y in range(max(0, j - 1), min(self.width, j + 2)):
                        if x == i and y == j:
                            continue  # Kendi hücresi hariç tutulur
                        if self.grid[x][y]['is_mine']:
                            count += 1  # Mayın varsa sayacı artırır
                self.grid[i][j]['adjacent_mines'] = count  # Komşu mayın sayısı atanır

    def reveal(self, row, col):
        # Belirtilen hücreyi açma işlemini gerçekleştirir.
        # Eğer oyun bitmişse, hücre zaten açılmışsa veya bayraklıysa hiçbir işlem yapmaz.
        if self.game_over or self.grid[row][col]['revealed'] or self.grid[row][col]['flagged']:
            return False

        # İlk hamle ise, tıklanan hücre hariç mayınları yerleştirir.
        if self.first_move:
            self.place_mines(row, col)
            self.first_move = False
            self.mines_placed = True

        # Hücre açılır ve açılan hücre sayısı artırılır.
        self.grid[row][col]['revealed'] = True
        self.revealed_count += 1

        # Eğer açılan hücrede mayın varsa, oyunu bitirir.
        if self.grid[row][col]['is_mine']:
            self.game_over = True
            return True

        # Eğer açılan hücrede komşu mayın yoksa, çevresindeki tüm hücreleri açmaya çalışır.
        if self.grid[row][col]['adjacent_mines'] == 0:
            for x in range(max(0, row - 1), min(self.height, row + 2)):
                for y in range(max(0, col - 1), min(self.width, col + 2)):
                    if not self.grid[x][y]['revealed']:
                        self.reveal(x, y)

        # Eğer açılan hücre sayısı kazanma durumunu sağlarsa oyunu bitirir.
        if self.revealed_count == self.width * self.height - self.num_mines:
            self.game_over = True
        return False

    def get_adjacent_cells(self, row, col):
        # Belirtilen hücrenin çevresindeki henüz açılmamış hücreleri döndürür.
        cells = []
        for i in range(max(0, row - 1), min(self.height, row + 2)):
            for j in range(max(0, col - 1), min(self.width, col + 2)):
                if (i, j) != (row, col) and not self.grid[i][j]['revealed']:
                    cells.append((i, j))
        return cells

    def save_state(self):
        # Oyun tahtasının mevcut durumunu (grid, açılan hücre sayısı, oyun durumu vs.) kaydeder.
        return {
            'grid': [[cell.copy() for cell in row] for row in self.grid],
            'revealed_count': self.revealed_count,
            'game_over': self.game_over,
            'first_move': self.first_move,
            'mines_placed': self.mines_placed
        }

    def load_state(self, state):
        # Daha önce kaydedilmiş olan durumu geri yükler.
        self.grid = [[cell.copy() for cell in row] for row in state['grid']]
        self.revealed_count = state['revealed_count']
        self.game_over = state['game_over']
        self.first_move = state['first_move']
        self.mines_placed = state['mines_placed']

# SolverBase: Ortak Çözücü Sınıfı
# Tüm çözücü algoritmaların ortak özelliklerini ve temel yöntemlerini barındırır.

class SolverBase:
    def __init__(self, board):
        self.board = board  # Oyun tahtasına referans
        self.bad_moves = set()  # Güvenli olmayan hamlelerin kaydı
        self.flagged_mines = set()  # İşaretlenmiş mayınların takibi
        self.visited = set()  # Ziyaret edilen hücrelerin takibi (bazı algoritmalarda kullanılır)

    def find_safe_moves(self):
        """
        Basit mantıksal kurallar kullanarak güvenli hamleleri ve mayın olabilecek hücreleri belirler.
        Her açılmış hücrenin komşularını kontrol ederek iki kural uygular:
         - Kural 1: Kalan sayı gizli hücre sayısına eşitse, tüm gizli hücreler mayındır.
         - Kural 2: Kalan sayı 0 ise, tüm gizli hücreler güvenlidir.
        """
        safe = []
        mines = []

        # Tüm açılmış hücreler üzerinden geçerek komşu hücreleri inceler.
        for i in range(self.board.height):
            for j in range(self.board.width):
                if self.board.grid[i][j]['revealed'] and self.board.grid[i][j]['adjacent_mines'] > 0:
                    adj = self.board.get_adjacent_cells(i, j)
                    # Açılmamış ve bayraklanmamış hücreler bulunur.
                    hidden = [c for c in adj if not self.board.grid[c[0]][c[1]]['revealed']
                              and not self.board.grid[c[0]][c[1]]['flagged']]
                    # Bayraklanmış hücrelerin sayısı hesaplanır.
                    flags = sum(1 for c in adj if self.board.grid[c[0]][c[1]]['flagged'])
                    remaining = self.board.grid[i][j]['adjacent_mines'] - flags

                    # Eğer kalan sayı gizli hücre sayısına eşitse, bu hücreler mayın olarak işaretlenmelidir.
                    if remaining == len(hidden) and hidden:
                        for cell in hidden:
                            if cell not in mines:
                                mines.append(cell)

                    # Eğer kalan sayı 0 ise, komşudaki tüm gizli hücreler güvenlidir.
                    elif remaining == 0 and hidden:
                        for cell in hidden:
                            if cell not in safe:
                                safe.append(cell)

        # Sonuçları küme yapısına çevirip tekrar listeye çevirir (tekrarlananları önlemek için)
        return list(set(safe)), list(set(mines))

    def flag_mines(self, mines):
        # Belirlenen mayın konumlarını bayraklar ve flag listesine ekler.
        for x, y in mines:
            if not self.board.grid[x][y]['flagged']:
                self.board.grid[x][y]['flagged'] = True
                self.flagged_mines.add((x, y))

    def get_probability_move(self):
        """
        Olasılıksal olarak en iyi hamleyi seçer.
        Açılmamış ve bayraklanmamış hücreler arasından, açılmış hücrelere en yakın olanı tercih eder.
        """
        unknown_cells = []
        for i in range(self.board.height):
            for j in range(self.board.width):
                if (not self.board.grid[i][j]['revealed'] and
                        not self.board.grid[i][j]['flagged'] and
                        (i, j) not in self.bad_moves):
                    # Hücrenin açılmış komşu sayısı hesaplanır
                    adjacent_revealed = 0
                    for ni, nj in self._get_neighbors(i, j):
                        if self.board.grid[ni][nj]['revealed']:
                            adjacent_revealed += 1

                    unknown_cells.append((adjacent_revealed, i, j))

        # En fazla açılmış komşusu olan hücreyi seçer
        unknown_cells.sort(reverse=True)
        return (unknown_cells[0][1], unknown_cells[0][2]) if unknown_cells else None

    def _get_neighbors(self, row, col):
        # Belirtilen hücrenin komşularını döndürür.
        neighbors = []
        for i in range(max(0, row - 1), min(self.board.height, row + 2)):
            for j in range(max(0, col - 1), min(self.board.width, col + 2)):
                if (i, j) != (row, col):
                    neighbors.append((i, j))
        return neighbors



# LogicalSolver Sınıfı
# Basit mantıksal kuralları kullanarak hamle belirleyen çözücü.
# 10x10'luk 10 mayınlı mayın tarlasında ortalama 10.596 saniyede çözümü buluyor.
class LogicalSolver(SolverBase):
    def get_next_move(self):
        # Güvenli hamleleri ve mayın olabilecek hücreleri bulur.
        safe, mines = self.find_safe_moves()

        # Bulunan mayın hücrelerini bayraklar.
        self.flag_mines(mines)

        # Eğer güvenli hamle varsa, ilkini döndürür.
        if safe:
            return safe[0]

        # Güvenli hamle bulunamazsa olasılıksal hamleyi döndürür.
        return self.get_probability_move()



# DFSSolver Sınıfı
# Derinlemesine arama (DFS) mantığı ile hamle seçen çözücü.
# 10x10'luk 10 mayınlı mayın tarlasında ortalama 11.324 saniyede çözümü buluyor.
class DFSSolver(SolverBase):
    def __init__(self, board):
        super().__init__(board)
        self.visited = set()  # DFS sırasında ziyaret edilen hücreleri takip eder

    def get_next_move(self):
        safe, mines = self.find_safe_moves()

        # Bulunan mayınları işaretler.
        self.flag_mines(mines)

        # Güvenli hamle varsa ilkini döndürür.
        if safe:
            return safe[0]

        # DFS mantığı: Henüz ziyaret edilmemiş ve bayraklanmamış hücreler arasından seçim yapar.
        for i in range(self.board.height):
            for j in range(self.board.width):
                if (not self.board.grid[i][j]['revealed'] and
                        not self.board.grid[i][j]['flagged'] and
                        (i, j) not in self.visited and
                        (i, j) not in self.bad_moves):
                    self.visited.add((i, j))  # Hücreyi ziyaret edildi olarak işaretle
                    return (i, j)  # İlk bulunan uygun hücreyi seç

        # Hiçbir güvenli hamle bulunamazsa olasılıksal hamleyi döndürür.
        return self.get_probability_move()


# AStarSolver Sınıfı
# A* algoritmasına benzer sezgisel bir yaklaşım kullanarak hamle seçen çözücü.
# 10x10'luk 10 mayınlı mayın tarlasında ortalama 7.912 saniyede çözümü buluyor.
class AStarSolver(SolverBase):
    def get_next_move(self):
        safe, mines = self.find_safe_moves()

        # Mayınları işaretler.
        self.flag_mines(mines)

        # Güvenli hamle varsa döndürür.
        if safe:
            return safe[0]

        # A* mantığı: priority = revealed_neighbors - (total_adjacent_mines / (8 * revealed_neighbors)).
        candidates = []
        for i in range(self.board.height):
            for j in range(self.board.width):
                if (not self.board.grid[i][j]['revealed'] and
                        not self.board.grid[i][j]['flagged'] and
                        (i, j) not in self.bad_moves):

                    revealed_neighbors = 0
                    total_adjacent_mines = 0
                    for ni, nj in self._get_neighbors(i, j):
                        if self.board.grid[ni][nj]['revealed']:
                            revealed_neighbors += 1
                            total_adjacent_mines += self.board.grid[ni][nj]['adjacent_mines']

                    # Sezgisel hesaplama: Açılmış komşu sayısı ve ortalama mayın sayısı üzerinden öncelik belirlenir.
                    if revealed_neighbors > 0:
                        priority = revealed_neighbors - (total_adjacent_mines / (8 * revealed_neighbors))
                        # Negatif değer kullanılarak küçükten büyüğe sıralama sağlanır.
                        candidates.append((-priority, i, j))

        candidates.sort()  # Öncelik sırasına göre sıralar

        if candidates:
            return (candidates[0][1], candidates[0][2])

        # Güvenli hamle bulunamazsa olasılıksal hamleyi döndürür.
        return self.get_probability_move()

# BacktrackingSolver Sınıfı
# Geriye izleme algoritması kullanarak hamle seçen çözücü.
# 10x10'luk 10 mayınlı mayın tarlasında ortalama 8.88 saniyede çözümü buluyor.
class BacktrackingSolver(SolverBase):
    def get_next_move(self):
        # Öncelikle basit mantıksal kurallarla güvenli hamle bulunur.
        safe, mines = self.find_safe_moves()

        # Bulunan mayınları işaretler.
        self.flag_mines(mines)

        # Eğer güvenli hamle bulunursa döndürülür.
        if safe:
            return safe[0]

        # Basit mantık yetersizse, geri izleme algoritması devreye girer.
        safe_cells, mine_cells = self.deduce_mines_and_safe()

        # Tespit edilen mayınları işaretler.
        self.flag_mines(mine_cells)

        # Güvenli hücrelerden birini döndürür.
        if safe_cells:
            return safe_cells[0]

        # Hiçbir güvenli hamle bulunamazsa olasılıksal hamleyi döndürür.
        return self.get_probability_move()

    def deduce_mines_and_safe(self):
        """
        Geriye izleme algoritması ile sınır hücreleri üzerinde atama yaparak,
        kesin olarak mayın veya güvenli olan hücreleri belirler.
        """
        # Açılmış hücrelere komşu olan ancak henüz açılmamış hücreleri (frontier) belirler.
        frontier = set()
        for i in range(self.board.height):
            for j in range(self.board.width):
                if not self.board.grid[i][j]['revealed'] and not self.board.grid[i][j]['flagged']:
                    neighbors = self._get_neighbors(i, j)
                    for ni, nj in neighbors:
                        if self.board.grid[ni][nj]['revealed']:
                            frontier.add((i, j))
                            break

        # Frontier çok büyükse, performans için kısıtlamalar uygulanır.
        MAX_FRONTIER_SIZE = 16
        if len(frontier) > MAX_FRONTIER_SIZE:
            # Frontier içerisinden en fazla açılmış komşusu olanları seç.
            sorted_frontier = sorted(list(frontier),
                                     key=lambda cell: sum(1 for ni, nj in self._get_neighbors(cell[0], cell[1])
                                                          if self.board.grid[ni][nj]['revealed']))
            frontier = set(sorted_frontier[:MAX_FRONTIER_SIZE])

        frontier = list(frontier)
        valid_assignments = []  # Geçerli atamaları tutacak liste
        assignment = {}  # Hücrelere atanan değerler (True: mayın, False: güvenli)

        # Açılmış hücreler için kısıtlamaları toplar: her açılmış hücrenin komşularındaki gizli hücre sayısı ve
        # bu hücrelerde olması gereken mayın sayısı.
        constraints = []
        for i in range(self.board.height):
            for j in range(self.board.width):
                if self.board.grid[i][j]['revealed'] and self.board.grid[i][j]['adjacent_mines'] > 0:
                    neighbors = self._get_neighbors(i, j)
                    frontier_adj = [cell for cell in neighbors if cell in frontier]
                    if frontier_adj:
                        already_flagged = sum(1 for ni, nj in neighbors
                                              if self.board.grid[ni][nj]['flagged'])
                        remaining = self.board.grid[i][j]['adjacent_mines'] - already_flagged
                        constraints.append((frontier_adj, remaining))

        def check_assignment(assign):
            """
            Atanan değerlere göre tüm kısıtlamaların sağlanıp sağlanmadığını kontrol eder.
            """
            for cells, count in constraints:
                relevant_cells = [c for c in cells if c in assign]
                if len(relevant_cells) == len(cells):  # Tüm ilgili hücreler atandıysa
                    if sum(assign[c] for c in cells) != count:
                        return False
            return True

        def backtrack(index):
            """
            Geriye izleme algoritmasını uygular. Tüm frontier hücreleri için atama yapar ve
            geçerli atamalar listesini oluşturur.
            """
            if index == len(frontier):
                if check_assignment(assignment):
                    valid_assignments.append(assignment.copy())
                return

            cell = frontier[index]

            # Hücreyi mayın olarak atamayı dener.
            assignment[cell] = True
            if check_assignment(assignment):
                backtrack(index + 1)

            # Hücreyi güvenli olarak atamayı dener.
            assignment[cell] = False
            if check_assignment(assignment):
                backtrack(index + 1)

            del assignment[cell]

        # Geriye izleme algoritmasını başlatır.
        backtrack(0)

        # Geçerli atamalara göre kesin olarak mayın veya güvenli olan hücreleri belirler.
        mine_cells = []
        safe_cells = []

        if valid_assignments:
            for cell in frontier:
                # Tüm atamalarda hücre mayın ise kesin mayın olarak işaretlenir.
                if all(assign[cell] for assign in valid_assignments):
                    mine_cells.append(cell)
                # Tüm atamalarda hücre güvenli ise kesin güvenli olarak işaretlenir.
                elif all(not assign[cell] for assign in valid_assignments):
                    safe_cells.append(cell)

        return safe_cells, mine_cells


# --------------------------
# GUI ve Oyun Mantığı
# Minesweeper oyununu tkinter arayüzü ile oynanabilir hale getirir ve çözücü algoritmaları entegre eder.
# --------------------------
class MinesweeperGUI:
    def __init__(self, master, width=10, height=10, num_mines=10):
        self.master = master
        self.board = MinesweeperBoard(width, height, num_mines)
        self.width = width
        self.height = height
        self.num_mines = num_mines

        # Kullanılacak algoritmalar arasında "Manual" modu da bulunur.
        # Arc Consistency algoritması kaldırıldığı için seçenek listesinden çıkarıldı.
        self.algorithm = tk.StringVar(value="Manual")
        self.solver = None  # Otomatik çözücü nesnesi
        self.solver_running = False  # Çözücü çalışıyor mu kontrolü
        self.paused = False  # Duraklatma durumu
        self.start_time = None  # Oyuna başlama zamanı

        self.setup_ui()  # Arayüz öğelerini oluşturur

    def setup_ui(self):
        # Kontrol çerçevesi oluşturulur.
        control_frame = tk.Frame(self.master)
        control_frame.pack(pady=10)

        ttk.Label(control_frame, text="Algorithm:").pack(side=tk.LEFT)
        # Kullanılabilir algoritmalar listesi (Arc Consistency kaldırıldı)
        algorithms = ["Manual", "Logical", "DFS", "A*", "Backtracking"]
        for algo in algorithms:
            rb = tk.Radiobutton(control_frame, text=algo, variable=self.algorithm, value=algo)
            rb.pack(side=tk.LEFT, padx=5)

        # Başlat butonu ve duraklatma butonu oluşturulur.
        ttk.Button(control_frame, text="Start", command=self.start_mode).pack(side=tk.LEFT, padx=10)
        self.pause_button = ttk.Button(control_frame, text="Pause", command=self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        # Oyun alanı için grid çerçevesi oluşturulur.
        self.grid_frame = tk.Frame(self.master)
        self.grid_frame.pack()

        self.buttons = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                # Her hücre için bir buton oluşturulur; başlangıçta manuel modda kullanılmak üzere ayarlanır.
                btn = tk.Button(self.grid_frame, text=' ', width=3, font=('Arial', 8))
                btn.grid(row=i, column=j)
                row.append(btn)
            self.buttons.append(row)

    def toggle_pause(self):
        # Çözücü duraklatma veya devam ettirme işlemini yönetir.
        if self.paused:
            self.paused = False
            self.pause_button.config(text="Pause")
            if self.algorithm.get() != "Manual":
                self.make_move()
        else:
            self.paused = True
            self.pause_button.config(text="Resume")

    def update_display(self):
        # Her hücre için buton görünümünü günceller.
        for i in range(self.height):
            for j in range(self.width):
                cell = self.board.grid[i][j]
                btn = self.buttons[i][j]

                if cell['flagged']:
                    btn.config(text='🚩', bg='red', relief=tk.RAISED)
                elif cell['revealed']:
                    btn.config(relief=tk.SUNKEN,
                               text=str(cell['adjacent_mines']) if cell['adjacent_mines'] > 0 else ' ',
                               bg='lightgrey', state=tk.DISABLED)
                else:
                    btn.config(text=' ', bg='SystemButtonFace', relief=tk.RAISED, state=tk.NORMAL)

                # Oyun bittiğinde, mayınlar bayraklı şekilde gösterilir.
                if self.board.game_over and cell['is_mine']:
                    btn.config(text='🚩', bg='red')

    def start_mode(self):
        # Oyunu başlatır ve seçilen moda göre çözücü veya manuel oynanış ayarlanır.
        self.board.reset_board()  # Oyun tahtası sıfırlanır
        self.update_display()  # Ekran güncellenir
        mode = self.algorithm.get()
        self.solver_running = False
        self.paused = False
        self.pause_button.config(text="Pause")
        self.start_time = time.time()  # Oyuna başlama zamanı kaydedilir

        # Manuel mod için her butona sol tıklama ve sağ tıklama işlemleri bağlanır.
        if mode == "Manual":
            for i in range(self.height):
                for j in range(self.width):
                    self.buttons[i][j].config(command=lambda i=i, j=j: self.manual_left_click(i, j))
                    self.buttons[i][j].bind("<Button-3>", lambda e, i=i, j=j: self.manual_right_click(i, j))
        else:
            # Otomatik modlar için uygun çözücü (solver) oluşturulur.
            if mode == "Logical":
                self.solver = LogicalSolver(self.board)
            elif mode == "DFS":
                self.solver = DFSSolver(self.board)
            elif mode == "A*":
                self.solver = AStarSolver(self.board)
            elif mode == "Backtracking":
                self.solver = BacktrackingSolver(self.board)

            # Otomatik modda butonlar pasif hale getirilir.
            for i in range(self.height):
                for j in range(self.width):
                    self.buttons[i][j].config(command=None)
                    self.buttons[i][j].unbind("<Button-3>")

            # Çözücü başlatılır.
            self.solver_running = True
            self.make_move()

    def manual_left_click(self, i, j):
        # Manuel modda sol tıklama işlemi: Hücre açılır.
        if self.board.game_over:
            return
        cell = self.board.grid[i][j]
        if cell['flagged'] or cell['revealed']:
            return
        mine_hit = self.board.reveal(i, j)  # Hücre açılır ve mayın kontrolü yapılır.
        self.update_display()  # Ekran güncellenir.
        if mine_hit:
            self.show_game_over()  # Mayına basılırsa oyun biter.
        elif self.board.revealed_count == self.width * self.height - self.num_mines:
            self.show_game_over()  # Tüm güvenli hücreler açılırsa oyun kazanılır.

    def manual_right_click(self, i, j):
        # Manuel modda sağ tıklama işlemi: Hücre bayraklanır veya bayrak kaldırılır.
        if self.board.game_over:
            return
        cell = self.board.grid[i][j]
        if cell['revealed']:
            return

        # Hücre bayrak durumu değiştirilir.
        cell['flagged'] = not cell['flagged']
        self.update_display()  # Görüntü güncellenir.

    def make_move(self):
        # Otomatik modda çözücünün hamle yapma işlemini yönetir.
        if self.paused or not self.solver_running or self.board.game_over:
            return

        # Güvenli hamleler ve mayın hücreleri tespit edilir.
        prev_state = self.board.save_state()
        if hasattr(self.solver, 'find_safe_moves'):
            safe, mines = self.solver.find_safe_moves()
            # Eğer çözücü kendi içinde bayraklama yapmıyorsa burada bayraklama yapılır.
            if hasattr(self.solver, 'flag_mines'):
                self.solver.flag_mines(mines)

        self.update_display()  # Ekran güncellenir
        self.master.update_idletasks()

        if self.paused or not self.solver_running or self.board.game_over:
            return

        # Çözücüden bir sonraki hamle alınır.
        move = self.solver.get_next_move()

        # Eğer hamle bulunamazsa, gizli hücrelerden rastgele seçim yapılır.
        if not move:
            hidden = [(i, j) for i in range(self.height) for j in range(self.width)
                      if (not self.board.grid[i][j]['revealed'] and
                          not self.board.grid[i][j]['flagged'] and
                          (i, j) not in getattr(self.solver, 'bad_moves', set()))]

            if hidden:
                move = random.choice(hidden)
            else:
                self.show_game_over()
                return

        if move:
            row, col = move
            prev_state = self.board.save_state()  # Hamle öncesi durum kaydedilir.
            mine_hit = self.board.reveal(row, col)

            if mine_hit:
                #önceki duruma geri dönüp hamleyi kötü olarak işaretler.
                self.board.load_state(prev_state)
                if hasattr(self.solver, 'bad_moves'):
                    self.solver.bad_moves.add((row, col))
                if hasattr(self.solver, 'visited'):
                    self.solver.visited.discard((row, col))
                self.update_display()
                self.master.after(500, self.make_move)
            else:
                # Hamle başarılıysa ekran güncellenir ve sonraki hamle için beklenir.
                self.update_display()
                if self.board.game_over:
                    self.show_game_over()
                    return

                self.master.after(500, self.make_move)
        else:
            self.show_game_over()

    def show_game_over(self):
        # Oyun bittiğinde çözücüyü durdurur ve oyun sonucunu, çözüm süresiyle birlikte mesaj kutusu ile gösterir.
        self.solver_running = False
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        if self.board.revealed_count == self.width * self.height - self.num_mines:
            messagebox.showinfo("Oyun Bitti", f"Tebrikler, oyunu kazandınız!\nÇözüm süresi: {elapsed_time:.2f} saniye.")
        else:
            messagebox.showinfo("Oyun Bitti", f"Mayına bastınız, oyunu kaybettiniz!\nÇözüm süresi: {elapsed_time:.2f} saniye.")


if __name__ == "__main__":
    # Tkinter penceresi oluşturulur, başlık ayarlanır ve GUI çalıştırılır.
    root = tk.Tk()
    root.title("Minesweeper Solver")
    gui = MinesweeperGUI(root, width=10, height=10, num_mines=10)
    root.mainloop()

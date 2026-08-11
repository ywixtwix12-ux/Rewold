import tkinter as tk
from tkinter import filedialog, messagebox
import re

# =============================================================
# OPTIONAL LIBRARIES
# =============================================================

try:
    from tkinterweb import HtmlFrame
    HTML_PREVIEW_AVAILABLE = True
except ImportError:
    HTML_PREVIEW_AVAILABLE = False


try:
    from spellchecker import SpellChecker
    SPELLCHECKER_AVAILABLE = True
except ImportError:
    SPELLCHECKER_AVAILABLE = False


class RewoldApp:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Rewold — Бесплатный редактор документов"
        )

        self.root.geometry("1200x700")

        self.current_file = None
        self.preview_enabled = True
        self.updating_text = False

        # =====================================================
        # SPELLCHECKER
        # =====================================================

        if SPELLCHECKER_AVAILABLE:
            self.spellchecker = SpellChecker(
                language="ru"
            )
        else:
            self.spellchecker = None

        self._setup_ui()

    # =========================================================
    # UI
    # =========================================================

    def _setup_ui(self):

        self.menu_bar = tk.Menu(
            self.root
        )

        self.root.config(
            menu=self.menu_bar
        )

        # =====================================================
        # FILE MENU
        # =====================================================

        file_menu = tk.Menu(
            self.menu_bar,
            tearoff=0
        )

        file_menu.add_command(
            label="Сохранить как...",
            command=self.save_file_as
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="Выход",
            command=self.root.quit
        )

        self.menu_bar.add_cascade(
            label="Файл",
            menu=file_menu
        )

        # =====================================================
        # VIEW MENU
        # =====================================================

        view_menu = tk.Menu(
            self.menu_bar,
            tearoff=0
        )

        view_menu.add_command(
            label="Переключить предпросмотр",
            command=self.toggle_preview
        )

        self.menu_bar.add_cascade(
            label="Вид",
            menu=view_menu
        )

        # =====================================================
        # MAIN AREA
        # =====================================================

        self.main_frame = tk.Frame(
            self.root
        )

        self.main_frame.pack(
            expand=True,
            fill="both"
        )

        # =====================================================
        # EDITOR
        # =====================================================

        self.editor_frame = tk.Frame(
            self.main_frame
        )

        self.editor_frame.pack(
            side="left",
            expand=True,
            fill="both"
        )

        self.editor_label = tk.Label(
            self.editor_frame,
            text="  Rewold HTML Editor",
            anchor="w",
            font=("Arial", 10, "bold")
        )

        self.editor_label.pack(
            fill="x"
        )

        self.text_area = tk.Text(
            self.editor_frame,
            wrap="word",
            font=("Consolas", 12),
            undo=True,
            padx=10,
            pady=10
        )

        self.text_area.pack(
            expand=True,
            fill="both"
        )

        # =====================================================
        # SPELLING STYLE
        # =====================================================

        self.text_area.tag_config(
            "misspelled",
            foreground="#d00000",
            underline=True
        )

        # =====================================================
        # CONTEXT MENU
        # =====================================================

        self.setup_context_menu()

        # =====================================================
        # PREVIEW
        # =====================================================

        self.preview_frame = tk.Frame(
            self.main_frame
        )

        self.preview_frame.pack(
            side="right",
            expand=True,
            fill="both"
        )

        self.preview_label = tk.Label(
            self.preview_frame,
            text="  Live Preview",
            anchor="w",
            font=("Arial", 10, "bold")
        )

        self.preview_label.pack(
            fill="x"
        )

        if HTML_PREVIEW_AVAILABLE:

            self.html_preview = HtmlFrame(
                self.preview_frame,
                messages_enabled=False
            )

            self.html_preview.pack(
                expand=True,
                fill="both"
            )

        else:

            self.html_preview = None

            self.preview_error = tk.Label(
                self.preview_frame,
                text=(
                    "Live Preview недоступен.\n\n"
                    "Установи tkinterweb:\n\n"
                    "pip install tkinterweb"
                ),
                justify="center"
            )

            self.preview_error.pack(
                expand=True
            )

        # =====================================================
        # EVENTS
        # =====================================================

        self.text_area.bind(
            "<KeyRelease>",
            self.on_text_change
        )

        self.text_area.bind(
            "<KeyPress>",
            self.on_key_press
        )

        self.text_area.bind(
            "<Tab>",
            self.handle_tab
        )

        # =====================================================
        # SYNTAX TAGS
        # =====================================================

        self._setup_syntax_tags()

    # =========================================================
    # CONTEXT MENU
    # =========================================================

    def setup_context_menu(self):

        self.context_menu = tk.Menu(
            self.root,
            tearoff=0
        )

        self.context_menu.add_command(
            label="↶ Отменить",
            command=self.undo_text
        )

        self.context_menu.add_command(
            label="↷ Повторить",
            command=self.redo_text
        )

        self.context_menu.add_separator()

        self.context_menu.add_command(
            label="✂ Вырезать",
            command=self.cut_text
        )

        self.context_menu.add_command(
            label="📋 Копировать",
            command=self.copy_text
        )

        self.context_menu.add_command(
            label="📄 Вставить",
            command=self.paste_text
        )

        self.context_menu.add_separator()

        self.context_menu.add_command(
            label="Выделить всё",
            command=self.select_all
        )

        self.context_menu.add_separator()

        self.context_menu.add_command(
            label="🔤 Проверить орфографию",
            command=self.check_all_spelling
        )

        self.context_menu.add_command(
            label="✨ Обновить предпросмотр",
            command=self.update_preview
        )

        self.text_area.bind(
            "<Button-3>",
            self.show_context_menu
        )

    def show_context_menu(self, event):

        try:

            self.text_area.mark_set(
                tk.INSERT,
                f"@{event.x},{event.y}"
            )

            self.context_menu.tk_popup(
                event.x_root,
                event.y_root
            )

        finally:

            self.context_menu.grab_release()

    # =========================================================
    # CONTEXT ACTIONS
    # =========================================================

    def undo_text(self):

        try:
            self.text_area.edit_undo()
            self.after_edit()
        except tk.TclError:
            pass

    def redo_text(self):

        try:
            self.text_area.edit_redo()
            self.after_edit()
        except tk.TclError:
            pass

    def cut_text(self):

        self.text_area.event_generate(
            "<<Cut>>"
        )

        self.after_edit()

    def copy_text(self):

        self.text_area.event_generate(
            "<<Copy>>"
        )

    def paste_text(self):

        self.text_area.event_generate(
            "<<Paste>>"
        )

        self.root.after(
            50,
            self.after_edit
        )

    def select_all(self):

        self.text_area.tag_add(
            tk.SEL,
            "1.0",
            tk.END
        )

        self.text_area.mark_set(
            tk.INSERT,
            "1.0"
        )

        self.text_area.see(
            tk.INSERT
        )

    # =========================================================
    # SYNTAX HIGHLIGHTING
    # =========================================================

    def _setup_syntax_tags(self):

        self.text_area.tag_config(
            "tag",
            foreground="#0066cc"
        )

        self.text_area.tag_config(
            "attribute",
            foreground="#993399"
        )

        self.text_area.tag_config(
            "string",
            foreground="#008000"
        )

        self.text_area.tag_config(
            "comment",
            foreground="#777777"
        )

        self.text_area.tag_config(
            "doctype",
            foreground="#aa5500"
        )

    def highlight_syntax(self):

        if self.updating_text:
            return

        self.updating_text = True

        try:

            for tag in (
                "tag",
                "attribute",
                "string",
                "comment",
                "doctype"
            ):

                self.text_area.tag_remove(
                    tag,
                    "1.0",
                    tk.END
                )

            content = self.text_area.get(
                "1.0",
                tk.END
            )

            # =================================================
            # COMMENTS
            # =================================================

            for match in re.finditer(
                r"<!--.*?-->",
                content,
                re.DOTALL
            ):

                self.text_area.tag_add(
                    "comment",
                    f"1.0+{match.start()}c",
                    f"1.0+{match.end()}c"
                )

            # =================================================
            # DOCTYPE
            # =================================================

            for match in re.finditer(
                r"<!DOCTYPE[^>]*>",
                content,
                re.IGNORECASE
            ):

                self.text_area.tag_add(
                    "doctype",
                    f"1.0+{match.start()}c",
                    f"1.0+{match.end()}c"
                )

            # =================================================
            # HTML TAGS
            # =================================================

            tag_pattern = (
                r"</?[a-zA-Z][a-zA-Z0-9-]*"
                r"(?:\s+[^<>]*?)?/?>"
            )

            for match in re.finditer(
                tag_pattern,
                content
            ):

                tag_start = match.start()
                tag_end = match.end()

                tag_text = match.group()

                self.text_area.tag_add(
                    "tag",
                    f"1.0+{tag_start}c",
                    f"1.0+{tag_end}c"
                )

                # =================================================
                # ATTRIBUTES
                # =================================================

                attribute_pattern = (
                    r"\s+"
                    r"([a-zA-Z_:][a-zA-Z0-9_:.!-]*)"
                    r"(?:\s*=\s*)?"
                )

                for attribute in re.finditer(
                    attribute_pattern,
                    tag_text
                ):

                    attr_start = (
                        tag_start +
                        attribute.start(1)
                    )

                    attr_end = (
                        tag_start +
                        attribute.end(1)
                    )

                    self.text_area.tag_add(
                        "attribute",
                        f"1.0+{attr_start}c",
                        f"1.0+{attr_end}c"
                    )

                # =================================================
                # STRINGS
                # =================================================

                string_pattern = (
                    r'"[^"]*"'
                    r"|"
                    r"'[^']*'"
                )

                for string in re.finditer(
                    string_pattern,
                    tag_text
                ):

                    string_start = (
                        tag_start +
                        string.start()
                    )

                    string_end = (
                        tag_start +
                        string.end()
                    )

                    self.text_area.tag_add(
                        "string",
                        f"1.0+{string_start}c",
                        f"1.0+{string_end}c"
                    )

        finally:

            self.updating_text = False

    # =========================================================
    # SPELLCHECKING
    # =========================================================

    def is_word_boundary(self, char):

        return (
            char.isspace()
            or char in ".,!?;:()[]{}\"'<>/\\|+=-*"
        )

    def get_word_at_cursor(self):

        cursor = self.text_area.index(
            tk.INSERT
        )

        line, column = map(
            int,
            cursor.split(".")
        )

        line_text = self.text_area.get(
            f"{line}.0",
            f"{line}.end"
        )

        if column > len(line_text):
            column = len(line_text)

        start = column
        end = column

        while start > 0:

            char = line_text[start - 1]

            if self.is_word_boundary(char):
                break

            start -= 1

        while end < len(line_text):

            char = line_text[end]

            if self.is_word_boundary(char):
                break

            end += 1

        word = line_text[start:end]

        return word, line, start, end

    def check_word(self, word, line, start, end):

        if not SPELLCHECKER_AVAILABLE:
            return

        # Убираем HTML-похожие конструкции

        if "<" in word or ">" in word:
            return

        # Проверяем только русские слова

        if not re.fullmatch(
            r"[А-Яа-яЁё-]+",
            word
        ):
            return

        # Слишком короткие слова пропускаем

        if len(word) <= 1:
            return

        # Сначала убираем старую подсветку
        # этого участка

        self.text_area.tag_remove(
            "misspelled",
            f"{line}.{start}",
            f"{line}.{end}"
        )

        # Проверка слова

        if word.lower() not in self.spellchecker:

            self.text_area.tag_add(
                "misspelled",
                f"{line}.{start}",
                f"{line}.{end}"
            )

    def check_current_word(self):

        if not SPELLCHECKER_AVAILABLE:
            return

        word, line, start, end = (
            self.get_word_at_cursor()
        )

        if word:

            self.check_word(
                word,
                line,
                start,
                end
            )

    def on_key_press(self, event):

        # Проверяем слово перед пробелом,
        # Enter и пунктуацией.

        if (
            event.keysym in (
                "space",
                "Return",
                "Tab"
            )
            or event.char in ".,!?;:"
        ):

            self.root.after(
                10,
                self.check_previous_word
            )

    def check_previous_word(self):

        if not SPELLCHECKER_AVAILABLE:
            return

        cursor = self.text_area.index(
            tk.INSERT
        )

        line, column = map(
            int,
            cursor.split(".")
        )

        if column <= 0:
            return

        # Переходим на один символ назад

        self.text_area.mark_set(
            tk.INSERT,
            f"{line}.{column - 1}"
        )

        word, word_line, start, end = (
            self.get_word_at_cursor()
        )

        # Возвращаем курсор обратно

        self.text_area.mark_set(
            tk.INSERT,
            cursor
        )

        if word:

            self.check_word(
                word,
                word_line,
                start,
                end
            )

    def check_all_spelling(self):

        if not SPELLCHECKER_AVAILABLE:

            messagebox.showwarning(
                "Rewold",
                "Модуль pyspellchecker не установлен.\n\n"
                "Установи:\n"
                "pip install pyspellchecker"
            )

            return

        # Удаляем старую подсветку

        self.text_area.tag_remove(
            "misspelled",
            "1.0",
            tk.END
        )

        content = self.text_area.get(
            "1.0",
            tk.END
        )

        # =====================================================
        # Убираем HTML
        # =====================================================

        clean_text = re.sub(
            r"<[^>]+>",
            " ",
            content
        )

        words = list(
            re.finditer(
                r"[А-Яа-яЁё-]+",
                clean_text
            )
        )

        count = 0

        for match in words:

            word = match.group()

            if len(word) <= 1:
                continue

            if word.lower() in self.spellchecker:
                continue

            self.text_area.tag_add(
                "misspelled",
                f"1.0+{match.start()}c",
                f"1.0+{match.end()}c"
            )

            count += 1

        messagebox.showinfo(
            "Проверка орфографии",
            "Проверка завершена!\n\n"
            f"Найдено подозрительных слов: {count}"
        )

    # =========================================================
    # TEXT CHANGE
    # =========================================================

    def on_text_change(self, event=None):

        if self.updating_text:
            return

        self.auto_close_tag()

        self.highlight_syntax()

        self.update_preview()

    def after_edit(self):

        self.highlight_syntax()

        self.update_preview()

    # =========================================================
    # AUTO CLOSE TAGS
    # =========================================================

    def auto_close_tag(self):

        cursor_position = self.text_area.index(
            tk.INSERT
        )

        text_before = self.text_area.get(
            "1.0",
            cursor_position
        )

        match = re.search(
            r"<([a-zA-Z][a-zA-Z0-9]*)>$",
            text_before
        )

        if not match:
            return

        tag_name = match.group(1)

        self_closing_tags = {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr"
        }

        if tag_name.lower() in self_closing_tags:
            return

        closing_tag = f"</{tag_name}>"

        text_after = self.text_area.get(
            cursor_position,
            tk.END
        )

        if text_after.startswith(
            closing_tag
        ):
            return

        self.text_area.insert(
            tk.INSERT,
            closing_tag
        )

        self.text_area.mark_set(
            tk.INSERT,
            cursor_position
        )

    # =========================================================
    # LIVE PREVIEW
    # =========================================================

    def update_preview(self):

        if not self.preview_enabled:
            return

        if not HTML_PREVIEW_AVAILABLE:
            return

        html = self.text_area.get(
            "1.0",
            tk.END
        )

        if "<html" not in html.lower():

            html = f"""
<!DOCTYPE html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<style>

body {{
    font-family: Arial, sans-serif;
    padding: 30px;
    line-height: 1.6;
}}

h1 {{
    color: #222;
}}

h2 {{
    color: #333;
}}

h3 {{
    color: #444;
}}

code {{
    background: #eeeeee;
    padding: 3px 6px;
    border-radius: 4px;
}}

table {{
    border-collapse: collapse;
    width: 100%;
}}

th, td {{
    border: 1px solid #999;
    padding: 8px;
    text-align: left;
}}

th {{
    background: #eeeeee;
}}

</style>

</head>

<body>

{html}

</body>

</html>
"""

        try:

            self.html_preview.load_html(
                html
            )

        except Exception as e:

            print(
                "Ошибка Live Preview:",
                e
            )

    # =========================================================
    # TOGGLE PREVIEW
    # =========================================================

    def toggle_preview(self):

        self.preview_enabled = (
            not self.preview_enabled
        )

        if self.preview_enabled:

            self.preview_frame.pack(
                side="right",
                expand=True,
                fill="both"
            )

            self.update_preview()

        else:

            self.preview_frame.pack_forget()

    # =========================================================
    # TAB
    # =========================================================

    def handle_tab(self, event):

        self.text_area.insert(
            tk.INSERT,
            "    "
        )

        self.root.after(
            10,
            self.check_previous_word
        )

        return "break"

    # =========================================================
    # SAVE
    # =========================================================

    def save_file_as(self):

        file_path = filedialog.asksaveasfilename(

            defaultextension=".html",

            filetypes=[
                (
                    "HTML файлы (*.html)",
                    "*.html"
                ),
                (
                    "Текстовые документы (*.txt)",
                    "*.txt"
                ),
                (
                    "Markdown файлы (*.md)",
                    "*.md"
                ),
                (
                    "Все файлы (*.*)",
                    "*.*"
                )
            ]
        )

        if not file_path:
            return

        try:

            content = self.text_area.get(
                "1.0",
                tk.END
            )

            with open(
                file_path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(content)

            self.current_file = file_path

            self.root.title(
                f"Rewold — {file_path}"
            )

            messagebox.showinfo(
                "Rewold",
                "Файл успешно сохранён!"
            )

        except Exception as e:

            messagebox.showerror(
                "Ошибка",
                f"Не удалось сохранить файл:\n{e}"
            )


# =============================================================
# START
# =============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = RewoldApp(
        root
    )

    root.mainloop()